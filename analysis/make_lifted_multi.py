"""Summary + figures of the lifted-teacher comparison on many bears (scripts/run_lifted_bears.sh STEP=figs; Tal, 2026-10-26).
summary.txt/.json: per bear and mean (soft-snap, 228-normalised) of SHIC | ZS | lifted stage 1 | stage 2 | per-seg | hybrid | 2D stage 1 | 2D stage 2 |
2D per-seg, the paired differences vs SHIC / ZS / 2D two-stage (mean, SE, better-on), separately for the 20-bear subset and the crowded set.
backproj_<set>_<k>.png: rows = bears (5 per figure), cols = photo | segments | SHIC | ZS | stage 1 | stage 2 | per-seg | hybrid | 2D two-stage."""
import argparse, json, math, os
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont

ARMS = ['SHIC', 'zs', 'lifted_stage1', 'lifted_stage2', 'lifted_perseg', 'lifted_hybrid', '2d_stage1', '2d_stage2', '2d_perseg']
PANELS = [('SHIC', 'SHIC'), ('zs', 'ZS'), ('lifted_stage1', 'stage 1 (global)'), ('lifted_stage2', 'stage 2 (two-stage)'),
          ('lifted_perseg', 'per-seg only'), ('lifted_hybrid', 'hybrid'), ('2d_stage2', '2D two-stage (before)'), ('2d_perseg', '2D per-seg (before)')]
H, GAP, PAD = 260, 6, 44


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
    pal = np.random.RandomState(3).randint(40, 255, (n + 1, 3)).astype(float); ov = ph * 0.35
    for k in range(1, n + 1):
        ov[lab == k] = 0.45 * ph[lab == k] + 0.55 * pal[k]
    return Image.fromarray(ov.clip(0, 255).astype(np.uint8)), int((np.unique(lab) > 0).sum())


def stats(x):
    n = len(x); m = float(np.mean(x)); se = float(np.std(x, ddof=1) / math.sqrt(n)) if n > 1 else float('nan')
    return n, m, se


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', nargs='+', required=True); ap.add_argument('--crowd', nargs='+', default=[])
    ap.add_argument('--out_dir', required=True); ap.add_argument('--src_sub', required=True); ap.add_argument('--src_crowd', required=True)
    ap.add_argument('--lifted_dir', default='data/densepose_lvis/lifted')
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    shic = json.load(open('data/densepose_lvis/eval_shic_bear/results.json'))['bbox']['per_instance']
    res = {}
    for i in a.ids:
        p = f'{a.lifted_dir}/lvis{i}/multi_eval.json'
        if not os.path.exists(p):
            continue
        r = {k: v['soft_snap']['all']['mean'] for k, v in json.load(open(p))['arms'].items()}
        if i in shic:
            r['SHIC'] = shic[i]
        res[i] = r
    sets = [('20-bear subset', [i for i in a.ids if i not in a.crowd and i in res]), ('crowded bears', [i for i in a.crowd if i in res])]
    lines = ['soft-snap geodesic error (228-normalised), mean of the GT points; lower = better; 1 seed. lifted_* = Pixal3D-mesh teacher, 2d_* = before', '']
    for name, ids in sets:
        if not ids:
            continue
        lines.append(f'== {name} ({len(ids)}) ==')
        lines.append('%-8s' % 'bear' + ''.join('%15s' % x for x in ARMS))
        for i in ids:
            lines.append('%-8s' % i + ''.join('%15s' % (f'{res[i][x]:.1f}' if x in res[i] else '-') for x in ARMS))
        lines.append('%-8s' % 'MEAN' + ''.join('%15s' % (f'{np.mean([res[i][x] for i in ids if x in res[i]]):.1f}'
                                                         if any(x in res[i] for i in ids) else '-') for x in ARMS))
        # Tal's questions (2026-10-26): (1) does stage 2 add to stage 1 / is per-seg alone better, (2) does the hybrid work,
        # (3) did the lift help (lifted vs the same arm with the 2D teacher)
        lines.append('  QUESTIONS (paired, negative = the first arm better):')
        for x, ref in [('lifted_stage2', 'lifted_stage1'), ('lifted_perseg', 'lifted_stage2'), ('lifted_hybrid', 'lifted_stage2'),
                       ('lifted_hybrid', 'lifted_perseg'), ('lifted_stage1', '2d_stage1'), ('lifted_stage2', '2d_stage2'), ('lifted_perseg', '2d_perseg')]:
            d = [res[i][x] - res[i][ref] for i in ids if x in res[i] and ref in res[i]]
            if len(d) > 1:
                n, m, se = stats(d); lines.append(f'    {x:14s} - {ref:14s} n={n:2d} {m:+6.2f} (SE {se:.2f}) first better on {sum(v < 0 for v in d)}/{n}')
        for ref in ('SHIC', 'zs', '2d_stage2'):
            lines.append(f'  paired arm - {ref} (negative = arm better):')
            for x in ['lifted_stage1', 'lifted_stage2', 'lifted_perseg', 'lifted_hybrid', '2d_stage2', '2d_perseg']:
                if x == ref:
                    continue
                d = [res[i][x] - res[i][ref] for i in ids if x in res[i] and ref in res[i]]
                if len(d) > 1:
                    n, m, se = stats(d); lines.append(f'    {x:15s} n={n:2d} {m:+6.2f} (SE {se:.2f}) better on {sum(v < 0 for v in d)}/{n}')
        lines.append('')
    open(f'{a.out_dir}/summary.txt', 'w').write('\n'.join(lines) + '\n'); json.dump(res, open(f'{a.out_dir}/summary.json', 'w'), indent=1)
    print('\n'.join(lines))

    f, fs = font(16), font(13)
    for name, ids in sets:
        key = 'sub20' if name.startswith('20') else 'crowd'
        for k0 in range(0, len(ids), 5):
            rows = []
            for i in ids[k0:k0 + 5]:
                src = f'{a.src_crowd if i in a.crowd else a.src_sub}/lvis{i}'; B = f'{a.lifted_dir}/lvis{i}/backproj'
                photo = Image.open(f'{src}/lvis{i}.png').convert('RGB'); w = round(photo.width * H / photo.height)
                seg, n = seg_overlay(photo, f'{src}/lvis{i}_fine_segments.pth')
                panels = [(f'bear {i}', photo.resize((w, H))), (f'{n} segments', seg.resize((w, H)))]
                for arm, title in PANELS:
                    p = f'{B}/lvis{i}_{arm}_backproj.png'; e = res[i].get(arm)
                    panels.append((f'{title}  {e:.1f}' if e is not None else title,
                                   Image.open(p).convert('RGB').resize((w, H)) if os.path.exists(p) else Image.new('RGB', (w, H), (235, 235, 235))))
                rows.append(panels)
            Wd = max(sum(im.width + GAP for _, im in r) for r in rows)
            out = Image.new('RGB', (Wd, len(rows) * (H + PAD) + 30), 'white'); d = ImageDraw.Draw(out)
            d.text((4, 6), f'{name}: soft-snap error (lower = better); lifted = Pixal3D-mesh teacher, SAM 1 segments', fill='black', font=fs)
            for r_i, r in enumerate(rows):
                x, y = 0, 30 + r_i * (H + PAD)
                for t, im in r:
                    out.paste(im, (x, y + PAD))
                    d.text((x + 4, y + 14), t, fill='black', font=f if d.textlength(t, font=f) <= im.width - 6 else fs); x += im.width + GAP
            pth = f'{a.out_dir}/backproj_{key}_{k0 // 5 + 1}.png'; out.save(pth); print('saved', pth, out.size)


if __name__ == '__main__':
    main()
