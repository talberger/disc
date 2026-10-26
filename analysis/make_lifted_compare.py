"""Figure + summary for the lifted-geodesic runs (scripts/make_lifted_figs.sh; Tal, 2026-10-26).
Figure: one row per instance -- colour key | photo | segments | SHIC | ZS | 2D two-stage | lifted two-stage, mean soft-snap error in each title.
Summary: per-instance table of every arm of eval_lifted.json + SHIC (its own eval, argmax), means, paired lifted - 2D."""
import argparse, json, math, os
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont

PANELS = [('SHIC', 'SHIC'), ('zs', 'ZS'), ('2d_final', '2D two-stage'), ('lifted_final', 'lifted two-stage')]
H, GAP, PAD = 300, 6, 40


def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def seg_overlay(photo, path):
    lab = torch.as_tensor(torch.load(path)).numpy(); ph = np.asarray(photo).astype(float); n = int(lab.max())
    pal = np.random.RandomState(3).randint(40, 255, (n + 1, 3)).astype(float)
    ov = ph * 0.35
    for k in range(1, n + 1):
        ov[lab == k] = 0.45 * ph[lab == k] + 0.55 * pal[k]
    return Image.fromarray(ov.clip(0, 255).astype(np.uint8)), int((np.unique(lab) > 0).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lifted_dir', required=True); ap.add_argument('--instances', nargs='+', required=True, help='class:tag:src_dir')
    ap.add_argument('--out', required=True); ap.add_argument('--summary', required=True)
    a = ap.parse_args()
    f, fs = font(16), font(13)
    shic = {}
    for cls in ('bear', 'horse', 'elephant'):
        p = f'data/densepose_lvis/eval_shic_{cls}/results.json'
        if os.path.exists(p):
            shic[cls] = json.load(open(p))['bbox']['per_instance']
    res, rows = {}, []
    for it in a.instances:
        cls, tag, src = it.split(':')
        ev = f'{a.lifted_dir}/{tag}/eval_lifted.json'
        if not os.path.exists(ev):
            continue
        r = {k: v['soft_snap']['all']['mean'] for k, v in json.load(open(ev))['arms'].items()}
        if tag[4:] in shic.get(cls, {}):
            r['SHIC'] = shic[cls][tag[4:]]
        res[tag] = {'class': cls, **r}
        o = f'{a.lifted_dir}/{tag}/backproj'
        photo = Image.open(f'{src}/{tag}.png').convert('RGB'); w = round(photo.width * H / photo.height)
        seg, n = seg_overlay(photo, f'{src}/{tag}_fine_segments.pth')
        key = f'demo/shic/colored_mesh/{"checker16_uv_azim135" if cls == "bear" else cls + "_checker16_uv_azim135"}.png'
        panels = [(f'{cls} {tag[4:]}', Image.open(key).convert('RGB').resize((H, H)) if os.path.exists(key) else Image.new('RGB', (H, H), 'white')),
                  ('photo', photo.resize((w, H))), (f'{n} segments', seg.resize((w, H)))]
        for arm, name in PANELS:
            p = f'{o}/{tag}_{arm}_backproj.png'
            title = f'{name}  {r[arm]:.1f}' if arm in r else name
            panels.append((title, Image.open(p).convert('RGB').resize((w, H)) if os.path.exists(p) else Image.new('RGB', (w, H), (235, 235, 235))))
        rows.append(panels)
    Wd = max(sum(im.width + GAP for _, im in r) for r in rows)
    out = Image.new('RGB', (Wd, len(rows) * (H + PAD) + 30), 'white'); dr = ImageDraw.Draw(out)
    dr.text((4, 6), 'soft-snap geodesic error (228-normalised, mean of the GT points; lower = better); SHIC = its own eval (argmax)', fill='black', font=fs)
    for k, r in enumerate(rows):
        x, y = 0, 30 + k * (H + PAD)
        for t, im in r:
            out.paste(im, (x, y + PAD)); dr.text((x + 4, y + 12), t, fill='black', font=f); x += im.width + GAP
    out.save(a.out); print('saved', a.out, out.size)

    arms = ['SHIC', 'zs', '2d_stage1', '2d_final', 'lifted_stage1', 'lifted_final']
    lines = ['soft-snap geodesic error (228-normalised), mean of the GT points; lower = better; 1 seed', '',
             '%-12s' % 'instance' + ''.join('%14s' % x for x in arms)]
    for tag, r in res.items():
        lines.append('%-12s' % f'{r["class"][0]}{tag[4:]}' + ''.join('%14s' % (f'{r[x]:.1f}' if x in r else '-') for x in arms))
    lines.append('%-12s' % 'MEAN' + ''.join('%14s' % (f'{np.mean([r[x] for r in res.values() if x in r]):.1f}'
                                                       if any(x in r for r in res.values()) else '-') for x in arms))
    d = [r['lifted_final'] - r['2d_final'] for r in res.values() if 'lifted_final' in r and '2d_final' in r]
    if len(d) > 1:
        m = float(np.mean(d)); se = float(np.std(d, ddof=1) / math.sqrt(len(d)))
        lines.append(f'\nlifted - 2D (final): {m:+.2f} (SE {se:.2f}), lifted better on {sum(x < 0 for x in d)}/{len(d)}')
    open(a.summary + '.txt', 'w').write('\n'.join(lines) + '\n'); json.dump(res, open(a.summary + '.json', 'w'), indent=1)
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
