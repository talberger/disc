"""Do mask pixels land on the FRONT of the lifted mesh? (Tal, 2026-11-08; the stage-1 study's x pixels, e.g. 171627 rep 3, end on a dotted =
hidden path.) Follows the pixel -> vertex chain of build_lifted_geodesic_table.py step by step and checks each step against the front depth:
  raw   : lift['pix_vertex'] (pixels without one take the nearest pixel's, as the table builder)
  final : -> decimate -> largest component -> nearest kept vertex (the vertex the lifted Dijkstra really starts / ends at)
per pixel: depth of the vertex - pix_depth (> tol = behind the visible surface) and how far it projects from its own pixel.
The x pixel of each rep (largest |lifted - 2D|, as lifted_vs_2d_stage1_study.py) is recomputed and reported.
Out: --out_dir/<tag>_pixel_vertex_check.{png,txt}
Usage (disc env, needs open3d):
  python analysis/lifted_pixel_vertex_check.py --tag lvis171627 --src_dir <runs_full_poly/lvis171627> --lift_path <..._full_lift.pth> \\
      --lifted_meta <..._lifted_seed0_full_meta.json> --out_dir <dir>
"""
import argparse, json, os, sys
import numpy as np, torch, scipy.ndimage, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph
from plot_lifted_geodesic_paths import grid_graph, project


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True); ap.add_argument('--src_dir', required=True); ap.add_argument('--lift_path', required=True)
    ap.add_argument('--lifted_meta', required=True); ap.add_argument('--out_dir', required=True)
    ap.add_argument('--target_faces', type=int, default=200000); ap.add_argument('--tol', type=float, default=0.02, help='x mesh extent')
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    S = a.src_dir; t = a.tag
    photo = np.array(Image.open(f'{S}/{t}.png').convert('RGB')); mask = torch.load(f'{S}/{t}_mask.pth').numpy().astype(bool)
    gt = torch.load(f'{S}/{t}_gt.pth', map_location='cpu'); reps = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
    diam2 = json.load(open(f'{S}/{t}_mask_geo_table_2d_seed0_meta.json'))['true_diameter_2d']
    diam3 = json.load(open(a.lifted_meta))['true_diameter_2d']

    # the chain, as build_lifted_geodesic_table.py
    G2, idx, prow, pcol = grid_graph(mask)
    lift = torch.load(a.lift_path, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']
    pv0 = lift['pix_vertex'].numpy(); has = pv0 >= 0
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~has, return_indices=True); pv = pv0[ir, ic]
    zbuf = lift['pix_depth'].numpy()[ir, ic]                              # the front depth (of the pixel that gave the vertex)
    V0 = lift['vertices'].numpy(); V, F = decimate(V0, lift['faces'].numpy(), a.target_faces)
    G3 = edge_graph(V, F); _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
    keep = np.nonzero(lab == np.bincount(lab).argmax())[0]; tree = cKDTree(V[keep])
    pix_v = keep[tree.query(V0[pv[prow, pcol]])[1]]
    ext = float(np.ptp(V, 0).max()); tol = a.tol * ext

    def check(P):                                                        # P: 3D point per graph node -> (depth - front, px offset)
        r, c, dep = project(P, cam, box)
        return dep - zbuf[prow, pcol], np.hypot(r - prow, c - pcol)
    dz_raw, off_raw = check(V0[pv[prow, pcol]]); dz_fin, off_fin = check(V[pix_v])
    img = lambda v: (lambda m: (m.__setitem__((prow, pcol), v), m)[1])(np.full(mask.shape, np.nan))
    behind = dz_fin > tol; nohit = ~has[prow, pcol]

    # the x pixel per rep (as the study)
    snap = lambda rc: int(np.argmin((prow - rc[0]) ** 2 + (pcol - rc[1]) ** 2))
    xs, lines = [], [f'{t}: mesh extent {ext:.3f}, tol {tol:.4f} (depth behind the front surface)',
                     f'pixels in mask {len(prow)}, without pix_vertex (filled from the nearest) {nohit.mean():.1%}',
                     f'raw   vertex behind the front: {np.mean(dz_raw > tol):.1%}, projects > 3 px away: {np.mean(off_raw > 3):.1%}',
                     f'final vertex behind the front: {behind.mean():.1%}, projects > 3 px away: {np.mean(off_fin > 3):.1%}',
                     f'kept component {len(keep)} of {len(V)} decimated vertices', '']
    for k, C in enumerate(reps):
        j = snap(C)
        D2 = scipy.sparse.csgraph.dijkstra(G2, indices=j); D3 = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=pix_v[j])
        diff = D3[pix_v] / diam3 - D2 / diam2; x = int(np.nanargmax(np.abs(diff)))
        xs.append((j, x))
        for nm, q in (('rep', j), ('x  ', x)):
            lines.append(f'rep {k + 1} {nm} ({prow[q]}, {pcol[q]}): pix_vertex {"yes" if has[prow[q], pcol[q]] else "NO (filled)"}, '
                         f'depth - front raw {dz_raw[q]:+.4f} final {dz_fin[q]:+.4f} -> {"BEHIND" if dz_fin[q] > tol else "front"}, '
                         f'offset raw {off_raw[q]:.1f} px final {off_fin[q]:.1f} px' + (f', change {diff[x]:+.3f}' if nm == 'x  ' else ''))

    fig, axs = plt.subplots(1, 5, figsize=(30, 6.5 * mask.shape[0] / mask.shape[1] + 1))
    pan = [(nohit.astype(float), 'gray_r', 0, 1, 'pixels without pix_vertex (black)'),
           (dz_raw / ext, 'RdBu_r', -0.1, 0.1, 'raw vertex: depth - front (/ extent)'),
           (dz_fin / ext, 'RdBu_r', -0.1, 0.1, 'final vertex: depth - front (/ extent)'),
           (np.minimum(off_fin, 30), 'magma', 0, 30, 'final vertex: projects how far (px, cap 30)'),
           (behind.astype(float), 'Reds', 0, 1, f'final vertex BEHIND (red) - {behind.mean():.1%}')]
    for ax, (v, cm, lo, hi, ti) in zip(axs, pan):
        ax.imshow(photo); im = ax.imshow(img(v), cmap=cm, vmin=lo, vmax=hi, alpha=0.8); ax.set_title(ti, fontsize=14); ax.axis('off')
        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.01)
        for k, (j, x) in enumerate(xs):
            ax.plot(pcol[j], prow[j], 'w*', ms=18, mec='k'); ax.plot(pcol[x], prow[x], 'X', ms=12, mfc='k', mec='w')
            ax.annotate(str(k + 1), (pcol[j] + 6, prow[j] - 6), color='w', fontsize=13, weight='bold')
            ax.annotate(f'x{k + 1}', (pcol[x] + 6, prow[x] - 6), color='w', fontsize=13, weight='bold')
    fig.suptitle(f'{t}: does each pixel map to the FRONT of the lifted mesh? (star = rep, X = its largest-change pixel)', fontsize=16)
    plt.tight_layout(); out = os.path.join(a.out_dir, f'{t}_pixel_vertex_check.png'); plt.savefig(out, dpi=60)
    open(os.path.join(a.out_dir, f'{t}_pixel_vertex_check.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines)); print('saved', out)


if __name__ == '__main__':
    main()
