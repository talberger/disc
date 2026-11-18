"""A page per class of the full alpha run (Tal, 2026-11-18): every instance as image | SHIC | ours alpha 0.5 | ours alpha 1, with the
scores, the painted canonical mesh on top (the key to the colours). make_shic_vs_ours_page.py (bears, one arm) with two alphas and any class.
Two steps, as the images live on the PVC and the class meshes (.ply) on the Mac:
  server: python analysis/make_class_alpha_page.py --cls horse --strips --out <dir>   -> <dir>/img/lvis<i>.webp + <dir>/data.json
  Mac:    python analysis/make_class_alpha_page.py --cls horse --page --out <dir>     -> <dir>/key_*.webp + <dir>/index.html
index.html is page CONTENT only (the Artifact tool wraps it).
"""
import argparse, glob, json, os
import numpy as np
from make_shic_vs_ours_page import VIEWS, key_views

W, GAP = 300, 8   # panel width / gap, px
R = 'data/densepose_lvis'
CLS = {'bear': ('lifted_full', 'runs_full_poly', 'bear_shic_normalized_mesh_checker16_uv_color.ply', 'backproj'),
       'horse': ('lifted_horse', 'runs_horse_poly', 'horse_mesh_checker16_uv_color.ply', 'stage1_tri/backproj'),
       'elephant': ('lifted_elephant', 'runs_elephant_poly', 'elephant_mesh_checker16_uv_color.ply', 'stage1_tri/backproj')}
ARMS = (('o', 'lifted_amodal', 'lvis{i}_lifted_amodal_backproj.png'), ('o1', 'lifted_amodal_a1', 'lvis{i}_lifted_amodal_a1_backproj.png'))

