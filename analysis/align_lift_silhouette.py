"""Our own silhouette alignment of a lift (Tal, 2026-11-20: SAM 3D's layout leaves the mesh off our mask, bear 6111 IoU 0.69; its own
manual alignment + ICP helps some and hurts others). Rigid + uniform scale about the mesh centroid,
    V' = s * Rot(w) (V - c) + c + t       (w = axis-angle [3], t [3] in units of the mesh size, log s [1])
chosen to maximise the silhouette IoU of the ray-cast mesh against OUR mask (the camera of the lift, pix_rays of
build_lifted_geodesic_table.py, stays fixed). Nelder-Mead on the ray-cast IoU (half-resolution rays), a few restarts; the result is kept
only if it beats the input. pix_vertex / pix_depth / iou / coverage are rebuilt as external/sam3d/to_lift.py builds them.
    python analysis/align_lift_silhouette.py --lift <in>_lift.pth --mask <mask.pth> --out <out>_lift.pth [--check_png p.png]
"""
import argparse, os, sys, time
import numpy as np, torch
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import pix_rays, cast


def transform(V, c, size, p):
    return np.exp(p[6]) * Rotation.from_rotvec(p[:3]).apply(V - c) + c + p[3:6] * size


def silhouette(V, F, o, dw, H, W):
    th, _ = cast(V, F, o, dw); return np.isfinite(th).reshape(H, W)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--lift', required=True); ap.add_argument('--mask', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--check_png', default=None); ap.add_argument('--restarts', type=int, default=3); ap.add_argument('--iters', type=int, default=300)
    a = ap.parse_args(); t0 = time.time()
    L = torch.load(a.lift, map_location='cpu'); mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape
    V0 = L['vertices'].numpy().astype(np.float64); F = L['faces'].numpy(); c = V0.mean(0); size = float(np.linalg.norm(V0.max(0) - V0.min(0)))
    o, dw, zc = pix_rays(L, H, W)
    sub = np.zeros((H, W), bool); sub[::2, ::2] = True; dws = dw[sub.ravel()]; ms = mask[::2, ::2]; hs, ws = ms.shape
    def loss(p):
        hit = silhouette(transform(V0, c, size, p), F, o, dws, hs, ws); return -(hit & ms).sum() / max((hit | ms).sum(), 1)
    p0 = np.zeros(7); best = (loss(p0), p0); iou0 = -best[0]
    rng = np.random.RandomState(0)
    for k in range(a.restarts):
        start = best[1] + (0 if k == 0 else rng.normal(0, [0.05] * 3 + [0.02] * 3 + [0.03]))
        simplex = np.vstack([start] + [start + np.eye(7)[j] * ([0.1] * 3 + [0.04] * 3 + [0.08])[j] for j in range(7)])
        r = minimize(loss, start, method='Nelder-Mead', options=dict(initial_simplex=simplex, maxiter=a.iters, xatol=1e-4, fatol=1e-4))
        if r.fun < best[0]: best = (r.fun, r.x)
    p = best[1]; V = transform(V0, c, size, p)
    th, pid = cast(V, F, o, dw); ok = np.isfinite(th); hit = ok.reshape(H, W)
    iou = float((hit & mask).sum() / max((hit | mask).sum(), 1)); iou_in = float(L.get('iou', np.nan))
    if iou <= iou_in:
        print(f'{os.path.basename(a.lift)}: no gain (IoU {iou_in:.3f} -> {iou:.3f}), input kept'); V, iou = V0, iou_in
        th, pid = cast(V, F, o, dw); ok = np.isfinite(th); hit = ok.reshape(H, W)
    tri = F[pid[ok]]; Pk = o + th[ok, None] * dw[ok]; kk = np.argmin(np.linalg.norm(V[tri] - Pk[:, None], axis=2), 1)
    pv = -np.ones(H * W, np.int64); pv[ok] = tri[np.arange(len(tri)), kk]; zb = np.full(H * W, np.inf); zb[ok] = (th * zc)[ok]
    cov = float((hit & mask).sum() / mask.sum())
    out = dict(L, vertices=torch.from_numpy(V.astype(np.float32)), pix_vertex=torch.from_numpy(pv.reshape(H, W)),
               pix_depth=torch.from_numpy(zb.reshape(H, W).astype(np.float32)), iou=iou, coverage=cov,
               align=dict(rotvec=p[:3].tolist(), trans=(p[3:6] * size).tolist(), scale=float(np.exp(p[6])), iou_before=iou_in, iou_half_res_start=iou0))
    torch.save(out, a.out)
    print(f'{os.path.basename(a.out)}: IoU {iou_in:.3f} -> {iou:.3f}, coverage {L.get("coverage", np.nan):.3f} -> {cov:.3f}, '
          f'rot {np.degrees(np.linalg.norm(p[:3])):.1f} deg, shift {np.linalg.norm(p[3:6]):.3f} x size, scale {np.exp(p[6]):.3f} [{time.time() - t0:.0f} s]')
    if a.check_png:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        sil = np.zeros((H, W, 3)); sil[hit & mask] = (0, 0.7, 0); sil[mask & ~hit] = (0.9, 0, 0); sil[hit & ~mask] = (0, 0.3, 1)
        plt.figure(figsize=(5, 5 * H / W)); plt.imshow(sil); plt.axis('off'); plt.title(f'aligned IoU {iou:.3f} (was {iou_in:.3f})', fontsize=9)
        plt.savefig(a.check_png, dpi=90, bbox_inches='tight')


if __name__ == '__main__':
    main()
