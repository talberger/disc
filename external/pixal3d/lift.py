"""2D -> 3D lift of one DISC crop with Pixal3D (Tal, 2026-10-26). Run INSIDE the Pixal3D clone with its env (Run:ai workspace pixal3d-env):
    cd /workspace/pixal3d_repo && source /workspace/envs/pixal3d/bin/activate
    python /workspace/disc/external/pixal3d/lift.py --image <crop RGBA png> --out_dir <dir> --tag lvis56069

Input = our crop with OUR object mask as alpha (Pixal3D then uses the alpha; its background-removal model is never needed, so it is
replaced by a stub -- the shipped one, briaai/RMBG-2.0, is a gated HF repo anyway).

Output <out_dir>/<tag>_lift.pth:
    vertices [V,3] float32, faces [F,3] int64  -- the generated mesh in the camera's world frame (Pixal3D convention, below)
    pix_vertex [H,W] int64   -- for every pixel of OUR crop: the visible (front-most) mesh vertex, -1 = no surface there
    pix_depth  [H,W] float32 -- its camera depth (inf where none)
    camera {camera_angle_x, distance, mesh_scale}, crop_box (x0, y0, S): Pixal3D's square crop of our image (S x S pixels from (x0, y0)),
    variant (which vertex frame matched), iou / coverage (mesh silhouette vs our mask)
plus <tag>.glb (textured, for viewing) and <tag>_lift_check.png (photo | mesh silhouette vs mask | depth).

Camera (pixal3d/trainers/flow_matching/mixins/image_conditioned_proj.py): Blender convention, c2w = [[1,0,0,0],[0,0,-1,-d],[0,1,0,0],[0,0,0,1]]
(camera at (0,-d,0) looking at the origin, +Z up), focal = 16/tan(fov/2) mm on a 32 mm sensor, image = the square crop. Its grid points go
through R = [[1,0,0],[0,0,-1],[0,1,0]] and /mesh_scale/2 before projection; whether the decoded mesh vertices need R too is checked here
empirically (both frames are projected, the one whose silhouette matches our mask is kept).
Correspondence = per-pixel z-buffer over the projected VERTICES (the decoded mesh is dense: many vertices per pixel at our 400 px crops).
"""
import argparse, json, math, os, sys, time
import numpy as np
import torch
from PIL import Image

REPO = os.environ.get('PIXAL3D_REPO', '/workspace/pixal3d_repo')
sys.path.insert(0, REPO)
import inference as inf                                   # Pixal3D's own inference.py: init_pipeline, MoGe camera, defaults
import pixal3d.pipelines.rembg as rembg_mod
from pixal3d.trainers.flow_matching.mixins.image_conditioned_proj import project_points_to_image_batch


class NoRembg:
    """Stands in for the background-removal model: our input always carries the mask as alpha."""
    def __init__(self, *a, **k): pass
    def to(self, *a, **k): return self
    def cuda(self): return self
    def cpu(self): return self
    def __call__(self, *a, **k): raise RuntimeError('lift.py needs an RGBA input (our mask as alpha); background removal is disabled')


for _name in dir(rembg_mod):
    if not _name.startswith('_') and isinstance(getattr(rembg_mod, _name), type):
        setattr(rembg_mod, _name, NoRembg)

R = torch.tensor([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])


def square_crop_box(rgba):
    """The box Pixal3D's preprocess_image crops (same arithmetic): bbox of alpha > 0.8, a square 1.1 x its longer side around its centre."""
    alpha = np.array(rgba)[:, :, 3]
    yx = np.argwhere(alpha > 0.8 * 255)
    b = yx[:, 1].min(), yx[:, 0].min(), yx[:, 1].max(), yx[:, 0].max()
    c = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    size = int(max(b[2] - b[0], b[3] - b[1]) * 1.1)
    return c[0] - size // 2, c[1] - size // 2, c[0] + size // 2, c[1] + size // 2


