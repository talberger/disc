"""LIFTED 2D geodesic table (Pixal3D direction, Tal + Itai 2026-10-25): the pixel-to-pixel distances of rkd_spatial measured as geodesics
on a 3D mesh lifted from the photo (external/pixal3d/lift.py), instead of 2D geodesics inside the mask.

Takes an EXISTING 2D table of the same instance (analysis/build_geodesic_tables.py: same mask, same 2048 centres, same seed) and replaces only
its distances, so the file is a drop-in --geo_table_2d_path: coords / pixel_to_node / geodesic_safe_mask / object_mask_path / seed are copied
unchanged and train_relational_loss.py's consistency checks pass as before. Feed the printed lifted diameter as --geo_diag_2d.

Steps: lifted mesh (Pixal3D: ~2-3 M vertices) -> quadric decimation to --target_faces -> largest connected component -> every mask pixel gets
the decimated vertex nearest (in 3D) to its front-most lifted vertex (pixels with no surface point: the nearest pixel that has one) ->
Dijkstra on the decimated mesh's EDGE graph (edge length = Euclidean; overestimates the true surface geodesic by a roughly uniform factor,
which the diameter normalisation cancels to first order) from every centre's vertex -> table[i, n] = d(centre_i, pixel n).
Diameter = double sweep over the vertices of the mask pixels (visible-to-visible, like true_diameter_2d).

Run in the disc env (Run:ai tberger3-disc-gpu2 or a pod), e.g.
  python analysis/build_lifted_geodesic_table.py --lift_path <tag>_lift.pth --table_2d <..._mask_geo_table_2d_seed0.pth> \\
      --out_path <dir>/<tag>_mask_geo_table_lifted_seed0.pth [--gt_path <tag>_gt.pth --check_png <png>]
"""
import argparse, json, os, sys, time
import numpy as np
import scipy.ndimage
import scipy.sparse
import scipy.sparse.csgraph
import torch
from scipy.spatial import cKDTree


def decimate(V, F, target_faces):
    import open3d as o3d
    m = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(V.astype(np.float64)), o3d.utility.Vector3iVector(F.astype(np.int32)))
    m.remove_duplicated_vertices(); m.remove_degenerate_triangles()
    if len(m.triangles) > target_faces:
        m = m.simplify_quadric_decimation(target_faces)
    m.remove_unreferenced_vertices()
    return np.asarray(m.vertices), np.asarray(m.triangles)


