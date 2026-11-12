"""SAM 3D raw output (external/sam3d/run_sam3d.py) -> a lift file in Pixal3D's convention (external/pixal3d/lift.py docstring), so
build_lifted_geodesic_table.py / scripts/run_stage1_raycast.sh use it unchanged (arm e.g. "lifted_sam3d=sam3d"). Disc env.
    python external/sam3d/to_lift.py --raw <tag>_sam3d_raw.npz --mask <our visible mask .pth> --out <G>/<class>_<tag>_sam3d_lift.pth

1. The glb mesh into SAM 3D's PyTorch3D camera frame (x left, y up, z into the scene): p = ((v @ Rz2y.T) * scale) @ R(quat) + trans;
   the rotation's side (R or R.T) is checked empirically, the one whose silhouette matches our mask is kept (as lift.py does for Pixal3D).
2. Intrinsics fitted on SAM 3D's own pointmap (same frame): u = a X/Z + b, v = c Y/Z + d in OUR crop's pixels (pixel centres at +0.5).
3. Into lift.py's frame: OpenGL camera G = (sgn(a) X, -sgn(c) Y, -Z), focal f = (|a| + |c|) / 2, principal point (b, d) -> camera_angle_x
   and crop_box (x0, y0, S) with S = max(H, W), x0 = b - S/2, y0 = d - S/2; world = Rgl @ G + (0, -distance, 0) as pix_rays() expects.
4. pix_vertex / pix_depth by ray casting (pix_rays + cast of build_lifted_geodesic_table.py), iou / coverage vs our mask, a check png.
"""
import argparse, math, os, sys
import numpy as np, torch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'analysis'))
from build_lifted_geodesic_table import pix_rays, cast

RZ2Y = np.array([[1.0, 0, 0], [0, 0, -1], [0, 1, 0]]); RGL = np.array([[1.0, 0, 0], [0, 0, -1], [0, 1, 0]]); DIST = 1.0


def quat_to_matrix(q):   # pytorch3d.transforms.quaternion_to_matrix, real part first
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def fit_intrinsics(pm, H, W):
    h, w = pm.shape[:2]; X, Y, Z = pm[..., 0], pm[..., 1], pm[..., 2]; ok = np.isfinite(pm).all(-1) & (Z > 1e-6)
    ii, jj = np.nonzero(ok); u = (jj + 0.5) * W / w; v = (ii + 0.5) * H / h; x = X[ok] / Z[ok]; y = Y[ok] / Z[ok]
    (a, b), ru = np.polyfit(x, u, 1, full=True)[:2]; (c, d), rv = np.polyfit(y, v, 1, full=True)[:2]
    res = math.sqrt((float(ru[0]) + float(rv[0])) / (2 * len(u))) if len(ru) and len(rv) else float('nan')
    return a, b, c, d, res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--raw', required=True); ap.add_argument('--mask', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--check_png', default=None)
    a = ap.parse_args()
    r = np.load(a.raw); mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape
    assert tuple(r['image_hw']) == (H, W), (r['image_hw'], mask.shape)
    V0 = r['vertices'].astype(np.float64) @ RZ2Y.T * r['scale']; F = r['faces'].astype(np.int64); Rq = quat_to_matrix(r['quat'].astype(np.float64))
    fa, fb, fc, fd, res = fit_intrinsics(r['pointmap'].astype(np.float64), H, W)
    f = (abs(fa) + abs(fc)) / 2; S = float(max(H, W)); fov = 2 * math.atan(S / (2 * f))
    cam = {'camera_angle_x': fov, 'distance': DIST, 'mesh_scale': 1.0}; box = (fb - S / 2, fd - S / 2, S)
    print(f'intrinsics on the pointmap: a {fa:.1f} c {fc:.1f} (|a|/|c| {abs(fa) / abs(fc):.3f}) principal ({fb:.1f}, {fd:.1f}) for a {W}x{H} crop, '
          f'fit residual {res:.2f} px -> fov {math.degrees(fov):.1f} deg')
    lift = {'camera': cam, 'crop_box': box}; o, dw, zc = pix_rays(lift, H, W); best = None
    for name, Rv in (('R', Rq), ('R.T', Rq.T)):
        P = V0 @ Rv + r['trans']                                            # PyTorch3D camera frame
        G = np.c_[np.sign(fa) * P[:, 0], -np.sign(fc) * P[:, 1], -P[:, 2]]  # OpenGL camera frame
        Vw = G @ RGL.T + np.array([0.0, -DIST, 0])
        th, pid = cast(Vw, F, o, dw); hit = np.isfinite(th).reshape(H, W)
        iou = float((hit & mask).sum() / max((hit | mask).sum(), 1)); print(f'  rotation {name}: silhouette IoU {iou:.3f}')
        if best is None or iou > best[1]: best = (name, iou, Vw, th, pid, hit)
    name, iou, Vw, th, pid, hit = best; ok = np.isfinite(th)
    tri = F[pid[ok]]; Pk = o + th[ok, None] * dw[ok]; k = np.argmin(np.linalg.norm(Vw[tri] - Pk[:, None], axis=2), 1)
    pv = -np.ones(H * W, np.int64); pv[ok] = tri[np.arange(len(tri)), k]; zb = np.full(H * W, np.inf); zb[ok] = (th * zc)[ok]
    coverage = float((hit & mask).sum() / mask.sum())
    out = {'vertices': torch.from_numpy(Vw.astype(np.float32)), 'faces': torch.from_numpy(F), 'pix_vertex': torch.from_numpy(pv.reshape(H, W)),
           'pix_depth': torch.from_numpy(zb.reshape(H, W).astype(np.float32)), 'camera': cam, 'crop_box': tuple(float(x) for x in box),
           'variant': name, 'iou': iou, 'coverage': coverage, 'source': 'sam3d', 'raw': os.path.abspath(a.raw),
           'intrinsics_fit': dict(a=fa, b=fb, c=fc, d=fd, residual_px=res), 'sam3d_layout_iou': float(r['iou'])}
    torch.save(out, a.out)
    print(f'{os.path.basename(a.out)}: rotation {name}, silhouette IoU {iou:.3f}, mask pixels with a surface point {coverage:.3f}, '
          f'{len(Vw)} vertices, {len(F)} faces')
    if a.check_png:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        sil = np.zeros((H, W, 3)); sil[hit & mask] = (0, 0.7, 0); sil[mask & ~hit] = (0.9, 0, 0); sil[hit & ~mask] = (0, 0.3, 1)
        fig, ax = plt.subplots(1, 2, figsize=(9, 4.5 * H / W + 0.6))
        ax[0].imshow(sil); ax[0].set_title(f'silhouette vs mask, IoU {iou:.3f}\n(green both, red mask only, blue mesh only)', fontsize=9)
        d = np.where(np.isfinite(zb), zb, np.nan).reshape(H, W); ax[1].imshow(d, cmap='viridis'); ax[1].set_title('depth of the visible surface', fontsize=9)
        for x in ax: x.axis('off')
        fig.savefig(a.check_png, dpi=90, bbox_inches='tight')


if __name__ == '__main__':
    main()
