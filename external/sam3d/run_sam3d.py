"""2D -> 3D with SAM 3D Objects (Itai's suggestion, 2026-11-12), the raw half: run INSIDE the SAM 3D clone with its env:
    cd /workspace/sam3d_repo && source /opt/conda/etc/profile.d/conda.sh && conda activate /workspace/envs/sam3d
    python /workspace/disc/external/sam3d/run_sam3d.py --jobs <tsv: tag, image png, mask (.pth bool [H,W] or an RGBA png's alpha)> --out_dir <dir>
The model loads ONCE per call. Per job: <out_dir>/<tag>_sam3d_raw.npz =
    vertices [V,3] / faces [F,3]: the glb mesh in its own frame (z-up, as SAM 3D's layout code reads it)
    quat [4] (w, x, y, z, pytorch3d), trans [3], scale [3]: object -> PyTorch3D camera (x left, y up, z into the scene), applied as
        p_cam = ((v @ Rz2y.T) * scale) @ R(quat) + trans   (sam3d_objects/pipeline/layout_post_optimization_utils.get_mesh + compose_transform)
    pointmap [h,w,3]: SAM 3D's per-pixel points, same camera frame -> external/sam3d/to_lift.py fits the intrinsics on it
    image_hw [2]: our crop's size.
external/sam3d/to_lift.py (disc env) then turns it into a <tag>_lift.pth that build_lifted_geodesic_table.py reads like a Pixal3D lift.
Needs a GPU with >= 32 GB (SAM 3D's setup doc) and the gated HF weights in checkpoints/hf.
"""
import argparse, os, sys, time
import numpy as np, torch
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('--jobs', required=True); ap.add_argument('--out_dir', required=True)
ap.add_argument('--seed', type=int, default=42); ap.add_argument('--layout_post', type=int, default=1, help='SAM 3D layout post-optimisation (fits the pose to mask + pointmap)')
a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
sys.path.append('notebook'); from inference import Inference

t0 = time.time(); inf = Inference('checkpoints/hf/pipeline.yaml', compile=False); print(f'[sam3d] model loaded [{time.time() - t0:.0f} s]', flush=True)
for line in open(a.jobs):
    if not line.strip(): continue
    tag, img, msk = line.split()[:3]; out = os.path.join(a.out_dir, f'{tag}_sam3d_raw.npz')
    if os.path.exists(out): print(f'[sam3d] {tag}: done, skipped'); continue
    t0 = time.time()
    rgb = np.array(Image.open(img).convert('RGB'))
    mask = torch.load(msk).numpy().astype(bool) if msk.endswith('.pth') else np.array(Image.open(msk).convert('RGBA'))[..., 3] > 127
    assert mask.shape == rgb.shape[:2], (mask.shape, rgb.shape)
    try:
        o = inf._pipeline.run(inf.merge_mask_to_rgba(rgb, mask), None, a.seed, stage1_only=False, with_mesh_postprocess=False, with_texture_baking=False,
                              with_layout_postprocess=bool(a.layout_post), use_vertex_color=True, stage1_inference_steps=None, pointmap=None)
    except Exception as e:
        print(f'[sam3d] {tag}: FAILED {e!r}', flush=True); continue
    g = o['glb']; f = lambda x: torch.as_tensor(x).detach().float().cpu().numpy().reshape(-1)
    np.savez_compressed(out, vertices=np.asarray(g.vertices, np.float32), faces=np.asarray(g.faces, np.int64), quat=f(o['rotation']),
                        trans=f(o['translation']), scale=f(o['scale']), pointmap=torch.as_tensor(o['pointmap']).float().numpy(),
                        image_hw=np.array(rgb.shape[:2]), iou=float(o.get('iou', -1) if not torch.is_tensor(o.get('iou')) else o['iou']))
    print(f'[sam3d] {tag}: {len(g.vertices)} vertices, {len(g.faces)} faces, pointmap {tuple(o["pointmap"].shape)}, '
          f'layout iou {o.get("iou", "-")} [{time.time() - t0:.0f} s]', flush=True)
print('SAM3D RAW DONE')