PAGE = """<title>__TITLE__: ours vs SHIC</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* layout: one reading column for the summary and the colour key, then a grid of instance cards (image | SHIC | alpha 0.5 | alpha 1) */
:root { --bg: #f2f4f7; --surface: #ffffff; --fg: #17212b; --muted: #5a6775; --line: #d4dae1; --accent: #0b6b6e; --good: #17794a;
  --sans: "IBM Plex Sans", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #10151b; --surface: #19212a; --fg: #e5eaf0; --muted: #98a5b3; --line: #2b3641; --accent: #62c8c4; --good: #62cf92; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #10151b; --surface: #19212a; --fg: #e5eaf0; --muted: #98a5b3; --line: #2b3641; --accent: #62c8c4; --good: #62cf92; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.55 var(--sans); padding-block: 28px 48px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.wrap { max-width: 1500px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
.read { max-width: 110ch; display: flex; flex-direction: column; gap: 10px; }
h1 { font-size: 26px; line-height: 1.2; font-weight: 600; margin: 0; text-wrap: balance; }
p { margin: 0; } .muted { color: var(--muted); }
table { border-collapse: collapse; align-self: flex-start; font-variant-numeric: tabular-nums; }
th, td { padding: 4px 0 4px 28px; text-align: right; } th:first-child, td:first-child { text-align: left; padding-left: 0; } th { font-weight: 500; color: var(--muted); border-bottom: 1px solid var(--line); }
td.num { font-family: var(--mono); }
.key { display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: flex-end; margin-top: -14px; }
.key figure { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 2px; } .key img { height: auto; max-width: 100%; display: block; }
.key figcaption { font-size: 12px; color: var(--muted); }
#btns { display: contents; }
.bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.bar button { font: 500 13px var(--sans); color: var(--fg); background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: 5px 10px; cursor: pointer; }
.bar button[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); } .bar button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 560px), 1fr)); gap: 22px 20px; }
.card { min-width: 0; display: flex; flex-direction: column; gap: 4px; border-top: 1px solid var(--line); padding-top: 8px; }
.card .head { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; } .card .id { font-weight: 600; } .card .d { font-family: var(--mono); color: var(--muted); }
.card .cap { display: grid; grid-template-columns: repeat(4, 1fr); column-gap: __GAPPCT__%; font-size: 13px; color: var(--muted); } .cap b { font-family: var(--mono); font-weight: 400; color: var(--fg); }
.cap .win, .cap .win b { color: var(--good); font-weight: 600; }
.card img { width: 100%; height: auto; display: block; }
</style>
<div class="wrap">
  <div class="read">
    <h1>Ours vs SHIC on __N__ LVIS __TITLE__</h1>
    <p class="muted">Each card: image, SHIC, ours at read-time alpha 0.5, ours at alpha 1 (one training, two read-outs). Error = soft-snap geodesic error, mean over the GT points; lower is better.</p>
    <table>
      <tr><th></th><th>SHIC</th><th>ours α 0.5</th><th>ours α 1</th></tr>
      <tr><td>mean error</td><td class="num">__SM__</td><td class="num">__OM__</td><td class="num">__O1M__</td></tr>
      <tr><td>median error</td><td class="num">__SMED__</td><td class="num">__OMED__</td><td class="num">__O1MED__</td></tr>
      <tr><td>better than SHIC by more than 2 (instances)</td><td></td><td class="num">__WIN__</td><td class="num">__WIN1__</td></tr>
      <tr><td>worse than SHIC by more than 2</td><td></td><td class="num">__LOSE__</td><td class="num">__LOSE1__</td></tr>
    </table>
  </div>
  <div class="key">__KEY__</div>
  <div class="bar" role="group" aria-label="Sort the instances"><span class="muted">Sort by</span><span id="btns"></span><span class="muted" id="count"></span></div>
  <div class="grid" id="grid"></div>
</div>
<script>
const DATA = __DATA__;
const SORTS = [['id', 'image id', r => r.n], ['d', 'α 0.5 − SHIC', r => r.o - r.s], ['d1', 'α 1 − SHIC', r => r.o1 - r.s], ['a', 'α 1 − α 0.5', r => r.o1 - r.o],
               ['s', 'SHIC', r => r.s], ['o', 'α 0.5', r => r.o], ['o1', 'α 1', r => r.o1]];
let key = 'id', desc = false;
const f1 = x => x.toFixed(1), sg = d => (d > 0 ? '+' : d < 0 ? '−' : '') + f1(Math.abs(d));
function draw() {
  const get = SORTS.find(s => s[0] === key)[2], R = DATA.slice().sort((a, b) => (desc ? -1 : 1) * (get(a) - get(b)));
  document.getElementById('grid').innerHTML = R.map(r => {
    const best = Math.min(r.s, r.o, r.o1), w = v => v === best ? 'win' : '';
    return `<div class="card"><div class="head"><span class="id">lvis ${r.id}</span><span class="d">α 0.5 − SHIC ${sg(r.o - r.s)} · α 1 − SHIC ${sg(r.o1 - r.s)}</span></div>` +
      `<div class="cap"><span>image</span><span class="${w(r.s)}">SHIC <b>${f1(r.s)}</b></span><span class="${w(r.o)}">α 0.5 <b>${f1(r.o)}</b></span><span class="${w(r.o1)}">α 1 <b>${f1(r.o1)}</b></span></div>` +
      `<img loading="lazy" width="__SW__" height="${r.h}" alt="lvis ${r.id}: image, SHIC, ours alpha 0.5, ours alpha 1" src="img/lvis${r.id}.webp"></div>`;
  }).join('');
  document.querySelectorAll('#btns button').forEach(b => { const on = b.dataset.k === key; b.setAttribute('aria-pressed', on); b.textContent = b.dataset.t + (on ? (desc ? ' ↓' : ' ↑') : ''); });
  document.getElementById('count').textContent = R.length + ' instances, green = the best of the three';
}
SORTS.forEach(([k, t]) => { const b = document.createElement('button'); b.id = 'sort-' + k; b.dataset.k = k; b.dataset.t = t; b.onclick = () => { desc = key === k ? !desc : false; key = k; draw(); }; document.getElementById('btns').appendChild(b); });
draw();
</script>
"""