def edge_graph(V, F):
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e = np.unique(np.sort(e, 1), axis=0)
    w = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    n = len(V)
    return scipy.sparse.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lift_path', required=True); ap.add_argument('--table_2d', required=True); ap.add_argument('--out_path', required=True)
    ap.add_argument('--target_faces', type=int, default=200000, help='decimated mesh size (~100 k vertices)')
    ap.add_argument('--gt_path', default=None, help='for the check figure: rows from the centres nearest the GT points')
    ap.add_argument('--check_png', default=None)
    a = ap.parse_args()
    t0 = time.time()
    lift = torch.load(a.lift_path, map_location='cpu')
    t2 = torch.load(a.table_2d, map_location='cpu')
    safe = t2['geodesic_safe_mask'].numpy().astype(bool)
    p2n = t2['pixel_to_node'].numpy() if torch.is_tensor(t2['pixel_to_node']) else np.asarray(t2['pixel_to_node'])
    coords = t2['coords'].numpy() if torch.is_tensor(t2['coords']) else np.asarray(t2['coords'])
    H, W = safe.shape
    pv = lift['pix_vertex'].numpy()
    assert pv.shape == (H, W), (pv.shape, safe.shape)

    # every safe-mask pixel -> a lifted vertex (pixels with no surface point borrow the nearest pixel that has one)
    has = pv >= 0
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~has, return_indices=True)
    pv_full = pv[ir, ic]
    print(f'[lifted] mask pixels {int(safe.sum())}, without a surface point {int((safe & ~has).sum())} (filled from the nearest one)', flush=True)

    V0, F0 = lift['vertices'].numpy(), lift['faces'].numpy()
    V, F = decimate(V0, F0, a.target_faces)
    G = edge_graph(V, F)
    ncomp, lab = scipy.sparse.csgraph.connected_components(G, directed=False)
    big = np.bincount(lab).argmax()
    keep = np.nonzero(lab == big)[0]
    print(f'[lifted] decimated {len(V0)} -> {len(V)} vertices, {len(F)} faces; {ncomp} components, largest {len(keep)} vertices '
          f'[{time.time() - t0:.0f} s]', flush=True)
    tree = cKDTree(V[keep])

    rows, cols = np.nonzero(safe)
    nodes = p2n[rows, cols]
    assert (nodes >= 0).all() and len(np.unique(nodes)) == len(nodes)
    pix_v = np.empty(len(rows), np.int64)
    _, nn = tree.query(V0[pv_full[rows, cols]]); pix_v[nodes] = keep[nn]          # column n -> decimated vertex
    _, cn = tree.query(V0[pv_full[coords[:, 0], coords[:, 1]]]); cen_v = keep[cn]  # centre i -> decimated vertex
    snap = np.linalg.norm(V0[pv_full[rows, cols]] - V[pix_v[nodes]], axis=1)
    print(f'[lifted] pixel -> decimated vertex snap distance: median {np.median(snap):.4f}, max {snap.max():.4f} (mesh extent '
          f'{np.ptp(V, 0).max():.3f})', flush=True)

    uc, inv = np.unique(cen_v, return_inverse=True)
    D = scipy.sparse.csgraph.dijkstra(G, directed=False, indices=uc)            # [unique centres, V]
    table = torch.from_numpy(D[inv][:, pix_v].astype(np.float32))               # [2048, M]
    assert torch.isfinite(table).all(), 'a pixel landed off the largest component'
    print(f'[lifted] table {tuple(table.shape)} from {len(uc)} unique centre vertices [{time.time() - t0:.0f} s]', flush=True)

    # diameter between mask-pixel vertices (double sweep, as true_diameter_2d does over visible pixels)
    pset = np.unique(pix_v); src = pset[0]; diam = 0.0
    for _ in range(4):
        d = scipy.sparse.csgraph.dijkstra(G, directed=False, indices=src)[pset]
        far = pset[int(np.argmax(d))]
        if d.max() <= diam + 1e-9:
            break
        diam, src = float(d.max()), far
    print(f'[lifted] diameter (visible-to-visible, double sweep) {diam:.5f}; 2D table diameter {t2.get("true_diameter_2d")}', flush=True)

    out = dict(t2)
    out.update({'table': table, 'diagonal': float(table.max()), 'true_diameter_2d': diam,
                'lifted': {'lift_path': os.path.abspath(a.lift_path), 'table_2d': os.path.abspath(a.table_2d),
                           'target_faces': a.target_faces, 'decimated_vertices': int(len(V)), 'largest_component_vertices': int(len(keep)),
                           'graph': 'edge-graph Dijkstra on the decimated lifted mesh'}})
    torch.save(out, a.out_path)
    meta = os.path.splitext(a.out_path)[0] + '_meta.json'
    json.dump({'diagonal': float(table.max()), 'true_diameter_2d': diam, 'num_centers': int(table.shape[0]),
               'num_mask_pixels': int(table.shape[1]), 'table_path': a.out_path, 'lifted_from': os.path.abspath(a.lift_path)},
              open(meta, 'w'), indent=1)
    print(f'[lifted] saved {a.out_path} (+ {os.path.basename(meta)}) [{time.time() - t0:.0f} s]', flush=True)

    if a.check_png:
        # rows of both tables from the centres nearest a few pixels (GT points if given), each normalised by its own diameter
        from PIL import Image
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        if a.gt_path:
            gt = torch.load(a.gt_path, map_location='cpu')
            pts = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
        else:
            pts = [tuple(coords[i]) for i in np.linspace(0, len(coords) - 1, 3).astype(int)]
        d2 = float(t2.get('true_diameter_2d') or t2['diagonal'])
        fig, ax = plt.subplots(2, len(pts), figsize=(3.2 * len(pts), 6.4))
        ax = np.atleast_2d(ax).reshape(2, len(pts))
        for k, (r, c) in enumerate(pts):
            i = int(np.argmin((coords[:, 0] - r) ** 2 + (coords[:, 1] - c) ** 2))
            for j, (tab, dd, name) in enumerate([(t2['table'], d2, '2D'), (table, diam, 'lifted 3D')]):
                img = np.full((H, W), np.nan); img[rows, cols] = tab[i].numpy()[nodes] / dd
                ax[j, k].imshow(img, cmap='turbo', vmin=0, vmax=1); ax[j, k].plot(coords[i, 1], coords[i, 0], 'w*', ms=12)
                ax[j, k].set_title(f'{name}: from pt {k + 1}'); ax[j, k].axis('off')
        plt.tight_layout(); plt.savefig(a.check_png, dpi=90)
        print(f'[lifted] check figure {a.check_png}', flush=True)


if __name__ == '__main__':
    main()
