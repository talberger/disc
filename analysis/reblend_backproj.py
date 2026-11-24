"""Re-blend existing back-projection PNGs with transparency (Itai's task 3, 2026-11-24) -- no GPU, no mask file.

A backproj PNG = the photo outside the mask + opaque mesh colours inside it, so the mask is recovered as the
pixels where the PNG differs from the photo. Inside it: out = a * colour + (1 - a) * photo.
New runs can do the same at render time with `color_image_from_knn.py --overlay_alpha a`.

Writes a grid: rows = instances, columns = image | SHIC at each alpha | ours at each alpha, with the scores.
Run:
  python analysis/reblend_backproj.py --ids 15618 6111 15745 --alphas 1 0.7 0.5 --out <png>
"""
import argparse, json, os
import numpy as np
from PIL import Image

ROOT, ARCH = 'data/densepose_lvis/lifted_full', 'data/densepose_lvis/pvc_archive/lifted_full'


def reblend(bp, photo, a, tol=3):
    """bp, photo: [H, W, 3] uint8. Mask = pixels whose colour differs from the photo by more than tol."""
    m = np.abs(bp.astype(np.int16) - photo.astype(np.int16)).max(-1) > tol
    out = photo.astype(np.float32).copy()
    out[m] = a * bp[m] + (1 - a) * photo[m]
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', nargs='+', required=True); ap.add_argument('--alphas', nargs='+', type=float, default=[1, 0.7, 0.5])
    ap.add_argument('--out', required=True); ap.add_argument('--dpi', type=int, default=140)
    a = ap.parse_args()
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    shic = {l.split()[0]: float(l.split()[1]) for l in open(f'{ROOT}/summary/summary.txt') if l.split() and l.split()[0].isdigit()}
    nc = 1 + 2 * len(a.alphas)
    fig, axs = plt.subplots(len(a.ids), nc, figsize=(3.2 * nc, 3.4 * len(a.ids)), squeeze=False)
    for r, i in enumerate(a.ids):
        photo = np.asarray(Image.open(f'data/densepose_lvis/runs_full_poly/lvis{i}/lvis{i}.png').convert('RGB'))
        ours_s = json.load(open(f'{ARCH}/lvis{i}/stage1_main/eval_all.json'))['arms']['lifted_amodal']['soft_snap']['all']['mean']
        arms = [('SHIC', f'{ROOT}/lvis{i}/backproj/lvis{i}_SHIC_backproj.png', shic[i]),
                ('ours', f'{ARCH}/lvis{i}/stage1_main/backproj/lvis{i}_lifted_amodal_backproj.png', ours_s)]
        axs[r, 0].imshow(photo, interpolation='nearest'); axs[r, 0].set_title(f'lvis{i}', fontsize=11)
        c = 1
        for name, p, s in arms:
            bp = np.asarray(Image.open(p).convert('RGB'))
            for al in a.alphas:
                axs[r, c].imshow(reblend(bp, photo, al), interpolation='nearest')
                axs[r, c].set_title(f'{name} {s:.1f}  (alpha {al:g})', fontsize=11); c += 1
    for ax in axs.flat: ax.axis('off')
    plt.tight_layout(); os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    plt.savefig(a.out, dpi=a.dpi); print('saved', a.out)


if __name__ == '__main__':
    main()