def strips(cls, out):
    from PIL import Image
    root, src, _, shic_dir = CLS[cls]; root, src = f'{R}/{root}', f'{R}/{src}'
    if cls == 'bear':
        shic = {l.split()[0]: float(l.split()[1]) for l in open(f'{root}/summary/summary.txt') if l.split() and l.split()[0].isdigit()}
    else:
        shic = {k: float(v) for k, v in json.load(open(f'{R}/eval_shic_{cls}/results.json'))['bbox']['per_instance'].items()}
    os.makedirs(f'{out}/img', exist_ok=True); data = []
    for js in sorted(glob.glob(f'{root}/lvis*/stage1_full/eval_all.json'), key=lambda p: int(p.split('/')[-3][4:])):
        d = os.path.dirname(os.path.dirname(js)); i = os.path.basename(d)[4:]; arms = json.load(open(js))['arms']
        ims = [f'{src}/lvis{i}/lvis{i}.png', f'{d}/{shic_dir}/lvis{i}_SHIC_backproj.png'] + [f'{d}/stage1_full/backproj/{p.format(i=i)}' for _, _, p in ARMS]
        if i not in shic or not all(os.path.exists(p) for p in ims):
            print('skipped', i); continue
        ims = [Image.open(p).convert('RGB') for p in ims]
        h = round(W * ims[0].height / ims[0].width); strip = Image.new('RGBA', (4 * W + 3 * GAP, h), (0, 0, 0, 0))
        for k, im in enumerate(ims): strip.paste(im.resize((W, h), Image.LANCZOS), (k * (W + GAP), 0))
        strip.save(f'{out}/img/lvis{i}.webp', quality=78)
        data.append(dict(id=i, n=int(i), s=round(shic[i], 2), h=h, **{k: round(arms[a]['soft_snap']['all']['mean'], 2) for k, a, _ in ARMS}))
    json.dump(data, open(f'{out}/data.json', 'w'))
    print(f'{cls}: {len(data)} instances -> {out}')


def page(cls, out):
    data = json.load(open(f'{out}/data.json'))
    kw = key_views(f'demo/shic/colored_mesh/{CLS[cls][2]}', out)
    S, O, O1 = (np.array([r[k] for r in data]) for k in ('s', 'o', 'o1'))
    rep = dict(TITLE=cls + 's', N=len(data), SM=f'{S.mean():.1f}', OM=f'{O.mean():.1f}', O1M=f'{O1.mean():.1f}',
               SMED=f'{np.median(S):.1f}', OMED=f'{np.median(O):.1f}', O1MED=f'{np.median(O1):.1f}',
               WIN=int((O < S - 2).sum()), LOSE=int((O > S + 2).sum()), WIN1=int((O1 < S - 2).sum()), LOSE1=int((O1 > S + 2).sum()),
               GAPPCT=f'{100 * GAP / (4 * W + 3 * GAP):.2f}', SW=4 * W + 3 * GAP,
               KEY=''.join(f'<figure><img src="key_{k}.webp" width="{round(0.55 * kw[k])}" alt="painted mesh, {v[0]}"><figcaption>{v[0]}</figcaption></figure>' for k, v in enumerate(VIEWS)),
               DATA=json.dumps(data))
    html = PAGE
    for k, v in rep.items(): html = html.replace(f'__{k}__', str(v))
    open(f'{out}/index.html', 'w').write(html)
    print(f"{cls}: {len(data)} | mean SHIC {rep['SM']} | a0.5 {rep['OM']} | a1 {rep['O1M']} -> {out}/index.html")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cls', required=True, choices=list(CLS)); ap.add_argument('--out', required=True)
    ap.add_argument('--strips', action='store_true'); ap.add_argument('--page', action='store_true')
    a = ap.parse_args()
    if a.strips: strips(a.cls, a.out)
    if a.page: page(a.cls, a.out)
