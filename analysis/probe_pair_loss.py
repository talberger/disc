"""What the stage-1 loss says about chosen pixel pairs, step by step (Tal, 2026-11-17: horse 147192, why the two hind legs
do not separate). Reads a stage-1 run trained WITHOUT --no_step_checkpoints (each encoder_checkpoint_step<k>.pth carries its
global ellipse) and, at step 0 (phase 1 = zero-shot) and every checkpoint, recomputes exactly what rkd_spatial_dist_loss
sees for each pair (rep, other):
  teacher  d_2D / D2   lifted geodesic (edge-graph Dijkstra on the decimated lift, triangle ray-cast pixel -> vertex,
                       as build_lifted_geodesic_table.py --pix_map triangle) over the run's --geo_diag_2d
  student  d_3D / D3 / s   expected template geodesic between the two pixels' top-K soft vertices, over the template
                       diameter, over the global ellipse's scale in the pair's image direction
Also for two image regions (--region NAME=r0:r1:c0:c1[+r0:r1:c0:c1...], intersected with the mask): the mean student and
teacher over sampled pairs inside each region and across the two, and where each region's pixels land on the template legs
(legs = the 4 components under the highest height cut that gives 4, as analysis/leg_colorings.py). The geodesic paths
(lift: rep -> each other pixel; template: rep's top-1 vertex -> each other's, at step 0 and the last step) go to the json
for the figure.

python analysis/probe_pair_loss.py --run_dir <phase2 out dir> --phase1_dir <P1> --obj_path ./demo/shic/shapes/horse.obj
  --name shic_horse --features <pix features .pth> --mask <mask.pth> --lift <lift.pth> --geo_table_3d <GEO3D> --geo_diag_2d <DL>
  --pixel rep=200,38 --pixel same=235,30 --pixel other=205,62 --region near=185:215:31:45+215:245:22:40
  --region far=185:248:54:84 --out_json probe.json
"""
import argparse, glob, json, os, re, sys
import numpy as np, scipy.sparse, scipy.sparse.csgraph, torch
import torch.nn.functional as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from analysis.build_lifted_geodesic_table import decimate, edge_graph, raycast_pix_vertex
from analysis.verify_encoder_resume import seed_everything
from modules.encoder_l2norm import EncoderL2Norm
from modules.mapping_loss import soft_map_to_vertices
from modules.relational_loss import expected_geodesic_distance_3d
from modules.utils import device, load_state_dict, loadmesh
from phase2.train_mapping_loss import set_fourier_basis
from phase2.train_relational_loss import aniso_scale_from_params

ap = argparse.ArgumentParser()
for k in ('run_dir', 'phase1_dir', 'obj_path', 'name', 'features', 'mask', 'lift', 'geo_table_3d', 'out_json'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--geo_diag_2d', type=float, required=True)
ap.add_argument('--pixel', action='append', required=True, help='NAME=row,col; the first one is the representative')
ap.add_argument('--region', action='append', default=[], help='NAME=r0:r1:c0:c1[+...] (exactly two, or none)')
ap.add_argument('--n_region', type=int, default=150, help='sampled pixels per region')
ap.add_argument('--k', type=int, default=10); ap.add_argument('--temperature', type=float, default=0.01)
ap.add_argument('--seed', type=int, default=0)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)

mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape
pix = {n: tuple(int(x) for x in v.split(',')) for n, v in (p.split('=') for p in a.pixel)}
names = list(pix); rep = names[0]
for n, (r, c) in pix.items():
    assert mask[r, c], f'{n} {r},{c} is off the mask'
regions = {}
for spec in a.region:
    n, boxes = spec.split('=')
    m = np.zeros_like(mask)
    for b in boxes.split('+'):
        r0, r1, c0, c1 = map(int, b.split(':')); m[r0:r1, c0:c1] = True
    rc = np.argwhere(m & mask); regions[n] = rc[rng.choice(len(rc), min(a.n_region, len(rc)), replace=False)]
    print(f'region {n}: {int((m & mask).sum())} mask pixels, {len(regions[n])} sampled')

