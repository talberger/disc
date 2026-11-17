"""Figure for analysis/probe_pair_loss.py (Tal, 2026-11-17, horse 147192 hind legs).
Top: the crop with the pixels and regions | the lift seen from the camera and from the other side, with the teacher's geodesic paths
rep -> each other pixel | the template (checker key) from both sides with the student's paths between the top-1 vertices, zero-shot and
trained. Bottom: student (d_3D / D3 / s) against teacher (d_2D / D2) per step for each pair and for the two regions, and where each region's
pixels land on the template legs.
python analysis/probe_pair_loss_fig.py --json probe_hind.json --img <crop png> --lift <lift.pth> --out fig.png
  [--checker demo/shic/colored_mesh/horse_mesh_checker16_uv_color.ply --obj_path ./demo/shic/shapes/horse.obj --name shic_horse]
"""
import argparse, json, os, sys
import numpy as np, open3d as o3d, torch
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from analysis.build_lifted_geodesic_table import decimate
from modules.utils import loadmesh

ap = argparse.ArgumentParser()
ap.add_argument('--json', required=True); ap.add_argument('--img', required=True); ap.add_argument('--lift', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--checker', default='demo/shic/colored_mesh/horse_mesh_checker16_uv_color.ply')
ap.add_argument('--obj_path', default='./demo/shic/shapes/horse.obj'); ap.add_argument('--name', default='shic_horse')
ap.add_argument('--title', default='')
ap.add_argument('--region', action='append', default=[], help="the probe's --region specs, drawn on the crop")
a = ap.parse_args()
J = json.load(open(a.json)); names = list(J['pixels']); rep = names[0]; others = names[1:]
COL = {rep: '#ffffff', others[0]: '#1f77b4', others[-1]: '#d62728'}
for n, c in zip(others[1:-1], ['#2ca02c', '#9467bd']): COL[n] = c

class Cam:
    """Ray-cast render of (V, F) along d with `up`; proj() gives pixel coords and visibility of 3D points."""
    def __init__(s, V, F, d, up, colors=None, res=520):
        s.V, s.F, s.res = V, F, res
        s.sc = o3d.t.geometry.RaycastingScene(); s.sc.add_triangles(V.astype(np.float32), F.astype(np.uint32))
        s.cen = (V.min(0) + V.max(0)) / 2; s.ext = np.ptp(V, 0).max() * 1.06
        d = np.array(d, float); s.d = d / np.linalg.norm(d); r = np.cross(s.d, up); s.r = r / np.linalg.norm(r); s.u = np.cross(s.r, s.d)
        g = (np.arange(res) + 0.5) / res - 0.5; gx, gy = np.meshgrid(g * s.ext, -g * s.ext)
        o = s.cen - 3 * s.ext * s.d + gx.ravel()[:, None] * s.r + gy.ravel()[:, None] * s.u
        h = s.sc.cast_rays(o3d.core.Tensor(np.c_[o, np.tile(s.d, (len(o), 1))].astype(np.float32)))
        t = h['t_hit'].numpy(); ok = np.isfinite(t); n = h['primitive_normals'].numpy()[ok]; sh = (0.45 + 0.55 * np.abs(n @ s.d))[:, None]
        im = np.ones((res * res, 3))
        if colors is None:
            im[ok] = sh * np.array([0.80, 0.66, 0.50])
        else:
            f = h['primitive_ids'].numpy()[ok]; uv = h['primitive_uvs'].numpy()[ok]
            im[ok] = colors[F[f]][np.arange(len(f)), np.c_[1 - uv.sum(1), uv].argmax(1)] * (0.55 + 0.45 * sh)
        s.im = im.reshape(res, res, 3)
    def proj(s, P):
        P = np.atleast_2d(P); q = P - s.cen
        x = (q @ s.r / s.ext + 0.5) * s.res; y = (0.5 - q @ s.u / s.ext) * s.res
        o = P - 3 * s.ext * s.d; t = s.sc.cast_rays(o3d.core.Tensor(np.c_[o, np.tile(s.d, (len(P), 1))].astype(np.float32)))['t_hit'].numpy()
        return x, y, np.abs(t - 3 * s.ext) < 0.015 * s.ext

def draw_path(ax, cam, P, c, label=None):
    x, y, vis = cam.proj(np.asarray(P))
    ax.plot(x, y, ls=(0, (2, 2)), c=c, lw=1.4, alpha=0.8)                     # whole path, dotted = hidden parts
    xv, yv = np.where(vis, x, np.nan), np.where(vis, y, np.nan)
    ax.plot(xv, yv, c='k', lw=4.5); ax.plot(xv, yv, c=c, lw=2.8, label=label)
def dot(ax, cam, p, c, m='o', s=110):
    x, y, v = cam.proj(np.asarray(p)[None])
    ax.scatter(x, y, s=s, marker=m, c=c if v[0] else 'none', edgecolors='k' if v[0] else c, linewidths=1.6, zorder=6)

# lift (world: the camera looks along +y with z up)
lift = torch.load(a.lift, map_location='cpu'); LV, LF = decimate(lift['vertices'].numpy(), lift['faces'].numpy(), 200000)
lcams = [('lift, camera view', Cam(LV, LF, (0, 1, 0), (0, 0, 1))), ('lift, from the other side', Cam(LV, LF, (0, -1, 0), (0, 0, 1)))]
# template in loadmesh order (= the indices in the json), placed in the checker key's frame
mesh = loadmesh(dir=a.obj_path, name=a.name, load_rings=False); TV = mesh.vertices.cpu().numpy()
km = o3d.io.read_triangle_mesh(a.checker); KV, KF, KC = np.asarray(km.vertices), np.asarray(km.triangles), np.asarray(km.vertex_colors)
TV = (TV - (TV.min(0) + TV.max(0)) / 2) * (np.ptp(KV, 0).max() / np.ptp(TV, 0).max()) + (KV.min(0) + KV.max(0)) / 2
tcams = [('x+ side', Cam(KV, KF, (-1, 0, 0), (0, 1, 0), KC)), ('x- side', Cam(KV, KF, (1, 0, 0), (0, 1, 0), KC))]
S = J['steps']; first, last = S[0], S[-1]

fig = plt.figure(figsize=(30, 15)); gs = fig.add_gridspec(2, 7, height_ratios=[1.05, 1])
img = np.asarray(Image.open(a.img).convert('RGB'))
ax = fig.add_subplot(gs[0, 0]); ax.imshow(img); ax.set_title('crop: the pixels and the two regions', fontsize=13); ax.axis('off')
for spec in a.region:
    for b in spec.split('=')[1].split('+'):
        r0, r1, c0, c1 = map(int, b.split(':')); ax.add_patch(plt.Rectangle((c0, r0), c1 - c0, r1 - r0, fill=False, ec='w', lw=1.2, ls='--'))
for n in names:
    r, c = J['pixels'][n]; ax.scatter([c], [r], s=150, c=COL[n], edgecolors='k', linewidths=1.5, zorder=5)
    ax.text(c + 6, r - 6, n, color=COL[n], fontsize=13, weight='bold', path_effects=[pe.withStroke(linewidth=3, foreground='k')])
xs = [J['pixels'][n][1] for n in names]; ys = [J['pixels'][n][0] for n in names]
ax.set_xlim(max(0, min(xs) - 70), min(img.shape[1], max(xs) + 70)); ax.set_ylim(min(img.shape[0], max(ys) + 40), max(0, min(ys) - 120))
for k, (t, cam) in enumerate(lcams):
    ax = fig.add_subplot(gs[0, 1 + k]); ax.imshow(cam.im); ax.axis('off')
    ax.set_title(f'{t}\nteacher paths: ' + ', '.join(f'{n} {J["teacher"][n]:.2f}' for n in others), fontsize=12)
    for n in others: draw_path(ax, cam, J['lift_path'][n], COL[n])
    for n in names: dot(ax, cam, J['lift_pix_vertex'][n], COL[n])
for k, (tag, row) in enumerate((('zero-shot', first), ('trained', last))):
    P = J['template_path']['zs' if k == 0 else 'trained']
    for j, (t, cam) in enumerate(tcams):
        ax = fig.add_subplot(gs[0, 3 + 2 * k + j]); ax.imshow(cam.im); ax.axis('off')
        ax.set_title(f'{tag} (step {row["step"]}), template {t}\n' + ', '.join(f'{n}: {row["leg"][n]}' for n in names), fontsize=11)
        for n in others: draw_path(ax, cam, TV[P[n]], COL[n])
        for n in names: dot(ax, cam, TV[row['top1'][n]], COL[n])

st = [r['step'] for r in S]
ax = fig.add_subplot(gs[1, 0:2])
for n in others:
    ax.plot(st, [r['student'][n] for r in S], '-o', c=COL[n], lw=2.2, label=f'{rep}-{n}: student')
    ax.axhline(J['teacher'][n], c=COL[n], ls='--', lw=1.6, label=f'{rep}-{n}: teacher')
ax.set_xlabel('training step'); ax.set_ylabel('distance / diameter'); ax.set_title('the pairs: student (template) vs teacher (lift)', fontsize=13)
ax.legend(fontsize=11); ax.grid(alpha=0.3)
if 'regions' in S[0]:
    ax = fig.add_subplot(gs[1, 2:4]); RC = ['#1f77b4', '#ff7f0e', '#d62728']
    for c, k in zip(RC, S[0]['regions']):
        ax.plot(st, [r['regions'][k]['student'] for r in S], '-o', c=c, lw=2.2, label=f'{k}: student')
        ax.plot(st, [r['regions'][k]['teacher'] for r in S], '--', c=c, lw=1.6, label=f'{k}: teacher')
    ax.set_xlabel('training step'); ax.set_title('the two regions: mean over sampled pairs', fontsize=13); ax.legend(fontsize=11); ax.grid(alpha=0.3)
    LC = {'x+ front': '#d62728', 'x+ hind': '#1f77b4', 'x- front': '#ff9f1c', 'x- hind': '#2ca02c', 'body': '#999999'}
    for k, rn in enumerate(S[0]['region_legs']):
        ax = fig.add_subplot(gs[1, 4 + k])
        for l in S[0]['region_legs'][rn]:
            ax.plot(st, [r['region_legs'][rn][l] for r in S], '-o', c=LC.get(l, 'k'), lw=2.2, label=l)
        ax.set_ylim(-0.03, 1.03); ax.set_xlabel('training step'); ax.set_title(f'region "{rn}": where its pixels land (top-1)', fontsize=13)
        ax.legend(fontsize=10); ax.grid(alpha=0.3)
fig.suptitle(a.title or 'What the loss sees for one hind-leg pixel, per training step', fontsize=16)
plt.tight_layout(rect=(0, 0, 1, 0.96)); plt.savefig(a.out, dpi=70); print('saved', a.out)
