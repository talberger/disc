"""One figure for the 20-bear XSEG run (scripts/make_xseg_bears_figs.sh; Tal, 2026-10-24): one row per bear,
colour key | photo | segment map | twostage | perseg | nofeat | Fonly, mean soft-snap error (228-normalised) in each title."""
import argparse, json, os
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont

ARMS = ['SHIC', 'twostage', 'perseg', 'nofeat', 'Fonly']
H, GAP, PAD = 300, 6, 40


def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def seg_overlay(photo, path):
    lab = torch.as_tensor(torch.load(path)).numpy(); ph = np.asarray(photo).astype(float); n = int(lab.max())
    pal = np.random.RandomState(3).randint(40, 255, (n + 1, 3)).astype(float)
    ov = ph * 0.35
    for k in range(1, n + 1):
        ov[lab == k] = 0.45 * ph[lab == k] + 0.55 * pal[k]
    return Image.fromarray(ov.clip(0, 255).astype(np.uint8)), int((np.unique(lab) > 0).sum())


def pick(res):
    """Largest Fonly gain vs twostage, largest loss, the median bear, the largest |Fonly - nofeat| (unique, in that order)."""
    r = {i: v for i, v in res.items() if 'Fonly' in v and 'twostage' in v}
    g = sorted(r, key=lambda i: r[i]['Fonly'] - r[i]['twostage'])      # most negative = Fonly best
    return list(dict.fromkeys([g[0], g[-1], g[len(g) // 2], max(r, key=lambda i: abs(r[i]['Fonly'] - r[i]['nofeat']))]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs_in'); ap.add_argument('--xdemo'); ap.add_argument('--summary', required=True)
    ap.add_argument('--ids', nargs='+'); ap.add_argument('--key'); ap.add_argument('--out')
    ap.add_argument('--print_pick', action='store_true', help='only print the picked bear ids and exit')
    ap.add_argument('--shic_results', default=None, help="SHIC's own eval json (bbox.per_instance = its error per bear)")
    a = ap.parse_args()
    if a.print_pick:
        print(' '.join(pick(json.load(open(a.summary)))))
        return
    res = json.load(open(a.summary)); f, fs = font(16), font(13)
    shic = json.load(open(a.shic_results))['bbox']['per_instance'] if a.shic_results and os.path.exists(a.shic_results) else {}
    for i in res:
        if i in shic: res[i]['SHIC'] = shic[i]
    rows = []
    for i in a.ids:
        tag = f'lvis{i}'; d = f'{a.runs_in}/{tag}'; o = f'{a.xdemo}/bear_{tag}/backproj'
        photo = Image.open(f'{d}/{tag}.png').convert('RGB'); w = round(photo.width * H / photo.height)
        seg, n = seg_overlay(photo, f'{d}/{tag}_fine_segments.pth')
        r = res.get(i, {})
        panels = [(f'bear {i}', Image.open(a.key).convert('RGB').resize((H, H))), ('photo', photo.resize((w, H))),
                  (f'{n} segments', seg.resize((w, H)))]
        for arm in ARMS:
            p = f'{o}/{tag}_{arm}_backproj.png'
            if os.path.exists(p):
                panels.append(('%s  %.1f' % (arm, r[arm]) if arm in r else arm, Image.open(p).convert('RGB').resize((w, H))))
            else:
                panels.append((f'{arm}  n/a', Image.new('RGB', (w, H), (235, 235, 235))))
        rows.append(panels)
    W = max(sum(im.width + GAP for _, im in r) for r in rows)
    out = Image.new('RGB', (W, len(rows) * (H + PAD) + 30), 'white'); dr = ImageDraw.Draw(out)
    dr.text((4, 6), 'soft-snap geodesic error (228-normalised, mean of the GT points; lower = better). ZS per bear in the summary table.',
            fill='black', font=fs)
    for k, r in enumerate(rows):
        x, y = 0, 30 + k * (H + PAD)
        for t, im in r:
            out.paste(im, (x, y + PAD)); dr.text((x + 4, y + 12), t, fill='black', font=f); x += im.width + GAP
    out.save(a.out); print('saved', a.out, out.size)


if __name__ == '__main__':
    main()
