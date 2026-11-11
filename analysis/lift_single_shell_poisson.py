"""ONE closed shell for a lifted mesh, by Poisson reconstruction (Tal, 2026-11-11: "a single full shell and that's it"; lvis151955).
remesh_lift.py's mesh is a thin DOUBLE shell (outer + inner skin joined at the rims of the openings, analysis/lifted_sheet_check.py). Here:
  1. outer skin = the faces the open sky sees: from each face centre, --k rays over the hemisphere of its normal; kept if > --vis escape
     (the inner skin faces the cavity and sees the sky only through an opening);
  2. screened Poisson (open3d, --depth) on points + normals sampled from the outer skin -> one closed surface, the openings capped;
  3. checks: watertight, components, wall thickness behind the first hit (rays along +y, the camera axis), distance outer skin -> new surface.
Only the mesh (no table, no training). Figure: before | after, 3 shaded views + a vertical cross-section.
  python analysis/lift_single_shell_poisson.py --mesh <lift.ply> --out_ply <ply> --out_png <png>
--lift_path <..._lift.pth> --out_lift <..._poisson_lift.pth>: the same on a lift file (lift.py / remesh_lift.py); the output is that lift with
its vertices / faces replaced (camera, crop box unchanged), a drop-in --lift_path of build_lifted_geodesic_table.py's ray-cast mappings.
"""
import argparse
import numpy as np


def scene_of(V, F):
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(V.astype(np.float32), F.astype(np.uint32)); return sc


def cast(sc, o, d):
    import open3d as o3d
    r = sc.cast_rays(o3d.core.Tensor(np.c_[o, d].astype(np.float32)))
    return r['t_hit'].numpy().astype(np.float64), r['primitive_normals'].numpy()


def face_frame(V, F):
    c = V[F].mean(1); n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); a = np.linalg.norm(n, axis=1, keepdims=True)
    return c, n / np.maximum(a, 1e-20), a[:, 0] / 2


def sky_visibility(V, F, k, rng):
    """Fraction of k hemisphere rays (around the face normal) that leave the mesh, per face."""
    c, n, _ = face_frame(V, F); sc = scene_of(V, F); eps = 1e-4 * np.ptp(V, 0).max(); vis = np.zeros(len(F))
    for _ in range(k):
        d = rng.normal(size=n.shape); d /= np.linalg.norm(d, axis=1, keepdims=True); d *= np.sign((d * n).sum(1, keepdims=True))
        vis += ~np.isfinite(cast(sc, c + eps * n, d)[0])
    return vis / k


def thickness(V, F, n_rays=200000, rng=None):
    """Next surface behind the first hit / extent, for rays along +y (the camera axis) over the x-z bounding box."""
    lo, hi = V.min(0), V.max(0); ext = (hi - lo).max(); sc = scene_of(V, F)
    o = np.c_[rng.uniform(lo[0], hi[0], n_rays), np.full(n_rays, lo[1] - ext), rng.uniform(lo[2], hi[2], n_rays)]; d = np.tile([0.0, 1, 0], (n_rays, 1))
    t = cast(sc, o, d)[0]; ok = np.isfinite(t); t2 = cast(sc, o[ok] + (t[ok, None] + 1e-4 * ext) * d[ok], d[ok])[0] / ext
    return t2


def shade(V, F, axis, sign, res=420):
    """Orthographic shaded view looking along sign * axis; image axes = the two other world axes."""
    lo, hi = V.min(0), V.max(0); ext = (hi - lo).max(); c = (lo + hi) / 2; u, v = [a for a in range(3) if a != axis]
    g = (np.arange(res) + 0.5) / res - 0.5; gu, gv = np.meshgrid(g * ext * 1.05, -g * ext * 1.05)
    o = np.zeros((res * res, 3)); o[:, u] = c[u] + gu.ravel() * (sign if axis == 1 else 1); o[:, v] = c[v] + gv.ravel(); o[:, axis] = c[axis] - sign * 2 * ext
    d = np.zeros_like(o); d[:, axis] = sign; t, n = cast(scene_of(V, F), o, d)
    return np.where(np.isfinite(t), 0.25 + 0.75 * np.abs(n[:, axis]), np.nan).reshape(res, res)


