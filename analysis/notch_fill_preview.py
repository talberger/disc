"""Notch fill of the amodal lift input -- PREVIEW only, nothing trained. DROPPED (Tal, 2026-11-12): already at r = 3% of the diagonal it
closes 6462's open mouth, at 4% the gap between its raised paw and head, before it closes 55342's grass notch -- shape alone cannot tell a
grass notch from a real gap. Kept as the record of what was tried (Tal, 2026-11-12; bear 55342: pix2gestalt copies the visible mask's
sharp notch where sparse grass stands in front of the fur instead of completing it). Generic rule: a morphological closing of the lift
input's alpha with a disk of radius --frac x the mask's bbox diagonal fills every inward notch NARROWER than the disk that opens to the
outside; wider gaps (between legs) and enclosed holes (between arm and body) stay. The new pixels take the colour of the nearest pixel of the object's core, smoothed.
Per instance: the lift input RGBA (as Pixal3D gets it) before / after, the added pixels in red, and the added share.
Usage: python analysis/notch_fill_preview.py --rgba_dir /workspace/pixal3d_out --ids 55342 6462 ... --frac 0.03 --out_dir <dir>
       (--all: every bear_lvis<i>_amodal_rgba.png in --rgba_dir; prints the added share per bear, sorted)
"""
import argparse, glob, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gapfill_preview import closing


def notch_fill(rgba, frac):
    """-> (filled RGBA uint8, added bool [H, W], radius px)."""
    import cv2
    m = rgba[..., 3] > 127; ys, xs = np.nonzero(m)
    r = max(1, int(round(frac * np.hypot(np.ptp(ys) + 1, np.ptp(xs) + 1))))
    add = closing(m, r) & ~m
    lab, n = ndimage.label(add, structure=np.ones((3, 3)))                   # enclosed holes stay (a real gap, e.g. between arm and body):
    outside = ndimage.binary_dilation(~(m | add) & ~ndimage.binary_fill_holes(m), structure=np.ones((3, 3)))   # only notches open to the outside
    add &= np.isin(lab, np.setdiff1d(np.unique(lab[outside & add]), [0]))
    out = rgba.copy()
    if add.any():   # colour = the nearest pixel of the object's core (eroded: its edge is blended with the background), smoothed
        core = ndimage.binary_erosion(m, iterations=2); core = core if core.any() else m
        _, (ir, ic) = ndimage.distance_transform_edt(~core, return_indices=True)
        fill = cv2.GaussianBlur(np.ascontiguousarray(rgba[..., :3][ir, ic]), (0, 0), max(1.0, r / 4))
        out[..., :3] = np.where(add[..., None], fill, rgba[..., :3])
        out[..., 3] = np.where(m | add, 255, 0).astype(np.uint8)
    return out, add, r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--rgba_dir', required=True); ap.add_argument('--ids', nargs='*', default=[])
    ap.add_argument('--all', action='store_true'); ap.add_argument('--frac', type=float, default=0.03); ap.add_argument('--out_dir', required=True)
    ap.add_argument('--cls', default='bear')
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    ids = a.ids or sorted(p.split('_lvis')[1].split('_')[0] for p in glob.glob(f'{a.rgba_dir}/{a.cls}_lvis*_amodal_rgba.png'))
    rows = []
    for i in ids:
        p = f'{a.rgba_dir}/{a.cls}_lvis{i}_amodal_rgba.png'
        if not os.path.exists(p): print(f'lvis{i}: no amodal rgba'); continue
        rgba = np.asarray(Image.open(p).convert('RGBA')); out, add, r = notch_fill(rgba, a.frac)
        share = add.sum() / (rgba[..., 3] > 127).sum(); rows.append((share, i, r))
        if a.all: continue
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        W = lambda x: (x[..., :3] / 255.) * (x[..., 3:] / 255.) + 1 - x[..., 3:] / 255.
        red = W(out).copy(); red[add] = red[add] * 0.35 + np.array([1, 0, 0]) * 0.65
        fig, axs = plt.subplots(1, 3, figsize=(13, 4.8 * rgba.shape[0] / rgba.shape[1] + 0.8))
        for ax, im, t in zip(axs, (W(rgba), W(out), red), ('before (lift input)', f'after notch fill (r = {r} px)', f'added: {100 * share:.1f}% of the object')):
            ax.imshow(im); ax.axis('off'); ax.set_title(t, fontsize=12)
        fig.suptitle(f'{a.cls} {i}', fontsize=13); plt.tight_layout(); plt.savefig(f'{a.out_dir}/{a.cls}_lvis{i}_notch_fill.png', dpi=80); plt.close(fig)
        Image.fromarray(out).save(f'{a.out_dir}/{a.cls}_lvis{i}_amodal_notchfill_rgba.png')
    for s, i, r in sorted(rows, reverse=True): print(f'lvis{i}\tadded {100 * s:.2f}%\tr {r}')


if __name__ == '__main__':
    main()