# ---- teacher: lifted geodesics, as build_lifted_geodesic_table.py --pix_map triangle
lift = torch.load(a.lift, map_location='cpu')
V, Fc = decimate(lift['vertices'].numpy(), lift['faces'].numpy(), 200000)
G = edge_graph(V, Fc); _, lab = scipy.sparse.csgraph.connected_components(G, directed=False); big = np.bincount(lab).argmax()
pv, _ = raycast_pix_vertex(lift, V, Fc[lab[Fc[:, 0]] == big], H, W)
src = pv[pix[rep]]
dl, pred = scipy.sparse.csgraph.dijkstra(G, directed=False, indices=src, return_predecessors=True)
def path(pred, s, t):
    out = [t]
    while out[-1] != s and out[-1] >= 0:
        out.append(pred[out[-1]])
    return out[::-1]
res = {'pixels': pix, 'geo_diag_2d': a.geo_diag_2d, 'teacher': {}, 'lift_path': {}, 'steps': [], 'pairs': {}, 'regions': {}}
for n in names[1:]:
    res['teacher'][n] = float(dl[pv[pix[n]]] / a.geo_diag_2d)
    res['lift_path'][n] = V[path(pred, src, pv[pix[n]])].tolist()
print('teacher d_2D / D2:', {n: round(v, 3) for n, v in res['teacher'].items()})
# region teacher: Dijkstra from 30 pixels of each region to all sampled pixels of both regions
rn = list(regions)
if rn:
    assert len(rn) == 2, 'two regions'
    allr = np.concatenate([regions[rn[0]], regions[rn[1]]]); split = len(regions[rn[0]])
    srcs = np.r_[np.arange(30), split + np.arange(30)]
    Dr = scipy.sparse.csgraph.dijkstra(G, directed=False, indices=pv[allr[srcs, 0], allr[srcs, 1]])[:, pv[allr[:, 0], allr[:, 1]]] / a.geo_diag_2d

# ---- student
mesh = loadmesh(dir=a.obj_path, name=a.name, load_rings=False)
verts = mesh.vertices; VT = verts.cpu().numpy(); FT = mesh.faces.cpu().numpy()
g3 = torch.load(a.geo_table_3d, map_location='cpu'); T3, D3 = g3['table'].to(device), float(g3['diagonal'])
GT = edge_graph(VT, FT)
E_ = np.vstack([FT[:, [0, 1]], FT[:, [1, 2]], FT[:, [2, 0]]])
for cut in np.arange(0.0, -0.4, -0.005):                 # the 4 template legs (analysis/leg_colorings.py)
    keep = VT[:, 1] < cut; e = E_[keep[E_[:, 0]] & keep[E_[:, 1]]]
    _, ll = scipy.sparse.csgraph.connected_components(scipy.sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(VT),) * 2), directed=False)
    ll = np.where(keep, ll, -1); ids, cnt = np.unique(ll[ll >= 0], return_counts=True)
    if (cnt >= 40).sum() == 4: break
legs = ids[cnt >= 40]; leg_of = np.full(len(VT), 'body', dtype=object)
ax = 2 if np.ptp(VT[:, 2]) > np.ptp(VT[:, 0]) else 0      # long axis; the head is the highest vertex
head = VT[np.argmax(VT[:, 1]), ax]; mid = VT[:, ax].mean()
for l in legs:                                           # name each leg by its side (x, the mirror axis) and end
    c = VT[ll == l].mean(0); leg_of[ll == l] = ('x+' if c[0] > 0 else 'x-') + (' front' if (c[ax] - mid) * (head - mid) > 0 else ' hind')
res['template_legs'] = sorted(set(leg_of) - {'body'})

feat = torch.load(a.features, map_location='cpu')
def pfeat(rc):
    rc = torch.as_tensor(np.asarray(rc)).long()
    return F.normalize(feat[rc[:, 0], rc[:, 1]].float().to(device), dim=-1)