def splat(verts_world, cam, box, H, W):
    """Project the vertices with Pixal3D's camera into OUR crop; per-pixel front-most vertex."""
    x0, y0, x1, y1 = box
    S = int(round(x1 - x0))
    c2w = torch.tensor([[1.0, 0, 0, 0], [0, 0, -1, -cam['distance']], [0, 1, 0, 0], [0, 0, 0, 1]], device=verts_world.device)[None]
    pts, depth, _ = project_points_to_image_batch(verts_world, c2w, torch.tensor([cam['camera_angle_x']], device=verts_world.device),
                                                  resolution=S)
    px, py, d = pts[0, :, 0] + x0, pts[0, :, 1] + y0, depth[0]   # pixel coords of OUR crop
    ix, iy = px.floor().long(), py.floor().long()
    ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H) & (d > 0)
    lin = (iy * W + ix)[ok]; dv = d[ok]; vid = torch.nonzero(ok).squeeze(1)
    zbuf = torch.full((H * W,), float('inf'), device=d.device).scatter_reduce(0, lin, dv, reduce='amin')
    front = dv <= zbuf[lin] + 1e-7
    pv = torch.full((H * W,), -1, dtype=torch.long, device=d.device)
    pv[lin[front]] = vid[front]
    return pv.view(H, W), zbuf.view(H, W)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', required=True, help='our crop as RGBA, alpha = our object mask')
    ap.add_argument('--out_dir', required=True); ap.add_argument('--tag', required=True)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--fov', type=float, default=-1.0, help='manual FOV (rad); default = MoGe-2 estimate')
    ap.add_argument('--low_vram', action='store_true'); ap.add_argument('--resolution', type=int, default=-1)
    ap.add_argument('--no_glb', action='store_true', help='skip the textured GLB (viewing only)')
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    rgba = Image.open(a.image)
    assert rgba.mode == 'RGBA', f'{a.image} is {rgba.mode}, need RGBA with our mask as alpha'
    W, H = rgba.size
    mask = np.array(rgba)[:, :, 3] > 127
    assert max(W, H) <= 1024, 'Pixal3D downscales inputs above 1024 px; crop_box below would not account for it'

    pipeline = inf.init_pipeline(inf.MODEL_PATH, low_vram=a.low_vram)
    pre = pipeline.preprocess_image(rgba)
    box = square_crop_box(rgba)
    assert abs((box[2] - box[0]) - pre.size[0]) <= 1, (box, pre.size)
    tmp = os.path.join(a.out_dir, f'_{a.tag}_preprocessed.png'); pre.save(tmp)
    if a.fov > 0:
        cam = {'camera_angle_x': a.fov, 'mesh_scale': 1.0,
               'distance': inf.distance_from_fov(a.fov, torch.tensor([-1.0, 0.0, 0.0]), torch.tensor([0, 511]), 1.0, 512)['distance_from_x']}
    else:
        moge = inf.load_moge_model(device='cuda')
        cam = inf.get_camera_params_wild_moge(tmp, moge, device='cuda', mesh_scale=1.0, extend_pixel=0, image_resolution=512)
        moge.cpu(); del moge; torch.cuda.empty_cache()
    print(f'[lift] camera {cam}', flush=True)

    torch.manual_seed(a.seed)
    ptype = f"{a.resolution if a.resolution > 0 else (1024 if a.low_vram else 1536)}_cascade"
    mesh_list, (_, _, res) = pipeline.run(
        pre, camera_params=cam, seed=a.seed, preprocess_image=False, return_latent=True, pipeline_type=ptype, max_num_tokens=49152,
        sparse_structure_sampler_params={'steps': 12, 'guidance_strength': 7.5, 'guidance_rescale': 0.7, 'rescale_t': 5.0},
        shape_slat_sampler_params={'steps': 12, 'guidance_strength': 7.5, 'guidance_rescale': 0.5, 'rescale_t': 3.0},
        tex_slat_sampler_params={'steps': 12, 'guidance_strength': 1.0, 'guidance_rescale': 0.0, 'rescale_t': 3.0})
    mesh = mesh_list[0]
    V = mesh.vertices.float(); F = mesh.faces.long()
    print(f'[lift] mesh {V.shape[0]} vertices, {F.shape[0]} faces, bbox {V.min(0).values.tolist()} .. {V.max(0).values.tolist()} '
          f'[{time.time() - t0:.0f} s]', flush=True)

    # Which frame do the decoded vertices live in? Project both candidates, keep the one whose silhouette matches our mask.
    mask_t = torch.from_numpy(mask).to(V.device)
    best = None
    for name, Vw in [('R', (V @ R.to(V.device).T) / cam['mesh_scale']), ('identity', V / cam['mesh_scale'])]:
        pv, zb = splat(Vw, cam, box, H, W)
        cov = pv >= 0
        iou = float((cov & mask_t).sum() / (cov | mask_t).sum())
        print(f'[lift] frame {name:8s}: silhouette IoU vs our mask {iou:.3f}, mask covered {float((cov & mask_t).sum() / mask_t.sum()):.3f}',
              flush=True)
        if best is None or iou > best[1]:
            best = (name, iou, Vw, pv, zb)
    name, iou, Vw, pv, zb = best
    coverage = float(((pv >= 0) & mask_t).sum() / mask_t.sum())
    out = {'vertices': Vw.cpu(), 'faces': F.cpu(), 'pix_vertex': pv.cpu(), 'pix_depth': zb.cpu(), 'camera': cam,
           'crop_box': tuple(float(b) for b in box[:2]) + (float(box[2] - box[0]),), 'variant': name, 'iou': iou, 'coverage': coverage,
           'image': os.path.abspath(a.image), 'seed': a.seed, 'pipeline_type': ptype}
    torch.save(out, os.path.join(a.out_dir, f'{a.tag}_lift.pth'))
    print(f'[lift] kept frame {name}: IoU {iou:.3f}, mask pixels with a surface point {coverage:.3f}', flush=True)

    # check figure: photo | silhouette (green = both, red = mask only, blue = mesh only) | depth of the visible surface
    photo = np.array(rgba.convert('RGB'))
    cov = (pv >= 0).cpu().numpy()
    sil = np.zeros_like(photo); sil[cov & mask] = (60, 200, 60); sil[mask & ~cov] = (220, 50, 50); sil[cov & ~mask] = (50, 90, 220)
    z = zb.cpu().numpy(); fin = np.isfinite(z)
    dep = np.zeros(z.shape, np.uint8)
    if fin.any():
        dep[fin] = (255 * (1 - (z[fin] - z[fin].min()) / (np.ptp(z[fin]) + 1e-9))).astype(np.uint8)
    fig = np.concatenate([photo, sil, np.repeat(dep[:, :, None], 3, 2)], 1)
    Image.fromarray(fig).save(os.path.join(a.out_dir, f'{a.tag}_lift_check.png'))
    os.remove(tmp)

    if not a.no_glb:
        import o_voxel
        glb = o_voxel.postprocess.to_glb(vertices=mesh.vertices, faces=mesh.faces, attr_volume=mesh.attrs, coords=mesh.coords,
                                         attr_layout=pipeline.pbr_attr_layout, grid_size=res, aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
                                         decimation_target=1000000, texture_size=2048, remesh=True, remesh_band=1, remesh_project=0,
                                         use_tqdm=False)
        glb.apply_transform(np.array([[-1, 0, 0, 0], [0, 0, -1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=np.float64))
        glb.export(os.path.join(a.out_dir, f'{a.tag}.glb'), extension_webp=True)
    print(f'LIFT DONE {a.tag} [{time.time() - t0:.0f} s]', flush=True)


if __name__ == '__main__':
    main()
