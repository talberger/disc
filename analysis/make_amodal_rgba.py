"""RGBA input for external/pixal3d/lift.py from pix2gestalt's COMPLETED CONTENT (occlusion + lift; Tal, 2026-10-28).
The amodal step (scripts/make_amodal_mask.sh) saved 3 RGB samples per instance (<tag>_amodal_samples.npz, 256x256 over the square crop of
<tag>_amodal_input.npz); until now only their masks were used. Here ONE sample is brought back to the run crop's pixel grid exactly as
analysis/merge_amodal_mask.py does (256 -> square crop px -> bbox -> run crop) and composed:
  RGB   = the sample's content on the whole object (--content all, default: the visible mask still holds thin occluders -- fence wires,
          branches -- that the sample has removed), or the original photo on the visible mask + the sample on the hidden part (--content hidden)
  alpha = visible | sample mask
The training is unchanged: centres only on visible pixels (--object_mask_path), distances through the amodal domain.
Out: <out_png> (RGBA, run-crop size) + <out_png minus .png>_check.png (photo | sample | composed | alpha).
Usage: python analysis/make_amodal_rgba.py --run_dir <dir> --tag lvis206034 --sample 2 --out_png <png>"""
import argparse
import numpy as np, torch
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--run_dir', required=True); ap.add_argument('--tag', required=True)
ap.add_argument('--sample', type=int, required=True, help='0-based index into the saved samples')
ap.add_argument('--content', choices=['all', 'hidden'], default='all')
ap.add_argument('--out_png', required=True)
a = ap.parse_args(); D, T = a.run_dir, a.tag
photo = np.array(Image.open(f'{D}/{T}.png').convert('RGB')); vis = torch.load(f'{D}/{T}_mask.pth').numpy().astype(bool)
g = np.load(f'{D}/{T}_amodal_input.npz'); s = np.load(f'{D}/{T}_amodal_samples.npz')
sq, box, size = g['square'], g['box'], g['size']; side = int(sq[2] - sq[0]); W, H = int(size[0]), int(size[1])
assert vis.shape == (H, W) and photo.shape[:2] == (H, W), (vis.shape, photo.shape, size)


def to_crop(im, resample):
    """256x256 over the square crop -> the run crop (same mapping as merge_amodal_mask.py)."""
    full = Image.fromarray(im).resize((side, side), resample)
    sub = full.crop((box[0] - sq[0], box[1] - sq[1], box[2] - sq[0], box[3] - sq[1]))
    return np.asarray(sub.resize((W, H), resample))


rgb = to_crop(s['preds'][a.sample], Image.LANCZOS)
am = to_crop((s['amodal'][a.sample] * 255).astype(np.uint8), Image.BILINEAR) > 127
hidden = am & ~vis; alpha = vis | am
out = np.where((alpha if a.content == 'all' else hidden)[..., None], rgb, photo)
Image.fromarray(np.dstack([out, (alpha * 255).astype(np.uint8)])).save(a.out_png)
shade = lambda im, m: np.where(m[..., None], im, (im * 0.25 + 190).astype(np.uint8))
Image.fromarray(np.concatenate([photo, rgb, shade(out, alpha), np.repeat((alpha * 255).astype(np.uint8)[..., None], 3, 2)], 1)) \
    .save(a.out_png[:-4] + '_check.png')
print(f'{T} sample {a.sample}: visible {vis.sum()} px, hidden part added {hidden.sum()} px (+{100 * hidden.sum() / vis.sum():.1f}%), '
      f'sample covers {100 * (am & vis).sum() / vis.sum():.1f}% of the visible -> {a.out_png}')
