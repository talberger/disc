"""Geodesic PATHS centre -> neighbours: 2D (inside the mask, as the old teacher) vs on the Pixal3D-lifted mesh (Tal, 2026-10-26).
The crowding study's pairs on horse 56069 (12 Oct): C = (270, 150) nose tip; N1 (250, 230) body right, N2 (70, 140) forehead, N3 (330, 30) chest
left, (row, col) on the crop. Same mesh processing as analysis/build_lifted_geodesic_table.py (decimation, largest component, pixel -> vertex).
Figure: photo + 2D paths | photo + lifted paths projected with Pixal3D's camera (dashed where the path is hidden behind the visible surface) |
the lifted mesh from the side with the paths. Table: geodesic length / diameter, 2D vs lifted.
  python analysis/plot_lifted_geodesic_paths.py --lift_path <tag>_lift.pth --mask_path <tag>_mask.pth --img_path <tag>.png \\
      --lifted_meta <tag>_mask_geo_table_lifted_seed0_meta.json --out <png> [--centre 270 150 --neighbours 250 230 70 140 330 30]
"""
import argparse, json, math, os, sys
import numpy as np
import scipy.ndimage, scipy.sparse, scipy.sparse.csgraph
import torch
from scipy.spatial import cKDTree
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph


def grid_graph(mask):
    """8-connected pixel graph inside the mask (edge = Euclidean pixel step), largest component."""
    lab, _ = scipy.ndimage.label(mask, structure=np.ones((3, 3)))
    mask = lab == np.bincount(lab[mask]).argmax()
    rows, cols = np.nonzero(mask); idx = -np.ones(mask.shape, int); idx[rows, cols] = np.arange(len(rows))
    src, dst, w = [], [], []
    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        r2, c2 = rows + dr, cols + dc
        ok = (r2 >= 0) & (r2 < mask.shape[0]) & (c2 >= 0) & (c2 < mask.shape[1])
        ok[ok] &= mask[r2[ok], c2[ok]]
        src.append(idx[rows[ok], cols[ok]]); dst.append(idx[r2[ok], c2[ok]]); w.append(np.full(ok.sum(), math.hypot(dr, dc)))
    s, d, ww = map(np.concatenate, (src, dst, w)); n = len(rows)
    return scipy.sparse.coo_matrix((np.r_[ww, ww], (np.r_[s, d], np.r_[d, s])), shape=(n, n)).tocsr(), idx, rows, cols


def path_from_pred(pred, target):
    p = [target]
    while pred[p[-1]] >= 0:
        p.append(pred[p[-1]])
    return p[::-1]


