"""Clean an existing <tag>_lift.pth with the GLB export's remesh (Tal, 2026-10-28). Run in the Pixal3D env (needs cumesh).
The raw decoded mesh lift.py saves is full of holes and loose pieces (bear 171627: 185 k components, the largest 71.5 % of the vertices,
15 % boundary edges); the GLB we looked at for horse 56069 went through o_voxel.postprocess.to_glb(remesh=True), which rebuilds a
closed surface. Same steps here, geometry only: fill_holes -> narrow-band dual-contouring remesh (band 1, no projection back, as our
--glb call) -> simplify to --target. Then pix_vertex / pix_depth are recomputed on the new mesh with lift.py's splat (same camera, box).
The vertices are already in the world frame (R applied); the decoder's [-0.5, 0.5]^3 box is unchanged by R, so the remesh grid is the same.
Out: <out_dir>/<tag>_lift.pth (same keys + 'remesh' stats) [+ <tag>_lift.ply with --ply].
Usage: cd /workspace/pixal3d_repo && python /workspace/disc/external/pixal3d/remesh_lift.py --lifts <a>_lift.pth ... --out_dir <dir> [--ply]"""
import argparse, os, sys, time
import numpy as np, torch
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lift import splat   # noqa: E402  (also patches Pixal3D's rembg; harmless here)
import cumesh             # noqa: E402


def stats(V, F):
    """components (by vertex), largest share, boundary-edge share."""
    import scipy.sparse as sp, scipy.sparse.csgraph as cg
    F = F.cpu().numpy(); nv = int(V.shape[0])
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1); _, cnt = np.unique(e, axis=0, return_counts=True)
    n, lab = cg.connected_components(sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)), directed=False)
    return {'vertices': nv, 'faces': int(F.shape[0]), 'components': int(n), 'largest': float(np.bincount(lab).max() / nv),
            'boundary_edges': float((cnt == 1).mean())}


def write_ply(path, V, F):
    V = V.cpu().numpy().astype('<f4'); F = F.cpu().numpy().astype('<i4')
    fa = np.empty(len(F), dtype=[('n', 'u1'), ('i', '<i4', 3)]); fa['n'] = 3; fa['i'] = F
    hdr = (f'ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n'
           f'element face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n').encode()
    open(path, 'wb').write(hdr + V.tobytes() + fa.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lifts', nargs='+', required=True); ap.add_argument('--out_dir', required=True)
    ap.add_argument('--target', type=int, default=1000000, help='simplify target (as our --glb call)')
    ap.add_argument('--band', type=float, default=1.0); ap.add_argument('--ply', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    for p in a.lifts:
        t0 = time.time(); tag = os.path.basename(p)[:-len('_lift.pth')]
        L = torch.load(p, map_location='cpu')
        res = int(str(L.get('pipeline_type', '1024_cascade')).split('_')[0])
        V, F = L['vertices'].float().cuda(), L['faces'].int().cuda()
        before = stats(V, F)
        m = cumesh.CuMesh(); m.init(V, F); m.fill_holes(max_hole_perimeter=3e-2); v, f = m.read()
        bvh = cumesh.cuBVH(v, f)
        m.init(*cumesh.remeshing.remesh_narrow_band_dc(v, f, center=torch.zeros(3, device='cuda'), scale=(res + 3 * a.band) / res * 1.0,
                                                       resolution=res, band=a.band, project_back=0, verbose=False, bvh=bvh))
        m.simplify(a.target, verbose=False)
        V2, F2 = m.read(); V2, F2 = V2.float(), F2.long()
        after = stats(V2, F2)
        H, W = L['pix_vertex'].shape; x0, y0, S = L['crop_box']
        pv, zb = splat(V2, L['camera'], (x0, y0, x0 + S, y0 + S), H, W)
        mask = torch.from_numpy(np.array(Image.open(L['image']))[:, :, 3] > 127).cuda()
        cov = pv >= 0; iou = float((cov & mask).sum() / (cov | mask).sum()); coverage = float((cov & mask).sum() / mask.sum())
        out = dict(L); out.update({'vertices': V2.cpu(), 'faces': F2.cpu(), 'pix_vertex': pv.cpu(), 'pix_depth': zb.cpu(), 'iou': iou,
                                   'coverage': coverage, 'remesh': {'from': os.path.abspath(p), 'resolution': res, 'band': a.band,
                                                                    'target': a.target, 'before': before, 'after': after}})
        # legacy format: the DISC env (torch 1.12) cannot read torch 2.6's zip records ("invalid header"), and it builds the tables
        torch.save({k: (v.contiguous().clone() if torch.is_tensor(v) else v) for k, v in out.items()}, os.path.join(a.out_dir, f'{tag}_lift.pth'),
                   _use_new_zipfile_serialization=False)
        if a.ply:
            write_ply(os.path.join(a.out_dir, f'{tag}_lift.ply'), V2, F2)
        print(f'REMESH {tag}: {before["components"]} -> {after["components"]} components, largest {before["largest"]:.3f} -> {after["largest"]:.3f}, '
              f'boundary edges {before["boundary_edges"]:.4f} -> {after["boundary_edges"]:.4f}, {after["vertices"]} vertices, '
              f'IoU {L["iou"]:.3f} -> {iou:.3f} [{time.time() - t0:.0f} s]', flush=True)
    print('REMESH DONE', flush=True)


if __name__ == '__main__':
    main()
