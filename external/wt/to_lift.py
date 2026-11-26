"""World Tracing raw output (/workspace/newm/wt_run.py npz) -> a lift file in Pixal3D's convention (external/pixal3d/lift.py docstring), so
build_lifted_geodesic_table.py / scripts/run_stage1_raycast.sh use it unchanged. Disc env.
    python external/wt/to_lift.py --raw lvis<id>.npz --mask <our visible mask .pth> --out <G>/<class>_<tag>_wt_lift.pth

1. Mesh from the 6 camera-space XYZ layers (OpenCV frame: x right, y down, z forward), without TRELLIS.2: the layers are entry/exit
   pairs along each pixel ray, so only (0,1), (2,3), (4,5) are solid (the gaps between them are air, e.g. between the near and far leg);
   points sampled inside the solid spans -> voxel grid -> close + fill -> Gaussian blur -> marching cubes -> largest component.
2. Intrinsics fitted on layer 0 in OUR crop's pixels: WT's 504 crop is (y1, x1, side) of our crop, pixel j -> x1 + (j + 0.5) side / 504;
   u = a X/Z + b, v = c Y/Z + d.
3. Into lift.py's frame as external/sam3d/to_lift.py does: G = (sgn(a) X, -sgn(c) Y, -Z), f = (|a| + |c|) / 2, crop_box from (b, d).
4. pix_vertex / pix_depth by ray casting, iou / coverage vs our mask, a check png.
"""
import argparse, math, os, sys
import numpy as np, torch, trimesh
from scipy import ndimage as ndi
from skimage.measure import marching_cubes
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sam3d'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'analysis'))
from build_lifted_geodesic_table import pix_rays, cast
from to_lift import RGL, DIST

SOLID = ((0, 1), (2, 3), (4, 5))


def layers_to_mesh(xyz, mask, res=192, steps=24, sigma=1.0):
    pts = [xyz[l][mask[l]] for l in range(len(xyz))]
    for i, j in SOLID:
        m = mask[i] & mask[j]; p0, p1 = xyz[i][m], xyz[j][m]
        pts += [p0 * (1 - t) + p1 * t for t in np.linspace(0, 1, steps + 2)[1:-1]]
    P = np.concatenate(pts); P = P[np.isfinite(P).all(1)]
    lo = P.min(0); vox = float((P.max(0) - lo).max()) / (res - 4); lo = lo - 2 * vox
    n = np.ceil((P.max(0) - lo) / vox).astype(int) + 3
    g = np.zeros(n, bool); idx = np.floor((P - lo) / vox).astype(int); g[tuple(idx.T)] = True
    g = ndi.binary_fill_holes(ndi.binary_closing(g, iterations=1))
    v, f, _, _ = marching_cubes(ndi.gaussian_filter(g.astype(np.float32), sigma), 0.5)
    m = trimesh.Trimesh(v * vox + lo, f, process=True)
    m = max(m.split(only_watertight=False), key=lambda c: len(c.faces))
    return np.asarray(m.vertices), np.asarray(m.faces, np.int64), vox


def fit_intrinsics(x0, ok, crop, side_px):
    y1, x1, side = crop; s = side / side_px; ii, jj = np.nonzero(ok)
    u = x1 + (jj + 0.5) * s; v = y1 + (ii + 0.5) * s; X, Y, Z = x0[ok].T
    (a, b), ru = np.polyfit(X / Z, u, 1, full=True)[:2]; (c, d), rv = np.polyfit(Y / Z, v, 1, full=True)[:2]
    return a, b, c, d, math.sqrt((float(ru[0]) + float(rv[0])) / (2 * len(u)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--raw', required=True); ap.add_argument('--mask', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--seed', default='42'); ap.add_argument('--res', type=int, default=192); ap.add_argument('--check_png', default=None)
    a = ap.parse_args()
    r = np.load(a.raw); mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape
    assert tuple(r['hw']) == (H, W), (r['hw'], mask.shape)
    xyz = r[f'xyz_{a.seed}'].astype(np.float64); lm = r[f'mask_{a.seed}'].astype(bool)
    V, F, vox = layers_to_mesh(xyz, lm, res=a.res)
    fa, fb, fc, fd, res = fit_intrinsics(xyz[0], lm[0] & np.isfinite(xyz[0]).all(-1), r['crop'], xyz.shape[1])
    f = (abs(fa) + abs(fc)) / 2; S = float(max(H, W)); fov = 2 * math.atan(S / (2 * f))
    cam = {'camera_angle_x': fov, 'distance': DIST, 'mesh_scale': 1.0}; box = (fb - S / 2, fd - S / 2, S)
    print(f'mesh {len(V)} vertices {len(F)} faces (voxel {vox:.4f}); intrinsics on layer 0: a {fa:.1f} c {fc:.1f} principal ({fb:.1f}, {fd:.1f}) '
          f'for a {W}x{H} crop, fit residual {res:.2f} px -> fov {math.degrees(fov):.1f} deg')
    G = np.c_[np.sign(fa) * V[:, 0], -np.sign(fc) * V[:, 1], -V[:, 2]]; Vw = G @ RGL.T + np.array([0.0, -DIST, 0])
    lift = {'camera': cam, 'crop_box': box}; o, dw, zc = pix_rays(lift, H, W)
    th, pid = cast(Vw, F, o, dw); ok = np.isfinite(th); hit = ok.reshape(H, W)
    iou = float((hit & mask).sum() / max((hit | mask).sum(), 1)); coverage = float((hit & mask).sum() / mask.sum())
    tri = F[pid[ok]]; Pk = o + th[ok, None] * dw[ok]; k = np.argmin(np.linalg.norm(Vw[tri] - Pk[:, None], axis=2), 1)
    pv = -np.ones(H * W, np.int64); pv[ok] = tri[np.arange(len(tri)), k]; zb = np.full(H * W, np.inf); zb[ok] = (th * zc)[ok]
    out = {'vertices': torch.from_numpy(Vw.astype(np.float32)), 'faces': torch.from_numpy(F), 'pix_vertex': torch.from_numpy(pv.reshape(H, W)),
           'pix_depth': torch.from_numpy(zb.reshape(H, W).astype(np.float32)), 'camera': cam, 'crop_box': tuple(float(x) for x in box),
           'iou': iou, 'coverage': coverage, 'source': 'wt', 'raw': os.path.abspath(a.raw), 'seed': a.seed,
           'intrinsics_fit': dict(a=fa, b=fb, c=fc, d=fd, residual_px=res)}
    torch.save(out, a.out)
    print(f'{os.path.basename(a.out)}: silhouette IoU {iou:.3f}, mask pixels with a surface point {coverage:.3f}, '
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