def project(P, cam, box):
    """Pixal3D camera (Blender convention): world -> (row, col) on OUR crop, and depth."""
    d = cam['distance']; c2w = np.array([[1, 0, 0, 0], [0, 0, -1, -d], [0, 1, 0, 0], [0, 0, 0, 1.0]])
    pc = (np.c_[P, np.ones(len(P))] @ np.linalg.inv(c2w).T)[:, :3]
    x0, y0, S = box
    f = (16.0 / math.tan(cam['camera_angle_x'] / 2)) * S / 32.0
    col = f * pc[:, 0] / (-pc[:, 2]) + S / 2 + x0
    row = -f * pc[:, 1] / (-pc[:, 2]) + S / 2 + y0
    return row, col, -pc[:, 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lift_path', required=True); ap.add_argument('--mask_path', required=True); ap.add_argument('--img_path', required=True)
    ap.add_argument('--lifted_meta', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--centre', type=int, nargs=2, default=[270, 150])
    ap.add_argument('--neighbours', type=int, nargs='+', default=[250, 230, 70, 140, 330, 30])
    ap.add_argument('--target_faces', type=int, default=200000)
    a = ap.parse_args()
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    C = tuple(a.centre); Ns = [tuple(a.neighbours[i:i + 2]) for i in range(0, len(a.neighbours), 2)]
    names = [f'N{k + 1}' for k in range(len(Ns))]
    photo = np.array(Image.open(a.img_path).convert('RGB')); mask = torch.load(a.mask_path).numpy().astype(bool)

    # 2D: geodesic inside the mask
    G2, idx, rows, cols = grid_graph(mask)
    D2, P2 = scipy.sparse.csgraph.dijkstra(G2, indices=idx[C], return_predecessors=True)
    diam2 = 0.0; s = idx[C]
    for _ in range(4):
        dd = scipy.sparse.csgraph.dijkstra(G2, indices=s); far = int(np.argmax(np.where(np.isfinite(dd), dd, -1)))
        if dd[far] <= diam2 + 1e-9: break
        diam2, s = float(dd[far]), far

    # lifted: geodesic on the decimated mesh, pixels -> vertices exactly as the table builder
    lift = torch.load(a.lift_path, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']
    pv = lift['pix_vertex'].numpy(); has = pv >= 0
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~has, return_indices=True); pv = pv[ir, ic]
    V0 = lift['vertices'].numpy(); V, F = decimate(V0, lift['faces'].numpy(), a.target_faces)
    G3 = edge_graph(V, F); _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
    keep = np.nonzero(lab == np.bincount(lab).argmax())[0]; tree = cKDTree(V[keep])
    vtx = lambda rc: int(keep[tree.query(V0[pv[rc]])[1]])
    D3, P3 = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=vtx(C), return_predecessors=True)
    diam3 = json.load(open(a.lifted_meta))['true_diameter_2d']

    zbuf = lift['pix_depth'].numpy(); ext = float(np.ptp(V, 0).max())
    fig, ax = plt.subplots(1, 3, figsize=(17, 7.5))
    for k in (0, 1):
        ax[k].imshow(photo); ax[k].imshow(np.where(mask, np.nan, 0.0), cmap='gray', alpha=0.5, vmin=0, vmax=1); ax[k].axis('off')
    colours = ['tab:red', 'tab:orange', 'tab:cyan', 'tab:green', 'tab:purple']
    lines = [f'{"pair":10s} {"2D geodesic / diam":>20s} {"lifted geodesic / diam":>24s}   (Euclidean px)']
    sub = np.random.RandomState(0).choice(len(V), min(25000, len(V)), replace=False)
    ax[2].scatter(V[sub, 1], V[sub, 2], s=0.2, c='0.75'); ax[2].set_aspect('equal'); ax[2].axis('off')
    ax[2].set_title('lifted mesh from the SIDE (camera on the left, depth -> right); paths')
    for k, (N, nm) in enumerate(zip(Ns, names)):
        col = colours[k % len(colours)]
        p2 = path_from_pred(P2, idx[N]); ax[0].plot(cols[p2], rows[p2], '-', c=col, lw=2.5, label=nm)
        t = vtx(N); p3 = path_from_pred(P3, t)
        r, c, dep = project(V[p3], cam, box)
        ri, ci = np.clip(np.round(r).astype(int), 0, mask.shape[0] - 1), np.clip(np.round(c).astype(int), 0, mask.shape[1] - 1)
        hidden = dep > zbuf[ri, ci] + 0.02 * ext
        ax[1].plot(c, r, ':', c=col, lw=2); vis = np.where(hidden, np.nan, 1.0); ax[1].plot(c * vis, r * vis, '-', c=col, lw=2.8, label=nm)
        ax[2].plot(V[p3, 1], V[p3, 2], '-', c=col, lw=2.5, label=nm)
        lines.append(f'C -> {nm:5s} {D2[idx[N]] / diam2:20.3f} {D3[t] / diam3:24.3f}   ({math.dist(C, N):.0f})')
    for k in (0, 1):
        ax[k].plot(C[1], C[0], 'w*', ms=18, mec='k'); [ax[k].plot(N[1], N[0], 'wo', ms=9, mec='k') for N in Ns]
        [ax[k].annotate(nm, (N[1] + 6, N[0] - 6), color='w', fontsize=13, weight='bold') for N, nm in zip(Ns, names)]
    ax[0].set_title('2D geodesic inside the mask (old teacher)'); ax[1].set_title('lifted 3D geodesic, projected (dotted = hidden)')
    ax[0].legend(loc='lower right'); ax[2].legend(loc='lower right')
    fig.text(0.01, 0.01, '\n'.join(lines), family='monospace', fontsize=11)
    plt.tight_layout(rect=(0, 0.1, 1, 1)); plt.savefig(a.out, dpi=85)
    print('\n'.join(lines)); print('saved', a.out)


if __name__ == '__main__':
    main()
