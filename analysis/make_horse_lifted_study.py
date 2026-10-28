"""Compose the horse-56069 lifted-teacher study (scripts/run_horse56069_lifted_study.sh; Tal, 2026-10-26).
backproj_study.png : one row per (segment map, teacher): photo | segments + the 2048 centres | ZS | stage 1 | stage 2 | per-seg only,
                     mean soft-snap error (+ per GT point) in each title.
segments_centres.png: both segment maps with the centres (the pixels the distance table is measured from) and the GT points.
ellipses_study.png  : the ellipses_<run>.png side by side.
study_summary.txt   : every arm, per GT point + mean, + SHIC."""
import argparse, glob, json, os
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont

H, GAP, PAD = 320, 6, 46
ROWS = [   # Tal 2026-10-26: only the SAM 1 map and the VLPart partimagenet>=0.3 (4-seg) map (+ the 2D reference)
('SAM 1 map, lifted teacher', 'sam1', ['zs', 'sam1_lifted_stage1', 'sam1_lifted_stage2', 'sam1_lifted_perseg', 'sam1_lifted_hybrid']),
        ('VLPart 4-seg map, lifted teacher', 'vlp4', ['zs', 'vlp4_lifted_stage1', 'vlp4_lifted_stage2', 'vlp4_lifted_perseg', 'vlp4_lifted_hybrid']),
        ('SAM 1 map, 2D teacher (before)', 'sam1', ['zs', 'sam1_2d_stage1', 'sam1_2d_stage2', 'sam1_2d_perseg', 'none'])]
COLS = ['ZS', 'stage 1', 'stage 2 (two-stage)', 'per-seg only', 'hybrid (1 stage)']
MU_COLS = [(2, 'mu: stage 2'), (3, 'mu: per-seg'), (4, 'mu: hybrid')]   # ellipse columns: index into a row's arms


