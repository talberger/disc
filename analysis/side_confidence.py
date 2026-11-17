"""Which side of the (mirror-symmetric) template does each pixel pick, and how sure is it? (Tal, 2026-11-17, bear 6462: why does the
zero-shot pick the other flank.) Per mask pixel, the soft map (top-K, T, as the eval) gives p(x+) = the weight on template vertices with
x > +band (x < -band = the other side; the midline band counts for neither). Run once on the image's features and once on the features
of the image FLIPPED left-right (the map flipped back): if the picked side flips with the image, the zero-shot decides the side from
the image's orientation, not from the animal.
python analysis/side_confidence.py --img <crop png> --mask <mask.pth> --features <pix features> --features_flipped <features of the
  flipped png> --vertex_features <pred_f.pth> --obj_path ./demo/shic/shapes/bear.obj --name shic_bear [--gt <gt.pth>] --out fig.png
"""
import argparse, json, os, sys
import numpy as np, torch, torch.nn.functional as F
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from modules.mapping_loss import soft_map_to_vertices
from modules.utils import device, loadmesh

ap = argparse.ArgumentParser()
for k in ('img', 'mask', 'features', 'features_flipped', 'vertex_features', 'obj_path', 'name', 'out'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--gt', default=None); ap.add_argument('--k', type=int, default=10); ap.add_argument('--temperature', type=float, default=0.01)
ap.add_argument('--band', type=float, default=0.05, help='midline half-width, as a fraction of the template x extent')
a = ap.parse_args()

V = loadmesh(dir=a.obj_path, name=a.name, load_rings=False).vertices
Vn = V.cpu().numpy(); xr = np.ptp(Vn[:, 0])
mir = cKDTree(Vn).query(Vn * np.array([-1, 1, 1]))[0]
print(f'template mirror check about x=0: median nn distance {np.median(mir) / xr:.4f} of the x extent (0 = exactly symmetric)')
side = np.where(Vn[:, 0] > a.band * xr, 1, np.where(Vn[:, 0] < -a.band * xr, -1, 0))
vf = torch.load(a.vertex_features, map_location=device)
mask = torch.load(a.mask).numpy().astype(bool); H, W = mask.shape; rr, cc = np.nonzero(mask)

def pside(feat, flipped):
    c = W - 1 - cc if flipped else cc                     # the same physical pixel in the flipped image
    f = F.normalize(feat[torch.as_tensor(rr), torch.as_tensor(c)].float().to(device), dim=-1)
    out = []
    with torch.no_grad():
        for s in range(0, len(f), 8192):
            _, ti, w = soft_map_to_vertices(f[s:s + 8192], vf, V, a.k, return_topk=True, temperature=a.temperature)
            sd = torch.as_tensor(side, device=w.device)[ti]
            out.append(torch.stack([(w * (sd > 0)).sum(1), (w * (sd < 0)).sum(1)], 1).cpu())
    o = torch.cat(out).numpy(); m = np.full((H, W), np.nan); m[rr, cc] = o[:, 0] / np.maximum(o.sum(1), 1e-9)
    mid = np.full((H, W), np.nan); mid[rr, cc] = 1 - o.sum(1)
    return m, mid

p0, mid0 = pside(torch.load(a.features, map_location='cpu'), False)
p1, mid1 = pside(torch.load(a.features_flipped, map_location='cpu'), True)
st = lambda p: {'x+ share': float(np.nanmean(p > 0.5)), 'mean p(x+)': float(np.nanmean(p)), 'confidence mean |p-0.5|*2': float(np.nanmean(np.abs(p - 0.5)) * 2)}
res = {'image': st(p0), 'flipped image (mapped back)': st(p1), 'pixels that change side': float(np.nanmean((p0 > 0.5) != (p1 > 0.5)))}
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.splitext(a.out)[0] + '.json', 'w'), indent=1)

img = np.asarray(Image.open(a.img).convert('RGB'))
fig, axs = plt.subplots(1, 4, figsize=(24, 6.2 * H / W + 1.2))
def show(ax, p, t):
    ax.imshow(img); im = ax.imshow(p, cmap='coolwarm', vmin=0, vmax=1, alpha=0.85); ax.set_title(t, fontsize=13); ax.axis('off'); return im
axs[0].imshow(img); axs[0].set_title('crop', fontsize=13); axs[0].axis('off')
show(axs[1], p0, f'zero-shot: p(template x+ side)\nx+ share {res["image"]["x+ share"]:.2f}, confidence {res["image"]["confidence mean |p-0.5|*2"]:.2f}')
show(axs[2], p1, f'same, on the image FLIPPED left-right (mapped back)\nx+ share {res["flipped image (mapped back)"]["x+ share"]:.2f}')
im = show(axs[3], np.where(np.isnan(p0), np.nan, ((p0 > 0.5) != (p1 > 0.5)).astype(float)), f'pixels whose side changes with the flip: {res["pixels that change side"]:.2f}')
if a.gt:
    g = torch.load(a.gt, map_location='cpu')
    for ax in axs:
        ax.scatter(g['cols'].numpy(), g['rows'].numpy(), s=180, marker='*', c='yellow', edgecolors='k', zorder=5)
cb = fig.colorbar(im, ax=axs[1:3], fraction=0.02); cb.set_label('red = x+ side, blue = x- side (last panel: red = changes)')
plt.savefig(a.out, dpi=70, bbox_inches='tight'); print('saved', a.out)
