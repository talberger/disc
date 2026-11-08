"""Lifted geodesic path between two mask pixels, as PLYs for MeshLab (Tal, 2026-11-08; 171627 rep 3 -> x3: 16 px apart, both on the
front, yet 0.758 of the diameter on the mesh). Same chain as build_lifted_geodesic_table.py (decimate -> largest component -> pixel -> vertex).
Out (--out_dir):
  <tag>_mesh_dist.ply  the decimated mesh the Dijkstra runs on, coloured by the lifted distance from pixel A (turbo, / diameter)
  <tag>_path.ply       the path A -> B as a chain of small spheres (black)
  <tag>_points.ply     A (green) and B (red) as big spheres
Usage (disc env, needs open3d):
  python analysis/export_lifted_path_ply.py --tag lvis171627 --src_dir <runs_full_poly/lvis171627> --lift_path <..._full_lift.pth> \\
      --lifted_meta <..._lifted_seed0_full_meta.json> --a 258 130 --b 242 129 --out_dir <dir>
"""
import argparse, json, os, sys
import numpy as np, torch, scipy.ndimage, scipy.sparse.csgraph
import open3d as o3d
from scipy.spatial import cKDTree
import matplotlib.cm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lifted_geodesic_table import decimate, edge_graph
from plot_lifted_geodesic_paths import path_from_pred


def spheres(P, r, rgb):
    out = o3d.geometry.TriangleMesh()
    for p in P:
        s = o3d.geometry.TriangleMesh.create_sphere(radius=r, resolution=8); s.translate(p); out += s
    out.paint_uniform_color(rgb); return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True); ap.add_argument('--src_dir', required=True); ap.add_argument('--lift_path', required=True)
    ap.add_argument('--lifted_meta', required=True); ap.add_argument('--a', type=int, nargs=2, required=True)
    ap.add_argument('--b', type=int, nargs=2, required=True); ap.add_argument('--out_dir', required=True)
    ap.add_argument('--target_faces', type=int, default=200000)
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True); t = a.tag
    diam3 = json.load(open(a.lifted_meta))['true_diameter_2d']
    lift = torch.load(a.lift_path, map_location='cpu')
    pv = lift['pix_vertex'].numpy()
    _, (ir, ic) = scipy.ndimage.distance_transform_edt(~(pv >= 0), return_indices=True); pv = pv[ir, ic]
    V0 = lift['vertices'].numpy(); V, F = decimate(V0, lift['faces'].numpy(), a.target_faces)
    G3 = edge_graph(V, F); _, lab = scipy.sparse.csgraph.connected_components(G3, directed=False)
    keep = np.nonzero(lab == np.bincount(lab).argmax())[0]; tree = cKDTree(V[keep])
    va, vb = (int(keep[tree.query(V0[pv[r, c]])[1]]) for r, c in (a.a, a.b))
    D, P = scipy.sparse.csgraph.dijkstra(G3, directed=False, indices=va, return_predecessors=True)
    path = path_from_pred(P, vb); ext = float(np.ptp(V, 0).max())
    d = D / diam3; col = matplotlib.cm.turbo(np.clip(np.nan_to_num(d, posinf=1.0), 0, 1))[:, :3]
    col[~np.isfinite(D)] = 0.5                                           # not in the kept component: grey
    m = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(V), o3d.utility.Vector3iVector(F))
    m.vertex_colors = o3d.utility.Vector3dVector(col); m.compute_vertex_normals()
    o3d.io.write_triangle_mesh(f'{a.out_dir}/{t}_mesh_dist.ply', m)
    seg = np.concatenate([np.linspace(V[p], V[q], 4, endpoint=False) for p, q in zip(path[:-1], path[1:])] + [V[path[-1:]]])
    o3d.io.write_triangle_mesh(f'{a.out_dir}/{t}_path.ply', spheres(seg, 0.003 * ext, [0, 0, 0]))
    o3d.io.write_triangle_mesh(f'{a.out_dir}/{t}_points.ply', spheres(V[[va]], 0.012 * ext, [0, 0.8, 0]) + spheres(V[[vb]], 0.012 * ext, [0.9, 0, 0]))
    print(f'A {tuple(a.a)} -> vertex {va}, B {tuple(a.b)} -> vertex {vb}: 3D straight {np.linalg.norm(V[va] - V[vb]):.4f}, '
          f'path {D[vb]:.4f} = {D[vb] / diam3:.3f} of the diameter, {len(path)} vertices; mesh extent {ext:.3f}')
    print('saved', a.out_dir)


if __name__ == '__main__':
    main()
