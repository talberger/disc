"""Do the holes of the Pixal3D mesh break the lifted geodesic paths? (Tal, 2026-10-28; bear 171627 = broken mesh, 117682 = control)
One centre pixel + neighbours around it; the lifted geodesic from the centre to each neighbour exactly as the table builder computes it
(analysis/build_lifted_geodesic_table.py: decimate to 200 k faces -> largest connected component -> pixel -> nearest vertex -> edge-graph
Dijkstra), on the RAW mesh and on the REMESHED one (external/pixal3d/remesh_lift.py). Per pair: geodesic, straight 3D distance and their
ratio (detour; a path that has to go around a hole or that starts on a loose piece snapped elsewhere shows a large detour), and how far the
pixel's own vertex had to snap to reach the largest component.
Out (--out_dir): <tag>_probe.png (photo + projected paths raw | remeshed, side views, table) and, for MeshLab, <tag>_probe_{raw,remesh}.ply:
the decimated mesh, grey = largest component, red = everything the table drops; the paths as coloured vertices.
Usage: python analysis/geodesic_holes_probe.py --lift_raw <lift.pth> --lift_remesh <lift.pth> --img_path <png> --mask_path <pth> --tag lvis171627 --out_dir <dir>
"""
import argparse, math, os, sys
import numpy as np, torch, scipy.ndimage, scipy.sparse.csgraph
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph
from plot_lifted_geodesic_paths import project, path_from_pred

COLS = [(230, 25, 75), (60, 180, 75), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230), (210, 245, 60)]


def pick_points(mask, n):
    """centre = the mask pixel deepest inside (distance transform max); neighbours on a ring at 1/3 of the mask's extent."""
    dt = scipy.ndimage.distance_transform_edt(mask); c = np.unravel_index(np.argmax(dt), mask.shape)
    rows, cols = np.nonzero(mask); rad = 0.33 * max(np.ptp(rows), np.ptp(cols))
    nbs = []
    for k in range(n):
        th = 2 * math.pi * k / n
        for s in np.linspace(1.0, 0.3, 15):                      # pull in until the point is inside the mask
            r, cc = int(c[0] + s * rad * math.sin(th)), int(c[1] + s * rad * math.cos(th))
            if 0 <= r < mask.shape[0] and 0 <= cc < mask.shape[1] and mask[r, cc]:
                nbs.append((r, cc)); break
    return (int(c[0]), int(c[1])), nbs


def probe(lift, target_faces, C, nbs):
    pv = lift['pix_vertex'].numpy(); has = pv >= 0
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~has, return_indices=True); pv = pv[ir, ic]
    V0 = lift['vertices'].numpy(); V, F = decimate(V0, lift['faces'].numpy(), target_faces)
    G = edge_graph(V, F); ncomp, lab = scipy.sparse.csgraph.connected_components(G, directed=False)
    big = np.bincount(lab).argmax(); keep = np.nonzero(lab == big)[0]; tree = cKDTree(V[keep])
    def vtx(rc):
        d, j = tree.query(V0[pv[rc]]); return int(keep[j]), float(d)
    cv, _ = vtx(C)
    D, P = scipy.sparse.csgraph.dijkstra(G, directed=False, indices=cv, return_predecessors=True)
    ext = float(np.ptp(V[keep], 0).max()); res = []
    for N in nbs:
        t, snap = vtx(N); path = path_from_pred(P, t)
        res.append(dict(geo=float(D[t]), euc=float(np.linalg.norm(V[t] - V[cv])), snap=snap / ext, path=path))
    return V, F, lab == big, ncomp, res, ext