def section(V, F, axis, val):
    """Segments of the mesh on the plane {axis = val}: [n, 2, 3]."""
    s = V[F][:, :, axis] - val; cross = (s.min(1) < 0) & (s.max(1) > 0); T, s = V[F][cross], s[cross]; out = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        m = s[:, a] * s[:, b] < 0; w = (s[:, a] / (s[:, a] - s[:, b]))[:, None]
        out.append(np.where(m[:, None], T[:, a] + w * (T[:, b] - T[:, a]), np.nan))
    P = np.stack(out, 1); order = np.argsort(np.isnan(P[:, :, 0]), axis=1, kind='stable')[:, :2]
    return P[np.arange(len(P))[:, None], order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mesh'); ap.add_argument('--lift_path'); ap.add_argument('--out_lift'); ap.add_argument('--out_ply'); ap.add_argument('--out_png')
    ap.add_argument('--k', type=int, default=64); ap.add_argument('--vis', type=float, default=0.2, help='outer skin = sky visibility above this')
    ap.add_argument('--depth', type=int, default=9); ap.add_argument('--n_points', type=int, default=500000); ap.add_argument('--title', default='')
    a = ap.parse_args()
    import open3d as o3d, scipy.sparse, scipy.sparse.csgraph
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(0)
    if a.lift_path:
        import torch
        lift = torch.load(a.lift_path, map_location='cpu'); V, F = lift['vertices'].numpy().astype(np.float64), lift['faces'].numpy()
    else:
        m = o3d.io.read_triangle_mesh(a.mesh); V, F = np.asarray(m.vertices), np.asarray(m.triangles)
    ext = np.ptp(V, 0).max()
    vis = sky_visibility(V, F, a.k, rng); _, _, area = face_frame(V, F); keep = vis > a.vis
    print(f'input: {len(V)} vertices, {len(F)} faces | sky visibility of the faces (area weighted): ' +
          ' '.join(f'{lo:.1f}-{lo + 0.1:.1f}: {100 * area[(vis >= lo) & (vis < lo + 0.1 + 1e-9 * (lo > 0.85))].sum() / area.sum():.0f}%' for lo in np.arange(0, 1, 0.1)))
    print(f'outer skin (visibility > {a.vis}): {100 * area[keep].sum() / area.sum():.1f}% of the area')

    outer = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(V), o3d.utility.Vector3iVector(F[keep])); outer.compute_triangle_normals()
    pcd = outer.sample_points_uniformly(a.n_points, use_triangle_normal=True)
    pm, dens = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=a.depth, scale=1.1, linear_fit=False, n_threads=1)
    pm.remove_degenerate_triangles(); pm.remove_unreferenced_vertices()
    lab, cnt, _ = pm.cluster_connected_triangles(); lab = np.asarray(lab); pm.remove_triangles_by_mask(lab != np.argmax(cnt)); pm.remove_unreferenced_vertices()
    V2, F2 = np.asarray(pm.vertices), np.asarray(pm.triangles)
    P = np.asarray(pcd.points); q = pm.sample_points_uniformly(1000000); d_in = cKDTree(np.asarray(q.points)).query(P)[0] / ext
    d_out = cKDTree(P).query(np.asarray(q.points))[0] / ext
    print(f'poisson (depth {a.depth}): {len(V2)} vertices, {len(F2)} faces, {len(cnt)} components (largest kept), watertight {pm.is_watertight()}')
    print(f'outer skin -> new surface (/ extent): mean {d_in.mean():.4f}, 95% {np.percentile(d_in, 95):.4f}, max {d_in.max():.4f}')
    print(f'new surface -> outer skin (/ extent): mean {d_out.mean():.4f}, 95% {np.percentile(d_out, 95):.4f}; > 0.02 (= invented surface, the caps): '
          f'{100 * (d_out > 0.02).mean():.1f}% of the new area')
    for nm, (v, f) in (('input', (V, F)), ('poisson', (V2, F2))):
        t2 = thickness(v, f, rng=rng)
        print(f'{nm}: next surface behind the first hit (/ extent): median {np.median(t2):.4f}; < 0.01: {100 * (t2 < 0.01).mean():.1f}% < 0.03: {100 * (t2 < 0.03).mean():.1f}%')
    pm.vertex_colors = o3d.utility.Vector3dVector()   # open3d fills them with black (MeshLab then shows a black mesh)
    if a.out_ply: pm.compute_vertex_normals(); o3d.io.write_triangle_mesh(a.out_ply, pm)
    if a.out_lift:   # pix_vertex / pix_depth (lift.py's splat) still index the OLD mesh: only their shape is used by the ray-cast mappings
        torch.save({**lift, 'vertices': torch.from_numpy(V2).to(lift['vertices'].dtype), 'faces': torch.from_numpy(F2).to(lift['faces'].dtype),
                    'single_shell': f'poisson depth {a.depth}, outer skin = sky visibility > {a.vis}'}, a.out_lift)
    if not a.out_png: return

    views = (('front (the camera)', 1, 1), ('back', 1, -1), ('from below', 2, 1))
    fig, axs = plt.subplots(2, 4, figsize=(22, 11.5))
    for row, (nm, v, f) in enumerate((('before: remesh (double shell)', V, F), ('after: Poisson (one closed shell)', V2, F2))):
        for ax, (vn, axis, sign) in zip(axs[row], views):
            ax.imshow(shade(v, f, axis, sign), cmap='gray', vmin=0, vmax=1); ax.set_title(f'{nm}\n{vn}', fontsize=14); ax.axis('off')
        S = section(v, f, 0, np.median(V[:, 0])); ax = axs[row, 3]
        ax.plot(S[:, :, 1].T, S[:, :, 2].T, '-', c='k', lw=0.8); ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(f'{nm}\nvertical cross-section (x = median), camera on the left', fontsize=14)
    for ax in axs[:, 3]: ax.set_xlim(V[:, 1].min() - 0.05 * ext, V[:, 1].max() + 0.05 * ext); ax.set_ylim(V[:, 2].min() - 0.05 * ext, V[:, 2].max() + 0.05 * ext)
    fig.suptitle(f'{a.title}: lifted mesh before / after Poisson reconstruction of its outer skin', fontsize=17)
    plt.tight_layout(rect=(0, 0, 1, 0.95)); plt.savefig(a.out_png, dpi=70)


if __name__ == '__main__':
    main()