p1 = torch.load(os.path.join(a.phase1_dir, 'encoder_checkpoint.pth'), map_location=device)
cks = sorted(glob.glob(os.path.join(a.run_dir, 'encoder_checkpoint_step*.pth')), key=lambda p: int(re.findall(r'step(\d+)', p)[0]))
seed_everything(0)
enc = EncoderL2Norm(4, 2304, out_dim=2304, positional_encoding=True, sigma=5.0, network_verbose=0).to(device)
set_fourier_basis(enc, torch.load(cks[0], map_location='cpu').get('fourier_basis'))
P = np.array([pix[n] for n in names])
for step, ck in [(0, None)] + [(int(re.findall(r'step(\d+)', p)[0]), p) for p in cks]:
    c = None if ck is None else torch.load(ck, map_location=device)
    load_state_dict(enc, p1['encoder_state_dict'] if c is None else c['encoder_state_dict'])
    mu = torch.zeros(1, 3) if c is None or c.get('mu_aniso') is None else c['mu_aniso'][-1:].cpu()   # zeros = the init circle s=1
    with torch.no_grad():
        vf = enc(verts)
        _, ti, w = soft_map_to_vertices(pfeat(P), vf, verts, a.k, return_topk=True, temperature=a.temperature)
        d3 = expected_geodesic_distance_3d(ti[:1], w[:1], ti[None, 1:], w[None, 1:], T3)[0].cpu().numpy() / D3
    s = aniso_scale_from_params(mu, torch.as_tensor(P[:1]), torch.as_tensor(P[None, 1:]))[0].numpy()
    top1 = ti[:, 0].cpu().numpy()
    row = {'step': step, 'ellipse': mu[0].tolist(), 'top1': {n: int(top1[i]) for i, n in enumerate(names)},
           'leg': {n: leg_of[top1[i]] for i, n in enumerate(names)},
           'student': {n: float(d3[i - 1] / s[i - 1]) for i, n in enumerate(names) if i}, 'scale': {n: float(s[i - 1]) for i, n in enumerate(names) if i}}
    if rn:
        with torch.no_grad():
            _, tr, wr = soft_map_to_vertices(pfeat(allr), vf, verts, a.k, return_topk=True, temperature=a.temperature)
            d3r = expected_geodesic_distance_3d(tr[srcs], wr[srcs], tr[None].expand(len(srcs), -1, -1), wr[None].expand(len(srcs), -1, -1), T3).cpu().numpy() / D3
        sr = aniso_scale_from_params(mu.expand(len(srcs), 3), torch.as_tensor(allr[srcs]), torch.as_tensor(allr)[None].expand(len(srcs), -1, -1)).numpy()
        stu = d3r / sr
        blk = lambda i, j: (slice(0, 30) if i == 0 else slice(30, 60), slice(0, split) if j == 0 else slice(split, None))
        row['regions'] = {f'{rn[i]}-{rn[j]}': {'student': float(stu[blk(i, j)].mean()), 'teacher': float(Dr[blk(i, j)].mean()),
                                              'huber': float(F.huber_loss(torch.as_tensor(stu[blk(i, j)]), torch.as_tensor(Dr[blk(i, j)]), delta=1.0))}
                          for i, j in ((0, 0), (1, 1), (0, 1))}
        t1 = tr[:, 0].cpu().numpy()
        row['region_legs'] = {n: {l: float(np.mean(leg_of[t1[sl]] == l)) for l in res['template_legs'] + ['body']}
                              for n, sl in ((rn[0], slice(0, split)), (rn[1], slice(split, None)))}
    res['steps'].append(row)
    print(f'step {step:4d}  ' + '  '.join(f'{n}: student {row["student"][n]:.3f} teacher {res["teacher"][n]:.3f} ({row["leg"][n]})' for n in names[1:])
          + f'  [rep -> {row["leg"][rep]}]' + ('' if not rn else '  ' + '  '.join(f'{k} s/t {v["student"]:.3f}/{v["teacher"]:.3f}' for k, v in row['regions'].items())), flush=True)
# template paths rep -> others at the first and last step (top-1 vertices)
_, predT = scipy.sparse.csgraph.dijkstra(GT, directed=False, indices=[res['steps'][0]['top1'][rep], res['steps'][-1]['top1'][rep]], return_predecessors=True)
res['template_path'] = {tag: {n: path(predT[i], res['steps'][j]['top1'][rep], res['steps'][j]['top1'][n]) for n in names[1:]}
                        for i, (tag, j) in enumerate((('zs', 0), ('trained', -1)))}
res['lift_pix_vertex'] = {n: V[pv[pix[n]]].tolist() for n in names}
json.dump(res, open(a.out_json, 'w'))
print('saved', a.out_json)
