"""Is a pixel -> template mapping mirrored? (Tal, 2026-11-17, bear 6462.) The relational loss only sees distances, which a mirror keeps,
so it cannot tell the two flanks apart; the lift can: it is a 3D surface, and a rotation never turns a left side into a right one.
Per mask pixel: its point on the lift (ray cast, as build_lifted_geodesic_table.py) and its template point (top-1 vertex of the soft
map). Fit the template points to the lift points with a similarity (Procrustes, scale + rotation) twice: as mapped, and with every
template vertex replaced by its mirror (x -> -x). The mapping whose best PROPER rotation fits the lift better has the right handedness;
the other one would need a reflection.
python analysis/chirality_check.py --mask <mask.pth> --features <pix features> --vertex_features <pred_f.pth> --lift <lift.pth>
  --obj_path ./demo/shic/shapes/bear.obj --name shic_bear [--label zs]
"""
import argparse, os, sys
import numpy as np, torch, torch.nn.functional as F
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from analysis.build_lifted_geodesic_table import pix_points
from modules.mapping_loss import soft_map_to_vertices
from modules.utils import device, loadmesh

ap = argparse.ArgumentParser()
for k in ('mask', 'features', 'vertex_features', 'lift', 'obj_path', 'name'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--label', default=''); ap.add_argument('--n', type=int, default=4000)
a = ap.parse_args()

mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape
rr, cc = np.nonzero(mask); sel = np.random.default_rng(0).choice(len(rr), min(a.n, len(rr)), replace=False); rr, cc = rr[sel], cc[sel]
lift = torch.load(a.lift, map_location='cpu'); PP, has = pix_points(lift, H, W)
keep = has[rr, cc]; rr, cc = rr[keep], cc[keep]; Y = PP[rr, cc]                      # lift points of pixels the ray hits
V = loadmesh(dir=a.obj_path, name=a.name, load_rings=False).vertices; Vn = V.cpu().numpy()
mir = cKDTree(Vn).query(Vn * np.array([-1, 1, 1]))[1]
feat = torch.load(a.features, map_location='cpu'); vf = torch.load(a.vertex_features, map_location=device)
with torch.no_grad():
    f = F.normalize(feat[torch.as_tensor(rr), torch.as_tensor(cc)].float().to(device), dim=-1)
    _, ti, _ = soft_map_to_vertices(f, vf, V, 10, return_topk=True, temperature=0.01)
top1 = ti[:, 0].cpu().numpy()

def fit(X, Y):
    """Best similarity Y ~ s R X + t with R a PROPER rotation; returns the RMS residual / the lift's RMS radius, and det of the
    unconstrained (orthogonal) optimum (+1 = a rotation is optimal, -1 = the data wants a reflection)."""
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    U, S, Vt = np.linalg.svd(Yc.T @ Xc); d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1, 1, d]); R = U @ D @ Vt; s = (S * np.diag(D)).sum() / (Xc ** 2).sum()
    res = Yc - s * Xc @ R.T
    return np.sqrt((res ** 2).sum(1).mean()) / np.sqrt((Yc ** 2).sum(1).mean()), d

e0, d0 = fit(Vn[top1], Y); e1, d1 = fit(Vn[mir[top1]], Y)
xs = Vn[top1, 0]; xr = np.ptp(Vn[:, 0])
print(f'{a.label}: {len(rr)} pixels; template side of the mapped pixels: x+ {np.mean(xs > 0.05 * xr):.2f}, x- {np.mean(xs < -0.05 * xr):.2f}')
print(f'{a.label}: as mapped     -> best rotation residual {e0:.3f} (unconstrained optimum det {d0:+.0f})')
print(f'{a.label}: mirrored (x->-x) -> best rotation residual {e1:.3f} (unconstrained optimum det {d1:+.0f})')
print(f'{a.label}: VERDICT: ' + ('as mapped fits the lift better (handedness OK)' if e0 < e1 else 'the MIRRORED mapping fits the lift better: the mapping is flipped'))