def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def seg_overlay(photo, lab, centres=None, gt=None):
    ph = np.asarray(photo).astype(float); n = int(lab.max())
    pal = np.random.RandomState(3).randint(40, 255, (n + 1, 3)).astype(float)
    ov = ph * 0.35
    for k in range(1, n + 1):
        ov[lab == k] = 0.45 * ph[lab == k] + 0.55 * pal[k]
    im = Image.fromarray(ov.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    if centres is not None:
        for r, c in centres:
            d.point((int(c), int(r)), fill=(0, 0, 0))
    if gt is not None:
        for k, (r, c) in enumerate(gt):
            d.ellipse((c - 6, r - 6, c + 6, r + 6), outline=(255, 255, 255), width=3); d.text((c + 8, r - 8), str(k + 1), fill=(255, 255, 255))
    return im, int((np.unique(lab) > 0).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True); ap.add_argument('--tag', required=True); ap.add_argument('--study_dir', required=True)
    ap.add_argument('--table', required=True); ap.add_argument('--maps', nargs='+', required=True, help='name=path')
    ap.add_argument('--shic_results', default=None); ap.add_argument('--class_name', default='horse')
    ap.add_argument('--rows_json', default=None, help='[[title, map key, [4 arms: zs, stage 1, stage 2, per-seg]], ...] (default: the 56069 rows)')
    a = ap.parse_args()
    rows_def = json.loads(a.rows_json) if a.rows_json else ROWS
    f, fs = font(17), font(13)
    ev = json.load(open(f'{a.study_dir}/study_eval.json'))['arms']
    err = {k: v['soft_snap'] for k, v in ev.items()}
    shic_err = None
    if a.shic_results and os.path.exists(a.shic_results):
        shic_err = json.load(open(a.shic_results))['bbox']['per_instance'].get(a.tag[4:])
    photo = Image.open(f'{a.src}/{a.tag}.png').convert('RGB'); w = round(photo.width * H / photo.height)
    centres = torch.load(a.table, map_location='cpu')['coords']; centres = centres.numpy() if torch.is_tensor(centres) else np.asarray(centres)
    gt = torch.load(f'{a.src}/{a.tag}_gt.pth', map_location='cpu'); gtp = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
    maps = dict(m.split('=') for m in a.maps)
    segs = {k: torch.as_tensor(torch.load(p, map_location='cpu')).numpy() for k, p in maps.items()}

    # segments + centres
    tiles = []
    for k, lab in segs.items():
        im, n = seg_overlay(photo, lab, centres, gtp); tiles.append((f'{k}: {n} segments, {len(centres)} centres (black), GT 1-3', im))
    Wd = sum(im.width + GAP for _, im in tiles); out = Image.new('RGB', (Wd, photo.height + PAD), 'white'); d = ImageDraw.Draw(out); x = 0
    for t, im in tiles:
        out.paste(im, (x, PAD)); d.text((x + 4, 14), t, fill='black', font=fs); x += im.width + GAP
    out.save(f'{a.study_dir}/segments_centres.png')

    # back-projections
    rows = []
    for title, mk, arms in rows_def:
        seg, n = seg_overlay(photo, segs[mk], centres, gtp)
        panels = [(title, photo.resize((w, H))), (f'{n} segments + centres', seg.resize((w, H)))]
        sp = f'{os.path.dirname(a.study_dir.rstrip("/"))}/backproj/{a.tag}_SHIC_backproj.png'   # from scripts/make_lifted_figs.sh
        panels.append((f'SHIC  {shic_err:.1f}' if shic_err is not None else 'SHIC',
                       Image.open(sp).convert('RGB').resize((w, H)) if os.path.exists(sp) else Image.new('RGB', (w, H), (235, 235, 235))))
        for col, arm in zip(COLS, arms):
            p = f'{a.study_dir}/backproj/{a.tag}_{arm}_backproj.png'
            if arm in err and os.path.exists(p):
                e = err[arm]
                t = f'{col}  {e["all"]["mean"]:.1f}  (' + '/'.join(f'{x:.0f}' for x in e['per_point']) + ')'
                panels.append((t, Image.open(p).convert('RGB').resize((w, H))))
            else:
                panels.append((f'{col}  n/a', Image.new('RGB', (w, H), (235, 235, 235))))
        for idx, ttl in MU_COLS:                                      # the learned ellipses of the trained arms (Tal 2026-10-26)
            ep = f'{a.study_dir}/ellipses_{arms[idx]}.png' if idx < len(arms) else ''
            panels.append((ttl, Image.open(ep).convert('RGB').resize((w, H)) if os.path.exists(ep) else Image.new('RGB', (w, H), (235, 235, 235))))
        rows.append(panels)
    Wd = max(sum(im.width + GAP for _, im in r) for r in rows)
    out = Image.new('RGB', (Wd, len(rows) * (H + PAD) + 34), 'white'); d = ImageDraw.Draw(out)
    d.text((4, 8), f'{a.class_name} {a.tag[4:]}: soft-snap error, mean (GT pt 1 / 2 / 3' + (' = nose' if a.class_name == 'horse' else '') + '); lower = better. Black dots = the {len(centres)} centres.',
           fill='black', font=fs)
    for i, r in enumerate(rows):
        x, y = 0, 34 + i * (H + PAD)
        for t, im in r:
            out.paste(im, (x, y + PAD))
            if d.textlength(t, font=f) > im.width - 6 and ', ' in t:   # wrap a long row title onto two lines (Tal, 2026-10-26)
                l1, l2 = t.split(', ', 1); d.text((x + 4, y + 4), l1 + ',', fill='black', font=fs); d.text((x + 4, y + 22), l2, fill='black', font=fs)
            else:
                d.text((x + 4, y + 14), t, fill='black', font=f if d.textlength(t, font=f) <= im.width - 6 else fs)
            x += im.width + GAP
    out.save(f'{a.study_dir}/backproj_study.png')

    # ellipses side by side
    ells = sorted(p for p in glob.glob(f'{a.study_dir}/ellipses_*.png') if not p.endswith('ellipses_study.png'))
    if ells:
        ims = [Image.open(p).convert('RGB') for p in ells]; hh = max(i.height for i in ims)
        ims = [i.resize((round(i.width * hh / i.height), hh)) for i in ims]
        out = Image.new('RGB', (sum(i.width + GAP for i in ims), hh), 'white'); x = 0
        for i in ims:
            out.paste(i, (x, 0)); x += i.width + GAP
        out.save(f'{a.study_dir}/ellipses_study.png')

    lines = [f'{a.class_name} {a.tag[4:]}: soft-snap error per GT point (1 / 2 / 3' + (' = nose' if a.class_name == 'horse' else '') + ') and mean; lower = better; 1 seed', '']
    if a.shic_results and os.path.exists(a.shic_results):
        s = json.load(open(a.shic_results))['bbox']['per_instance'].get(a.tag[4:])
        if s is not None:
            lines.append('%-22s %28s %6.1f' % ('SHIC (its own eval)', '', s))
    for _, _, arms in rows_def:
        for arm in arms:
            if arm in err:
                e = err[arm]; lines.append('%-22s %28s %6.1f' % (arm, ' / '.join(f'{x:5.1f}' for x in e['per_point']), e['all']['mean']))
        lines.append('')
    open(f'{a.study_dir}/study_summary.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))


if __name__ == '__main__':
    main()
