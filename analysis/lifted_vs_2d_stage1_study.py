"""Why does the lifted teacher lose already at STAGE 1 (global mu)? (Tal, 2026-11-01; bears 186446, 171627, 32412, 109595)
Stage 1 only: no segments, one global ellipse. Per representative (= the 3 GT points, as in the <tag>_lifted_vs_2d_rows.png check) the
teacher distance from it to every mask pixel, 2D (inside the mask, as build_geodesic_tables.py) vs lifted (on the Pixal3D mesh, exactly as
build_lifted_geodesic_table.py: decimate -> largest component -> pixel -> vertex -> edge-graph Dijkstra), each over its own diameter (the
--geo_diag_2d the run trained with), the paths to ~8 neighbours around it, and the CHANGE lifted - 2D per pixel and per neighbour.
Figure (--out_dir/<tag>_stage1_study.png):
  top    : photo | --panel images (back-projections with scores) | the learned stage-1 global ellipse, 2D vs lifted
  per rep: 2D distance + 2D paths | lifted distance + lifted paths projected (dotted = hidden) | lifted - 2D (red = farther in 3D) | table
Usage (disc env, needs open3d):
  python analysis/lifted_vs_2d_stage1_study.py --tag lvis186446 --src_dir <runs_full_poly/lvis186446> --lift_path <..._full_lift.pth> \\
      --lifted_meta <..._lifted_seed0_full_meta.json> --mu_2d <2D run>/mu_aniso_stageA_end.pth --mu_lifted <lifted run>/mu_aniso[_stageA_end].pth \\
      --panel <png> "<title>" ... --out_dir <dir>
"""
import argparse, json, math, os, sys
import numpy as np, torch, scipy.ndimage, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph
from plot_lifted_geodesic_paths import grid_graph, path_from_pred, project
from plot_mu_ellipses import mu_dir
from geodesic_holes_probe import COLS


