"""One path, three teachers: 2D (inside the mask) | lifted with lift.py's vertex splat | lifted with the ray cast (Tal, 2026-11-10).
Shows the splat bug on a path: a front pixel mapped to a back vertex sends the lifted path around the back (dotted = hidden behind the
visible surface); after the ray-cast fix it stays on the front. rep = a GT point; target = --target (row col), or the pixel whose lifted
(splat) distance changes most vs 2D (the "x" of analysis/lifted_vs_2d_stage1_study.py).
  python analysis/lifted_path_fix_figure.py --tag lvis186446 --src_dir <runs_full_poly/lvis186446> --lift_path <..._full_lift.pth> \\
      --lifted_meta <meta.json> --rep 2 [--target r c] --out <png>
"""
import argparse, json, os, sys
import numpy as np, torch, scipy.ndimage, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph, pix_points
from plot_lifted_geodesic_paths import grid_graph, path_from_pred, project


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True); ap.add_argument('--src_dir', required=True); ap.add_argument('--lift_path', required=True)
    ap.add_argument('--lifted_meta', required=True); ap.add_argument('--rep', type=int, default=1, help='GT point, 1-based')
    ap.add_argument('--target', type=int, nargs=2); ap.add_argument('--out', required=True)
    ap.add_argument('--target_faces', type=int, default=200000)
    a = ap.parse_args()
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    S = a.src_dir; t = a.tag
    photo = np.array(Image.open(f'{S}/{t}.png').convert('RGB')); mask = torch.load(f'{S}/{t}_mask.pth').numpy().astype(bool)
    gt = torch.load(f'{S}/{t}_gt.pth', map_location='cpu'); C = (gt['rows'][a.rep - 1].item(), gt['cols'][a.rep - 1].item())
    diam2 = json.load(open(f'{S}/{t}_mask_geo_table_2d_seed0_meta.json'))['true_diameter_2d']
    diam3 = json.load(open(a.lifted_meta))['true_diameter_2d']

    G2, idx, prow, pcol = grid_graph(mask); H, W = mask.shape
    lift = torch.load(a.lift_path, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']
    pv = lift['pix_vertex'].numpy(); has_s = pv >= 0                     # lift.py's splat, inlined as lifted_pixel_vertex_check.py
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~has_s, return_indices=True); PS = lift['vertices'].numpy()[pv[ir, ic]]
    PR, _ = pix_points(lift, H, W)
    V, F = decimate(lift['vertices'].numpy(), lift['faces'].numpy(), a.target_faces)
    G3 = edge_graph(V, F); _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
    keep = np.nonzero(lab == np.bincount(lab).argmax())[0]; tree = cKDTree(V[keep])
    vs = keep[tree.query(PS[prow, pcol])[1]]; vr = keep[tree.query(PR[prow, pcol])[1]]
    zbuf = lift['pix_depth'].numpy(); ext = float(np.ptp(V, 0).max())
    snap = lambda rc: int(np.argmin((prow - rc[0]) ** 2 + (pcol - rc[1]) ** 2))

    j = snap(C)
    D2, P2 = scipy.sparse.csgraph.dijkstra(G2, indices=j, return_predecessors=True)
    Ds, Ps = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=vs[j], return_predecessors=True)
    Dr, Pr = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=vr[j], return_predecessors=True)
    x = snap(a.target) if a.target else int(np.nanargmax(np.abs(Ds[vs] / diam3 - D2 / diam2)))

    fig, axs = plt.subplots(1, 3, figsize=(21, 7 * H / W + 1.2))
    p2 = path_from_pred(P2, x)
    axs[0].imshow(photo); axs[0].plot(pcol[p2], prow[p2], '-', c='yellow', lw=4)
    axs[0].set_title(f'2D geodesic (inside the mask)\ndistance {D2[x] / diam2:.3f}', fontsize=17)
    for ax, v, P, D, ti in ((axs[1], vs, Ps, Ds, 'lifted, before: vertex splat'), (axs[2], vr, Pr, Dr, 'lifted, after: raycast')):
        p3 = path_from_pred(P, v[x]); r, c, dep = project(V[p3], cam, box)
        ri, ci = np.clip(np.round(r).astype(int), 0, H - 1), np.clip(np.round(c).astype(int), 0, W - 1)
        vis = np.where(dep > zbuf[ri, ci] + 0.02 * ext, np.nan, 1.0)
        ax.imshow(photo); ax.plot(c, r, ':', c='yellow', lw=3); ax.plot(c * vis, r * vis, '-', c='yellow', lw=4)
        ax.set_title(f'{ti}\ndistance {D[v[x]] / diam3:.3f}  (dotted = behind the bear)', fontsize=17)
    for ax in axs:
        ax.plot(C[1], C[0], 'w*', ms=26, mec='k'); ax.plot(pcol[x], prow[x], 'o', ms=14, mfc='red', mec='w', mew=2); ax.axis('off')
    fig.suptitle(f'{t}: geodesic path between two visible pixels (star -> red), distance / diameter', fontsize=19)
    plt.tight_layout(rect=(0, 0, 1, 0.92)); plt.savefig(a.out, dpi=70)
    print(f'{t} rep {a.rep} {C} -> ({prow[x]}, {pcol[x]}): 2D {D2[x] / diam2:.3f} | splat {Ds[vs[x]] / diam3:.3f} | ray {Dr[vr[x]] / diam3:.3f}')


if __name__ == '__main__':
    main()
