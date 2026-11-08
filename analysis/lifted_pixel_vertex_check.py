"""Do mask pixels land on the FRONT of the lifted mesh? (Tal, 2026-11-08; the stage-1 study's x pixels, e.g. 171627 rep 3 -> x3, end on a
dotted = hidden path, and in MeshLab x3 sits on the bear's back.) lift.py's pix_vertex is a VERTEX splat (per pixel the nearest vertex that
falls in it), so its own pix_depth cannot tell; the reference here is a ray cast on the faces (build_lifted_geodesic_table.raycast_pix_point).
Per pixel: depth of the splat vertex - depth of the first ray hit (> tol = the splat saw through to the back), for the raw splat vertex and for
the final one (after decimate -> largest component -> nearest kept vertex). The x pixel of each rep (largest |lifted - 2D|, splat chain, as
lifted_vs_2d_stage1_study.py) is recomputed, and its lifted distance from the rep is given for both mappings.
Out: --out_dir/<tag>_pixel_vertex_check.{png,txt}
Usage (disc env, needs open3d):
  python analysis/lifted_pixel_vertex_check.py --tag lvis171627 --src_dir <runs_full_poly/lvis171627> --lift_path <..._full_lift.pth> \\
      --lifted_meta <..._lifted_seed0_full_meta.json> --out_dir <dir>
"""
import argparse, json, os, sys
import numpy as np, torch, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph, pix_points, raycast_pix_point
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

    G2, idx, prow, pcol = grid_graph(mask)
    lift = torch.load(a.lift_path, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']; H, W = mask.shape
    PS, has_s = pix_points(lift, H, W, 'splat'); PR, has_r = pix_points(lift, H, W, 'raycast')
    _, zray = raycast_pix_point(lift, H, W)
    V, F = decimate(lift['vertices'].numpy(), lift['faces'].numpy(), a.target_faces)
    G3 = edge_graph(V, F); _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
    keep = np.nonzero(lab == np.bincount(lab).argmax())[0]; tree = cKDTree(V[keep])
    vs = keep[tree.query(PS[prow, pcol])[1]]; vr = keep[tree.query(PR[prow, pcol])[1]]
    ext = float(np.ptp(V, 0).max()); tol = a.tol * ext
    zr = zray[prow, pcol]; ok = np.isfinite(zr)                           # pixels the ray hits (else: no reference)
    dz = lambda P: np.where(ok, project(P, cam, box)[2] - np.where(ok, zr, 0), np.nan)
    dz_raw, dz_fin, dz_rfin = dz(PS[prow, pcol]), dz(V[vs]), dz(V[vr])
    img = lambda v: (lambda m: (m.__setitem__((prow, pcol), v), m)[1])(np.full(mask.shape, np.nan))
    behind = dz_fin > tol

    snap = lambda rc: int(np.argmin((prow - rc[0]) ** 2 + (pcol - rc[1]) ** 2))
    lines = [f'{t}: mesh extent {ext:.3f}, tol {tol:.4f} (camera depth beyond the first ray hit)',
             f'pixels in mask {len(prow)}: no splat vertex {np.mean(~has_s[prow, pcol]):.1%}, ray misses {np.mean(~ok):.1%}',
             f'splat raw   vertex BEHIND the ray hit: {np.nanmean(dz_raw > tol):.1%} of the hit pixels',
             f'splat final vertex BEHIND the ray hit: {np.nanmean(behind):.1%}',
             f'ray   final vertex BEHIND the ray hit: {np.nanmean(dz_rfin > tol):.1%} (decimation / snapping only)', '']
    xs = []
    for k, C in enumerate(reps):
        j = snap(C)
        D2 = scipy.sparse.csgraph.dijkstra(G2, indices=j)
        Ds = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=vs[j]); Dr = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=vr[j])
        diff = Ds[vs] / diam3 - D2 / diam2; x = int(np.nanargmax(np.abs(diff))); xs.append((j, x))
        for nm, q in (('rep', j), ('x  ', x)):
            lines.append(f'rep {k + 1} {nm} ({prow[q]}, {pcol[q]}): splat vertex {"yes" if has_s[prow[q], pcol[q]] else "NO (filled)"}, '
                         f'beyond the ray hit: splat {dz_fin[q]:+.4f} -> {"BEHIND" if dz_fin[q] > tol else "front"}, ray {dz_rfin[q]:+.4f}')
        lines.append(f'  rep -> x: 2D {D2[x] / diam2:.3f} | lifted splat {Ds[vs[x]] / diam3:.3f} | lifted ray {Dr[vr[x]] / diam3:.3f} '
                     f'(same diameter {diam3:.4f})')

    fig, axs = plt.subplots(1, 4, figsize=(26, 6.5 * H / W + 1))
    pan = [(dz_raw / ext, 'RdBu_r', -0.3, 0.3, 'splat vertex: depth - ray hit (/ extent)\nred = sees through to the back'),
           (behind.astype(float), 'Reds', 0, 1, f'splat final vertex BEHIND (red) - {np.nanmean(behind):.1%}'),
           (dz_rfin / ext, 'RdBu_r', -0.3, 0.3, 'ray final vertex: depth - ray hit (/ extent)'),
           ((~has_s[prow, pcol]).astype(float) + 2 * (~ok), 'viridis', 0, 3, 'no splat vertex (1) / ray miss (2) / both (3)')]
    for ax, (v, cm, lo, hi, ti) in zip(axs, pan):
        ax.imshow(photo); im = ax.imshow(img(v), cmap=cm, vmin=lo, vmax=hi, alpha=0.8); ax.set_title(ti, fontsize=14); ax.axis('off')
        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.01)
        for k, (j, x) in enumerate(xs):
            ax.plot(pcol[j], prow[j], 'w*', ms=18, mec='k'); ax.plot(pcol[x], prow[x], 'X', ms=12, mfc='k', mec='w')
            ax.annotate(str(k + 1), (pcol[j] + 6, prow[j] - 6), color='w', fontsize=13, weight='bold')
            ax.annotate(f'x{k + 1}', (pcol[x] + 6, prow[x] - 6), color='w', fontsize=13, weight='bold')
    fig.suptitle(f'{t}: does each pixel map to the FRONT of the lifted mesh? splat (lift.py) vs ray cast (star = rep, X = its largest-change pixel)',
                 fontsize=16)
    plt.tight_layout(); out = os.path.join(a.out_dir, f'{t}_pixel_vertex_check.png'); plt.savefig(out, dpi=60)
    open(os.path.join(a.out_dir, f'{t}_pixel_vertex_check.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines)); print('saved', out)


if __name__ == '__main__':
    main()