def ring(mask, c, n, frac):
    """n neighbours on a ring around c at frac of the mask's extent, pulled in until inside the mask."""
    rows, cols = np.nonzero(mask); rad = frac * max(np.ptp(rows), np.ptp(cols)); out = []
    for k in range(n):
        th = 2 * math.pi * k / n
        for s in np.linspace(1.0, 0.2, 17):
            r, cc = int(c[0] + s * rad * math.sin(th)), int(c[1] + s * rad * math.cos(th))
            if 0 <= r < mask.shape[0] and 0 <= cc < mask.shape[1] and mask[r, cc]:
                out.append((r, cc)); break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True); ap.add_argument('--src_dir', required=True); ap.add_argument('--lift_path', required=True)
    ap.add_argument('--lifted_meta', required=True); ap.add_argument('--mu_2d', required=True); ap.add_argument('--mu_lifted', required=True)
    ap.add_argument('--panel', nargs=2, action='append', default=[], metavar=('PNG', 'TITLE'))
    ap.add_argument('--out_dir', required=True); ap.add_argument('--n_nb', type=int, default=8)
    ap.add_argument('--ring_frac', type=float, default=0.25); ap.add_argument('--target_faces', type=int, default=200000)
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    S = a.src_dir; t = a.tag
    photo = np.array(Image.open(f'{S}/{t}.png').convert('RGB')); mask = torch.load(f'{S}/{t}_mask.pth').numpy().astype(bool)
    gt = torch.load(f'{S}/{t}_gt.pth', map_location='cpu'); reps = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
    diam2 = json.load(open(f'{S}/{t}_mask_geo_table_2d_seed0_meta.json'))['true_diameter_2d']
    diam3 = json.load(open(a.lifted_meta))['true_diameter_2d']

    # 2D graph (8-connected pixels in the mask) and the lifted graph + pixel -> vertex, as the two table builders
    G2, idx, prow, pcol = grid_graph(mask)
    lift = torch.load(a.lift_path, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']
    pv = lift['pix_vertex'].numpy(); has = pv >= 0
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~has, return_indices=True); pv = pv[ir, ic]
    V0 = lift['vertices'].numpy(); V, F = decimate(V0, lift['faces'].numpy(), a.target_faces)
    G3 = edge_graph(V, F); _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
    keep = np.nonzero(lab == np.bincount(lab).argmax())[0]; tree = cKDTree(V[keep])
    pix_v = keep[tree.query(V0[pv[prow, pcol]])[1]]                       # graph-2D node j (= pixel prow[j], pcol[j]) -> vertex
    zbuf = lift['pix_depth'].numpy(); ext = float(np.ptp(V, 0).max())
    snap = lambda rc: tuple(np.array([prow, pcol])[:, np.argmin((prow - rc[0]) ** 2 + (pcol - rc[1]) ** 2)])   # into the 2D graph

    nr, H, W = len(reps), *mask.shape
    nt = 2 + len(a.panel); rh = 26 / 4 * H / W + 0.9                # row height (in) so a map fills its column
    fig = plt.figure(figsize=(26, rh * (nr + 0.8) + 0.8))
    gs = fig.add_gridspec(nr + 1, 4 * nt, height_ratios=[0.8] + [1] * nr, hspace=0.25, wspace=0.3, left=0.01, right=0.99, top=0.94, bottom=0.01)
    # top row: photo, panels, stage-1 ellipses
    ax = fig.add_subplot(gs[0, 0:4]); ax.imshow(photo); ax.axis('off'); ax.set_title('image', fontsize=14)
    for k, (p, ti) in enumerate(a.panel):
        ax = fig.add_subplot(gs[0, 4 * (k + 1):4 * (k + 2)]); ax.imshow(Image.open(p)); ax.axis('off'); ax.set_title(ti.replace('\\n', '\n'), fontsize=14)
    ax = fig.add_subplot(gs[0, 4 * (nt - 1):]); ax.imshow(photo); ax.imshow(np.where(mask, np.nan, 0.0), cmap='gray', alpha=0.5, vmin=0, vmax=1)
    cy, cx = np.median(prow), np.median(pcol); R = 0.3 * min(mask.shape); th = np.radians(np.arange(0, 361, 3))
    ax.plot(cx + R * np.sin(th), cy + R * np.cos(th), 'w-', lw=1)
    ell = []
    for nm, p, col in (('2D', a.mu_2d, 'tab:blue'), ('lifted', a.mu_lifted, 'tab:red')):
        P = torch.load(p, map_location='cpu')['mu_aniso'][-1].tolist(); m = np.array([mu_dir(P, d) for d in np.degrees(th)])
        ax.plot(cx + R * m * np.sin(th), cy + R * m * np.cos(th), '-', c=col, lw=3, label=f'{nm}: vert {mu_dir(P, 0):.2f}, horiz {mu_dir(P, 90):.2f}')
        ell.append(f'{nm:7s} mu vert {mu_dir(P, 0):.3f} horiz {mu_dir(P, 90):.3f}')
    ax.legend(loc='lower center', fontsize=10); ax.axis('off'); ax.set_title('stage-1 global ellipse\n(white: mu = 1)', fontsize=14)
    cw = 4 * nt // 4                                                   # rep rows: 3 maps + the table, equal widths

    report = [f'{t}: diameter 2D {diam2:.1f} px, lifted {diam3:.4f}'] + ell
    for k, C in enumerate(reps):
        C = snap(C); nbs = [snap(n) for n in ring(mask, C, a.n_nb, a.ring_frac)]
        D2, P2 = scipy.sparse.csgraph.dijkstra(G2, indices=idx[C], return_predecessors=True)
        D3, P3 = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=pix_v[idx[C]], return_predecessors=True)
        d2 = np.full(mask.shape, np.nan); d2[prow, pcol] = D2 / diam2
        d3 = np.full(mask.shape, np.nan); d3[prow, pcol] = D3[pix_v] / diam3
        diff = d3 - d2; far = np.unravel_index(np.nanargmax(np.abs(diff)), diff.shape)
        axs = [fig.add_subplot(gs[k + 1, j * cw:(j + 1) * cw]) for j in range(4)]
        axs[0].imshow(photo); axs[0].imshow(d2, cmap='turbo', vmin=0, vmax=1, alpha=0.75); axs[0].set_title(f'rep {k + 1}: 2D distance / diameter + paths', fontsize=13)
        axs[1].imshow(photo); axs[1].imshow(d3, cmap='turbo', vmin=0, vmax=1, alpha=0.75); axs[1].set_title(f'rep {k + 1}: lifted distance / diameter + paths', fontsize=13)
        axs[2].imshow(photo); im = axs[2].imshow(diff, cmap='RdBu_r', vmin=-0.4, vmax=0.4, alpha=0.85)
        axs[2].set_title(f'change lifted - 2D (red = farther in 3D)\nx = largest change {diff[far]:+.2f}', fontsize=13)
        plt.colorbar(im, ax=axs[2], fraction=0.04, pad=0.01)
        lines = [f'rep {k + 1} {C}', f'{"nb":3s} {"2D":>6s} {"lifted":>7s} {"change":>7s}']
        for j, N in enumerate(nbs + [far]):
            col = np.array(COLS[j % len(COLS)]) / 255 if j < len(nbs) else 'k'
            n2 = idx[N]; p2 = path_from_pred(P2, n2); axs[0].plot(pcol[p2], prow[p2], '-', c=col, lw=2.2)
            p3 = path_from_pred(P3, pix_v[n2]); r, c, dep = project(V[p3], cam, box)
            ri, ci = np.clip(np.round(r).astype(int), 0, mask.shape[0] - 1), np.clip(np.round(c).astype(int), 0, mask.shape[1] - 1)
            vis = np.where(dep > zbuf[ri, ci] + 0.02 * ext, np.nan, 1.0)
            axs[1].plot(c, r, ':', c=col, lw=1.8); axs[1].plot(c * vis, r * vis, '-', c=col, lw=2.6)
            nm = str(j + 1) if j < len(nbs) else 'x'
            for q in axs[:3]:
                q.plot(N[1], N[0], 'X' if nm == 'x' else 'o', ms=10, mfc=col, mec='w' if nm == 'x' else 'k')
                q.annotate(nm, (N[1] + 5, N[0] - 5), color='w', fontsize=12, weight='bold')
            lines.append(f'{nm:3s} {d2[N]:6.3f} {d3[N]:7.3f} {d3[N] - d2[N]:+7.3f}')
        for q in axs[:3]:
            q.plot(C[1], C[0], 'w*', ms=20, mec='k'); q.axis('off')
        axs[3].axis('off'); axs[3].text(0, 1, '\n'.join(lines), va='top', family='monospace', fontsize=13)
        report += lines + [f'  mean |change| over the mask {np.nanmean(np.abs(diff)):.3f}, lifted farther on {np.nanmean(diff > 0):.0%} of pixels']
    fig.suptitle(f'{t} - stage 1 only: 2D teacher vs lifted teacher (distances / own diameter; star = rep = GT point, x = largest change)', fontsize=17)
    out = os.path.join(a.out_dir, f'{t}_stage1_study.png'); plt.savefig(out, dpi=55)
    open(os.path.join(a.out_dir, f'{t}_stage1_study.txt'), 'w').write('\n'.join(report) + '\n')
    print('\n'.join(report)); print('saved', out)


if __name__ == '__main__':
    main()
