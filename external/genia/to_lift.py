"""GenIA output (results/mono_static/image/<scene>/<ts>/final) -> a lift file in Pixal3D's convention (external/pixal3d/lift.py docstring),
so build_lifted_geodesic_table.py / scripts/run_stage1_raycast.sh use it unchanged. Disc env.
    python external/genia/to_lift.py --final <.../final> --pad <genia_pad scene>/pad.json --mask <our visible mask .pth> --out <G>/<class>_<tag>_genia_lift.pth

GenIA was fed our crop padded (white, mask 0) to one of map-anything's aspect ratios (/workspace/newm/genia_pad.py), so its centre crop
removes nothing.
1. meshes/world.glb is in COLMAP's world frame; colmap/sparse/000/images.txt (w2c, quaternion real first) takes it into the camera frame.
   The frame's axes (OpenCV x right, y down, z forward, or glTF's y up / z back) are checked empirically: the variant whose silhouette
   matches our mask is kept.
2. cameras.txt's PINHOLE K is in the model input (W', H'), a scale-to-cover + centre crop of the padded image (GenIA's
   crop_resize_transform): u' = s_x u_pad - left -> u_ours = (u' + left) / s_x - pad_left; the same in y.
3. Into lift.py's frame as external/sam3d/to_lift.py does, then pix_vertex / pix_depth by ray casting and a check png.
"""
import argparse, json, math, os, sys
import numpy as np, torch, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sam3d'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'analysis'))
from build_lifted_geodesic_table import pix_rays, cast
from to_lift import RGL, DIST, quat_to_matrix


def crop_resize_scales(orig_hw, target_hw):   # GenIA core/utils/sequence.py crop_resize_transform + crop_resize_scales
    (oh, ow), (th, tw) = orig_hw, target_hw; s = max(tw / ow, th / oh) + 1e-8; sw, sh = int(np.floor(ow * s)), int(np.floor(oh * s))
    return sw / ow, sh / oh, (sw - tw) // 2, (sh - th) // 2


def colmap_txt(path):
    return [l.split() for l in open(path) if l.strip() and not l.startswith('#')]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--final', required=True); ap.add_argument('--pad', required=True)
    ap.add_argument('--mask', required=True); ap.add_argument('--out', required=True); ap.add_argument('--check_png', default=None)
    a = ap.parse_args()
    mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape; pad = json.load(open(a.pad))
    assert (pad['H'], pad['W']) == (H, W), (pad, mask.shape)
    sc = trimesh.load(os.path.join(a.final, 'meshes', 'world.glb')); m = sc.to_geometry() if hasattr(sc, 'to_geometry') else sc
    V0 = np.asarray(m.vertices, np.float64); F = np.asarray(m.faces, np.int64)
    cam = colmap_txt(os.path.join(a.final, 'colmap', 'sparse', '000', 'cameras.txt'))[0]; im = colmap_txt(os.path.join(a.final, 'colmap', 'sparse', '000', 'images.txt'))[0]
    assert cam[1] == 'PINHOLE', cam
    Wm, Hm = int(cam[2]), int(cam[3]); fx, fy, cx, cy = map(float, cam[4:8])
    Rw = quat_to_matrix(np.array(im[1:5], np.float64)); tw = np.array(im[5:8], np.float64)
    sx, sy, left, top = crop_resize_scales((pad['Hp'], pad['Wp']), (Hm, Wm))
    fa, fc = fx / sx, fy / sy; fb = (cx + left) / sx - pad['left']; fd = (cy + top) / sy - pad['top']
    f = (fa + fc) / 2; S = float(max(H, W)); fov = 2 * math.atan(S / (2 * f))
    camd = {'camera_angle_x': fov, 'distance': DIST, 'mesh_scale': 1.0}; box = (fb - S / 2, fd - S / 2, S)
    print(f'K in our crop: fx {fa:.1f} fy {fc:.1f} principal ({fb:.1f}, {fd:.1f}) for a {W}x{H} crop (model input {Wm}x{Hm}, '
          f'padded {pad["Wp"]}x{pad["Hp"]}) -> fov {math.degrees(fov):.1f} deg; {len(V0)} vertices {len(F)} faces')
    lift = {'camera': camd, 'crop_box': box}; o, dw, zc = pix_rays(lift, H, W); best = None
    for name, A in (('opencv', np.diag([1.0, 1, 1])), ('gltf', np.diag([1.0, -1, -1]))):
        P = (V0 @ A.T) @ Rw.T + tw                                   # OpenCV camera frame
        Vw = np.c_[P[:, 0], -P[:, 1], -P[:, 2]] @ RGL.T + np.array([0.0, -DIST, 0])
        th, pid = cast(Vw, F, o, dw); hit = np.isfinite(th).reshape(H, W)
        iou = float((hit & mask).sum() / max((hit | mask).sum(), 1)); print(f'  axes {name}: silhouette IoU {iou:.3f}')
        if best is None or iou > best[1]: best = (name, iou, Vw, th, pid, hit)
    name, iou, Vw, th, pid, hit = best; ok = np.isfinite(th)
    tri = F[pid[ok]]; Pk = o + th[ok, None] * dw[ok]; k = np.argmin(np.linalg.norm(Vw[tri] - Pk[:, None], axis=2), 1)
    pv = -np.ones(H * W, np.int64); pv[ok] = tri[np.arange(len(tri)), k]; zb = np.full(H * W, np.inf); zb[ok] = (th * zc)[ok]
    coverage = float((hit & mask).sum() / mask.sum())
    out = {'vertices': torch.from_numpy(Vw.astype(np.float32)), 'faces': torch.from_numpy(F), 'pix_vertex': torch.from_numpy(pv.reshape(H, W)),
           'pix_depth': torch.from_numpy(zb.reshape(H, W).astype(np.float32)), 'camera': camd, 'crop_box': tuple(float(x) for x in box),
           'variant': name, 'iou': iou, 'coverage': coverage, 'source': 'genia', 'raw': os.path.abspath(a.final),
           'intrinsics': dict(fx=fa, fy=fc, cx=fb, cy=fd)}
    torch.save(out, a.out)
    print(f'{os.path.basename(a.out)}: axes {name}, silhouette IoU {iou:.3f}, mask pixels with a surface point {coverage:.3f}, '
          f'hits outside the mask {int((hit & ~mask).sum())}')
    if a.check_png:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        sil = np.zeros((H, W, 3)); sil[hit & mask] = (0, 0.7, 0); sil[mask & ~hit] = (0.9, 0, 0); sil[hit & ~mask] = (0, 0.3, 1)
        fig, ax = plt.subplots(1, 2, figsize=(9, 4.5 * H / W + 0.6))
        ax[0].imshow(sil, interpolation='nearest'); ax[0].set_title(f'silhouette vs mask, IoU {iou:.3f}\n(green both, red mask only, blue mesh only)', fontsize=9)
        d = np.where(np.isfinite(zb), zb, np.nan).reshape(H, W); ax[1].imshow(d, cmap='viridis', interpolation='nearest'); ax[1].set_title('depth of the visible surface', fontsize=9)
        for x in ax: x.axis('off')
        fig.savefig(a.check_png, dpi=140, bbox_inches='tight')


if __name__ == '__main__':
    main()