def write_ply(path, V, F, vcol):
    V = V.astype('<f4'); F = F.astype('<i4')
    vt = np.empty(len(V), dtype=[('p', '<f4', 3), ('c', 'u1', 3)]); vt['p'] = V; vt['c'] = vcol
    fa = np.empty(len(F), dtype=[('n', 'u1'), ('i', '<i4', 3)]); fa['n'] = 3; fa['i'] = F
    hdr = (f'ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n'
           f'property uchar red\nproperty uchar green\nproperty uchar blue\nelement face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n')
    open(path, 'wb').write(hdr.encode() + vt.tobytes() + fa.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lift_raw', required=True); ap.add_argument('--lift_remesh', required=True)
    ap.add_argument('--img_path', required=True); ap.add_argument('--mask_path', required=True)
    ap.add_argument('--tag', required=True); ap.add_argument('--out_dir', required=True)
    ap.add_argument('--n_nb', type=int, default=8); ap.add_argument('--target_faces', type=int, default=200000)
    ap.add_argument('--centre', type=int, nargs=2, default=None)
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    photo = np.array(Image.open(a.img_path).convert('RGB')); mask = torch.load(a.mask_path).numpy().astype(bool)
    C, nbs = pick_points(mask, a.n_nb)
    if a.centre:
        C = tuple(a.centre)
    fig, ax = plt.subplots(2, 3, figsize=(20, 13), gridspec_kw={'width_ratios': [1, 1, 1.1]})
    lines = [f'{a.tag}: centre {C}', f'{"nb":3s} {"geo/euc raw":>12s} {"geo/euc remesh":>15s} {"snap raw":>9s} {"snap rm":>8s}']
    out = {}
    for j, (name, p) in enumerate([('raw', a.lift_raw), ('remesh', a.lift_remesh)]):
        lift = torch.load(p, map_location='cpu'); cam, box = lift['camera'], lift['crop_box']
        V, F, big, ncomp, res, ext = probe(lift, a.target_faces, C, nbs); out[name] = res
        ax[j, 0].imshow(photo); ax[j, 0].axis('off')
        ax[j, 0].set_title(f'{name}: {ncomp} components, the largest has {big.mean():.1%} of the vertices')
        sub = np.random.RandomState(0).choice(len(V), min(40000, len(V)), replace=False)
        ax[j, 1].scatter(V[sub, 1], V[sub, 2], s=0.2, c=np.where(big[sub], '0.75', 'red')); ax[j, 1].set_aspect('equal'); ax[j, 1].axis('off')
        ax[j, 1].set_title(f'{name}, from the side (red = dropped by the table)')
        vcol = np.where(big[:, None], 170, np.array([220, 40, 40])).astype(np.uint8)
        for k, (N, r) in enumerate(zip(nbs, res)):
            col = np.array(COLS[k % len(COLS)]) / 255
            rr, cc, _ = project(V[r['path']], cam, box); ax[j, 0].plot(cc, rr, '-', c=col, lw=2.5)
            ax[j, 1].plot(V[r['path'], 1], V[r['path'], 2], '-', c=col, lw=2)
            ax[j, 0].plot(N[1], N[0], 'o', ms=9, mfc=col, mec='k')
            vcol[r['path']] = COLS[k % len(COLS)]
        ax[j, 0].plot(C[1], C[0], 'w*', ms=20, mec='k')
        write_ply(os.path.join(a.out_dir, f'{a.tag}_probe_{name}.ply'), V, F, vcol)
    for k in range(len(nbs)):
        r0, r1 = out['raw'][k], out['remesh'][k]
        lines.append(f'{k + 1:<3d} {r0["geo"] / max(r0["euc"], 1e-9):12.2f} {r1["geo"] / max(r1["euc"], 1e-9):15.2f} {r0["snap"]:9.3f} {r1["snap"]:8.3f}')
    lines += ['', 'geo/euc = path length / straight 3D distance (1 = straight;', '  a detour around a hole -> much larger)',
              'snap = how far the pixel\'s vertex moved to reach', '  the largest component (/ mesh extent)']
    for j in (0, 1):
        ax[j, 2].axis('off')
    ax[0, 2].text(0, 1, '\n'.join(lines), va='top', family='monospace', fontsize=12)
    for k, N in enumerate(nbs):
        ax[1, 2].plot([], [], 'o', c=np.array(COLS[k % len(COLS)]) / 255, label=f'neighbour {k + 1}')
    ax[1, 2].legend(loc='upper left', fontsize=12)
    plt.tight_layout(); plt.savefig(os.path.join(a.out_dir, f'{a.tag}_probe.png'), dpi=75)
    print('\n'.join(lines)); print('saved', a.out_dir)


if __name__ == '__main__':
    main()
