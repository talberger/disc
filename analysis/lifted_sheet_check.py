"""Is the speckle of the lifted teacher a pixel landing on ANOTHER SHEET of the mesh? (Tal, 2026-11-10; lvis151955 amodal: neighbouring
pixels alternate between near and far in analysis/lifted_pipeline_stages.py's distance maps.)
build_lifted_geodesic_table.py ray casts the FULL mesh and takes the nearest vertex of the DECIMATED one (cKDTree): where two sheets lie close
(a thin double shell), that vertex can be on the other sheet, geodesically far. Compared here, per lift:
  old = that mapping;  new = ray cast the decimated largest component itself and take the nearest vertex of the triangle the ray hits.
Prints, per lift: shell thickness behind the first hit, and per rep (= GT point): pixels whose old vertex is far (> 0.1 diameter) from their
new one, jumps between adjacent pixels (> 0.1 diameter) old / new, mean |change| vs the 2D teacher old / new. Figure: --rep's distance map
old | new | the far pixels, one row per lift.
  python analysis/lifted_sheet_check.py --tag lvis151955 --src_dir <runs_full_poly/lvis151955> --lift ray <full_lift.pth> <meta.json> \\
      --lift amodal <amodal_lift.pth> <meta.json> --rep 3 --out <png>
"""
import argparse, json, os, sys
import numpy as np, torch, scipy.ndimage, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph, pix_points, raycast_pix_point
from plot_lifted_geodesic_paths import grid_graph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True); ap.add_argument('--src_dir', required=True)
    ap.add_argument('--lift', nargs=3, action='append', required=True, metavar=('NAME', 'LIFT', 'META'))
    ap.add_argument('--rep', type=int, default=1, help='GT point of the figure, 1-based'); ap.add_argument('--out', required=True)
    ap.add_argument('--target_faces', type=int, default=200000)
    a = ap.parse_args()
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    import open3d as o3d
    S = a.src_dir; t = a.tag
    photo = np.array(Image.open(f'{S}/{t}.png').convert('RGB')); mask = torch.load(f'{S}/{t}_mask.pth').numpy().astype(bool)
    gt = torch.load(f'{S}/{t}_gt.pth', map_location='cpu'); reps = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
    diam2 = json.load(open(f'{S}/{t}_mask_geo_table_2d_seed0_meta.json'))['true_diameter_2d']
    G2, idx, prow, pcol = grid_graph(mask); H, W = mask.shape
    snap = lambda rc: int(np.argmin((prow - rc[0]) ** 2 + (pcol - rc[1]) ** 2))
    js = [snap(rc) for rc in reps]; D2 = scipy.sparse.csgraph.dijkstra(G2, indices=js) / diam2
    pa, pb = idx[:, :-1].ravel(), idx[:, 1:].ravel(); adj = (pa >= 0) & (pb >= 0); pa, pb = pa[adj], pb[adj]   # horizontally adjacent pixels
    img = lambda x: (lambda z: (z.__setitem__((prow, pcol), x), z)[1])(np.full((H, W), np.nan))

    fig, axs = plt.subplots(len(a.lift), 3, figsize=(21, len(a.lift) * (7 * H / W + 0.6)), squeeze=False)
    for ax, (name, lp, meta) in zip(axs, a.lift):
        lift = torch.load(lp, map_location='cpu'); diam = json.load(open(meta))['true_diameter_2d']
        V0, F0 = lift['vertices'].numpy(), lift['faces'].numpy(); ext = float(np.ptp(V0, 0).max())
        o = np.array([0.0, -lift['camera']['distance'], 0])
        P = raycast_pix_point(lift, H, W)[0][prow, pcol]; hit = np.isfinite(P[:, 0])
        d = np.where(hit[:, None], P - o, [0.0, 1, 0]); d /= np.linalg.norm(d, axis=1, keepdims=True)
        V, F = decimate(V0, F0, a.target_faces); G3 = edge_graph(V, F)
        _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False); big = np.bincount(lab).argmax(); keep = np.nonzero(lab == big)[0]
        v_old = keep[cKDTree(V[keep]).query(pix_points(lift, H, W)[0][prow, pcol])[1]]

        # shell thickness: the next surface behind the first hit, on the full mesh
        sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(V0.astype(np.float32), F0.astype(np.uint32))
        th2 = sc.cast_rays(o3d.core.Tensor(np.c_[P + 1e-4 * d, d][hit].astype(np.float32)))['t_hit'].numpy() / ext
        print(f'{name}: next surface behind the first hit (/ extent): median {np.median(th2):.4f}; < 0.01: {100 * (th2 < 0.01).mean():.1f}% '
              f'< 0.03: {100 * (th2 < 0.03).mean():.1f}% of the pixels', flush=True)

        # new mapping: ray cast the decimated largest component, nearest vertex of the hit triangle (misses: the nearest pixel that has one)
        Fk = F[lab[F[:, 0]] == big]; sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(V.astype(np.float32), Fk.astype(np.uint32))
        res = sc.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(o, d.shape), d].astype(np.float32)))
        th = res['t_hit'].numpy().astype(np.float64); ok = hit & np.isfinite(th); tri = Fk[res['primitive_ids'].numpy()[ok]]
        k = np.argmin(np.linalg.norm(V[tri] - (o + th[ok, None] * d[ok])[:, None], axis=2), 1)
        vimg = np.zeros((H, W), np.int64); vimg[prow[ok], pcol[ok]] = tri[np.arange(len(tri)), k]
        _, (ir, ic) = scipy.ndimage.distance_transform_edt(np.isnan(img(np.where(ok, 1.0, np.nan))), return_indices=True)
        v_new = vimg[ir, ic][prow, pcol]
        print(f'{name}: decimated largest component missed by {100 * (~ok).mean():.1f}% of the pixels', flush=True)

        for r, j in enumerate(js):
            Do = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=v_old[j]) / diam
            Dn = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=v_new[j]) / diam
            far = np.abs(Dn[v_old] - Dn[v_new]) > 0.1
            jo = (np.abs(Do[v_old[pa]] - Do[v_old[pb]]) > 0.1).mean(); jn = (np.abs(Dn[v_new[pa]] - Dn[v_new[pb]]) > 0.1).mean()
            print(f'{name} rep {r + 1} {reps[r]}: old vertex of the rep is {Dn[v_old[j]]:.3f} from its new one | pixels on a far vertex '
                  f'{100 * far.mean():.1f}% | adjacent jumps old {100 * jo:.1f}% new {100 * jn:.1f}% | mean |change| vs 2D old '
                  f'{np.abs(Do[v_old] - D2[r]).mean():.3f} new {np.abs(Dn[v_new] - D2[r]).mean():.3f}', flush=True)
            if r == a.rep - 1:
                for q, z, ti in ((ax[0], Do[v_old], 'old: nearest decimated vertex'), (ax[1], Dn[v_new], 'new: ray on the decimated mesh')):
                    q.imshow(photo); q.imshow(img(z), cmap='turbo', vmin=0, vmax=1, alpha=0.75)
                    q.set_title(f'{name}, rep {a.rep}: {ti}', fontsize=16)
                ax[2].imshow(photo); ax[2].imshow(img(np.where(far, 1.0, np.nan)), cmap='autumn', vmin=0, vmax=1)
                ax[2].set_title(f'{name}: old vertex > 0.1 diameter from the new one ({100 * far.mean():.1f}%)', fontsize=16)
                for q in ax:
                    q.plot(reps[r][1], reps[r][0], 'w*', ms=24, mec='k'); q.axis('off')
    fig.suptitle(f'{t}: teacher distance / diameter from rep {a.rep}, two pixel -> vertex mappings', fontsize=19)
    plt.tight_layout(rect=(0, 0, 1, 0.95)); plt.savefig(a.out, dpi=70)


if __name__ == '__main__':
    main()
