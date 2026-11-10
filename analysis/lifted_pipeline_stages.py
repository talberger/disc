"""Where does the lifted pipeline break? One bear, stage by stage, for SEVERAL lifts side by side (Tal, 2026-11-10; 151955: lifted_ray 16.2,
lifted_amodal 38.6 -> the lift of the amodal-completed image is the suspect). Same chain as build_lifted_geodesic_table.py
(decimate -> largest component -> ray-cast pixel -> vertex -> edge-graph Dijkstra). Figures (--out_dir):
  <tag>_stages_lift.png     per lift: ray-cast depth on the photo | the mesh from the side | from the top (coloured by camera depth) + stats
  <tag>_stages_teacher.png  per rep (= GT point): distance / diameter + paths to ~8 neighbours, 2D | each lift | change last lift - first lift
  <tag>_stages_ellipses.png the learned stage-1 global ellipse, 2D and each lift
  <tag>_<name>_lift.ply     with --ply: the decimated mesh coloured by camera depth (MeshLab)
Usage (disc env, needs open3d):
  python analysis/lifted_pipeline_stages.py --tag lvis151955 --src_dir <runs_full_poly/lvis151955> --mu_2d <2D run>/mu_aniso_stageA_end.pth \\
      --lift ray <full_lift.pth> <ray meta.json> <ray run>/mu_aniso.pth --lift amodal <amodal_lift.pth> <meta.json> <run>/mu_aniso.pth --out_dir <dir>
"""
import argparse, json, os, sys
import numpy as np, torch, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph, pix_points, raycast_pix_point
from plot_lifted_geodesic_paths import grid_graph, path_from_pred, project
from lifted_vs_2d_stage1_study import ring
from plot_mu_ellipses import mu_dir
from geodesic_holes_probe import COLS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True); ap.add_argument('--src_dir', required=True); ap.add_argument('--mu_2d', required=True)
    ap.add_argument('--lift', nargs=4, action='append', required=True, metavar=('NAME', 'LIFT', 'META', 'MU'))
    ap.add_argument('--out_dir', required=True); ap.add_argument('--n_nb', type=int, default=8); ap.add_argument('--ring_frac', type=float, default=0.25)
    ap.add_argument('--target_faces', type=int, default=200000); ap.add_argument('--ply', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    S = a.src_dir; t = a.tag
    photo = np.array(Image.open(f'{S}/{t}.png').convert('RGB')); mask = torch.load(f'{S}/{t}_mask.pth').numpy().astype(bool); H, W = mask.shape
    gt = torch.load(f'{S}/{t}_gt.pth', map_location='cpu'); reps = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
    diam2 = json.load(open(f'{S}/{t}_mask_geo_table_2d_seed0_meta.json'))['true_diameter_2d']
    G2, idx, prow, pcol = grid_graph(mask)
    snap = lambda rc: tuple(np.array([prow, pcol])[:, np.argmin((prow - rc[0]) ** 2 + (pcol - rc[1]) ** 2)])

    # per lift: the graph the table is built on, pixel -> vertex, the ray-cast depth
    Ls = []
    for name, lp, meta, mu in a.lift:
        lift = torch.load(lp, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']
        PP, _ = pix_points(lift, H, W); _, zray = raycast_pix_point(lift, H, W)
        V, F = decimate(lift['vertices'].numpy(), lift['faces'].numpy(), a.target_faces)
        G3 = edge_graph(V, F); nc, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
        keep = np.nonzero(lab == np.bincount(lab).argmax())[0]
        pix_v = keep[cKDTree(V[keep]).query(PP[prow, pcol])[1]]
        Ls.append(dict(name=name, cam=cam, box=box, V=V, F=F, G3=G3, pix_v=pix_v, zray=zray, ext=float(np.ptp(V, 0).max()), mu=mu,
                       diam=json.load(open(meta))['true_diameter_2d'], ncomp=nc, big=len(keep) / len(V), miss=float(np.mean(~np.isfinite(zray[mask])))))
        if a.ply:
            import open3d as o3d, matplotlib.cm
            dep = project(V, cam, box)[2]; m = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(V), o3d.utility.Vector3iVector(F))
            m.vertex_colors = o3d.utility.Vector3dVector(matplotlib.cm.turbo((dep - dep.min()) / np.ptp(dep))[:, :3])
            o3d.io.write_triangle_mesh(os.path.join(a.out_dir, f'{t}_{name}_lift.ply'), m)

    # 1. the lifts: depth on the photo, the mesh from the side and from the top (image row / column vs camera depth)
    zs = np.concatenate([L['zray'][mask & np.isfinite(L['zray'])] for L in Ls]); lo, hi = np.percentile(zs, [1, 99])
    fig, axs = plt.subplots(len(Ls), 3, figsize=(24, (7 * H / W + 0.8) * len(Ls)), squeeze=False)
    for ax, L in zip(axs, Ls):
        z = np.where(mask & np.isfinite(L['zray']), L['zray'], np.nan)
        ax[0].imshow(photo); im = ax[0].imshow(z, cmap='turbo', vmin=lo, vmax=hi, alpha=0.85); plt.colorbar(im, ax=ax[0], fraction=0.04, pad=0.01)
        ax[0].imshow(np.where(mask & ~np.isfinite(L['zray']), 1.0, np.nan), cmap='gray', vmin=0, vmax=1)
        ax[0].set_title(f'{L["name"]}: camera depth of the first ray hit (blue = near; white = ray misses, {L["miss"]:.1%})', fontsize=14)
        r, c, dep = project(L['V'], L['cam'], L['box']); s = np.random.default_rng(0).choice(len(r), min(len(r), 60000), replace=False)
        ax[1].scatter(dep[s], r[s], c=dep[s], cmap='turbo', vmin=lo, vmax=hi, s=1); ax[1].set_ylim(H, 0); ax[1].set_xlabel('camera depth'); ax[1].set_ylabel('image row')
        ax[1].set_title(f'{L["name"]}: mesh from the SIDE (camera on the left)\ncomponents {L["ncomp"]}, largest {L["big"]:.1%}, diameter {L["diam"]:.3f}', fontsize=14)
        ax[2].scatter(c[s], dep[s], c=dep[s], cmap='turbo', vmin=lo, vmax=hi, s=1); ax[2].set_xlim(0, W); ax[2].set_xlabel('image column'); ax[2].set_ylabel('camera depth')
        ax[2].set_title(f'{L["name"]}: mesh from the TOP (camera at the bottom)', fontsize=14)
        for q in ax[1:]: q.set_aspect('auto')
        ax[0].axis('off')
        for k, C in enumerate(reps):
            ax[0].plot(C[1], C[0], 'w*', ms=18, mec='k'); ax[0].annotate(str(k + 1), (C[1] + 6, C[0] - 6), color='w', fontsize=13, weight='bold')
    fig.suptitle(f'{t}: the lifted meshes', fontsize=18); plt.tight_layout(rect=(0, 0, 1, 0.97)); plt.savefig(os.path.join(a.out_dir, f'{t}_stages_lift.png'), dpi=55); plt.close()

    # 2. the teacher: per rep the distance / diameter and the paths, 2D | each lift | change last - first
    nc = len(Ls) + 3; rep_lines = []
    fig, axs = plt.subplots(len(reps), nc, figsize=(6.2 * nc, (6.2 * H / W + 0.7) * len(reps)), squeeze=False)
    for k, C in enumerate(reps):
        C = snap(C); nbs = [snap(n) for n in ring(mask, C, a.n_nb, a.ring_frac)]; ax = axs[k]
        D2, P2 = scipy.sparse.csgraph.dijkstra(G2, indices=idx[C], return_predecessors=True)
        d2 = np.full(mask.shape, np.nan); d2[prow, pcol] = D2 / diam2
        ax[0].imshow(photo); ax[0].imshow(d2, cmap='turbo', vmin=0, vmax=1, alpha=0.75); ax[0].set_title(f'rep {k + 1}: 2D', fontsize=14)
        d3s = []
        for j, L in enumerate(Ls):
            D3, P3 = scipy.sparse.csgraph.dijkstra(L['G3'], directed=False, indices=L['pix_v'][idx[C]], return_predecessors=True)
            d3 = np.full(mask.shape, np.nan); d3[prow, pcol] = D3[L['pix_v']] / L['diam']; d3s.append(d3)
            q = ax[1 + j]; q.imshow(photo); q.imshow(d3, cmap='turbo', vmin=0, vmax=1, alpha=0.75); q.set_title(f'rep {k + 1}: lifted {L["name"]}', fontsize=14)
            for n, N in enumerate(nbs):
                p3 = path_from_pred(P3, L['pix_v'][idx[N]]); r, c, dep = project(L['V'][p3], L['cam'], L['box'])
                ri, ci = np.clip(np.round(r).astype(int), 0, H - 1), np.clip(np.round(c).astype(int), 0, W - 1)
                vis = np.where(dep > L['zray'][ri, ci] + 0.02 * L['ext'], np.nan, 1.0); col = np.array(COLS[n % len(COLS)]) / 255
                q.plot(c, r, ':', c=col, lw=1.8); q.plot(c * vis, r * vis, '-', c=col, lw=2.6)
        diff = d3s[-1] - d3s[0]; q = ax[nc - 2]; q.imshow(photo); im = q.imshow(diff, cmap='RdBu_r', vmin=-0.4, vmax=0.4, alpha=0.85)
        q.set_title(f'change {Ls[-1]["name"]} - {Ls[0]["name"]} (red = farther)', fontsize=14); plt.colorbar(im, ax=q, fraction=0.04, pad=0.01)
        lines = [f'rep {k + 1} {C}', f'{"nb":3s} {"2D":>6s} ' + ' '.join(f'{L["name"]:>7s}' for L in Ls)]
        for n, N in enumerate(nbs):
            col = np.array(COLS[n % len(COLS)]) / 255; p2 = path_from_pred(P2, idx[N]); ax[0].plot(pcol[p2], prow[p2], '-', c=col, lw=2.2)
            for q in ax[:nc - 1]:
                q.plot(N[1], N[0], 'o', ms=10, mfc=col, mec='k'); q.annotate(str(n + 1), (N[1] + 5, N[0] - 5), color='w', fontsize=12, weight='bold')
            lines.append(f'{n + 1:<3d} {d2[N]:6.3f} ' + ' '.join(f'{d[N]:7.3f}' for d in d3s))
        lines.append('mean |change| vs 2D: ' + ', '.join(f'{L["name"]} {np.nanmean(np.abs(d - d2)):.3f}' for L, d in zip(Ls, d3s)))
        for q in ax[:nc - 1]:
            q.plot(C[1], C[0], 'w*', ms=20, mec='k'); q.axis('off')
        ax[nc - 1].axis('off'); ax[nc - 1].text(0, 1, '\n'.join(lines), va='top', family='monospace', fontsize=13, transform=ax[nc - 1].transAxes)
        rep_lines += lines
    fig.suptitle(f'{t}: teacher distance / own diameter from each rep (= GT point) and the paths to {a.n_nb} neighbours (dotted = hidden)', fontsize=18)
    plt.tight_layout(rect=(0, 0, 1, 0.97)); plt.savefig(os.path.join(a.out_dir, f'{t}_stages_teacher.png'), dpi=55); plt.close()

    # 3. the learned stage-1 global ellipses
    fig, ax = plt.subplots(figsize=(9, 9 * H / W + 0.8)); ax.imshow(photo); ax.imshow(np.where(mask, np.nan, 0.0), cmap='gray', alpha=0.5, vmin=0, vmax=1)
    cy, cx = np.median(prow), np.median(pcol); R = 0.3 * min(mask.shape); th = np.radians(np.arange(0, 361, 3)); ell = []
    ax.plot(cx + R * np.sin(th), cy + R * np.cos(th), 'w-', lw=1)
    for (nm, p), col in zip([('2D', a.mu_2d)] + [(L['name'], L['mu']) for L in Ls], ['tab:blue', 'tab:red', 'tab:green', 'tab:orange']):
        P = torch.load(p, map_location='cpu')['mu_aniso'][-1].tolist(); m = np.array([mu_dir(P, d) for d in np.degrees(th)])
        ax.plot(cx + R * m * np.sin(th), cy + R * m * np.cos(th), '-', c=col, lw=3, label=f'{nm}: vert {mu_dir(P, 0):.2f}, horiz {mu_dir(P, 90):.2f}')
        ell.append(f'{nm:7s} mu vert {mu_dir(P, 0):.3f} horiz {mu_dir(P, 90):.3f}')
    ax.legend(loc='lower center', fontsize=12); ax.axis('off'); ax.set_title(f'{t}: stage-1 global ellipse (white: mu = 1)', fontsize=15)
    plt.tight_layout(); plt.savefig(os.path.join(a.out_dir, f'{t}_stages_ellipses.png'), dpi=70); plt.close()

    rep = [f'{t}: diameter 2D {diam2:.1f} px'] + [f'{L["name"]}: diameter {L["diam"]:.4f}, extent {L["ext"]:.3f}, components {L["ncomp"]} (largest {L["big"]:.1%}), '
                                                    f'ray misses {L["miss"]:.1%} of the mask' for L in Ls] + ell + rep_lines
    open(os.path.join(a.out_dir, f'{t}_stages.txt'), 'w').write('\n'.join(rep) + '\n'); print('\n'.join(rep)); print('STAGES DONE')


if __name__ == '__main__':
    main()
