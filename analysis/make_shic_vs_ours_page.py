"""A page to share (an Artifact: index.html + images next to it): every bear as image | SHIC | ours, with the two scores, and on top the
painted canonical mesh, the key to the back-projection colours (Tal, 2026-11-11, for Itai).
  python analysis/make_shic_vs_ours_page.py --out data/densepose_lvis/lifted_full/summary/share_shic_vs_ours
--ours "<png under lvis<i>/ ({i} = id)>|<eval json under lvis<i>/>|<arm>": the arm shown as "ours" (default: amodal + the double-shell fix).
index.html is page CONTENT only (the Artifact tool wraps it); bears/lvis<i>.webp = the three panels side by side, transparent gaps.
"""
import argparse, glob, json, os
import numpy as np

VIEWS = (('side', (1, 0, 0), (0, 1, 0)), ('other side', (-1, 0, 0), (0, 1, 0)), ('front', (0, 0, -1), (0, 1, 0)), ('back', (0, 0, 1), (0, 1, 0)), ('top', (0, -1, 0), (0, 0, 1)))
W, GAP = 300, 8   # panel width / gap of a bear's strip, px

PAGE = """<title>Bears: ours vs SHIC</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* layout: one reading column for the summary and the colour key, then a grid of bear cards (image | SHIC | ours) that fills the width */
:root { --bg: #f2f4f7; --surface: #ffffff; --fg: #17212b; --muted: #5a6775; --line: #d4dae1; --accent: #0b6b6e; --good: #17794a;
  --sans: "IBM Plex Sans", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #10151b; --surface: #19212a; --fg: #e5eaf0; --muted: #98a5b3; --line: #2b3641; --accent: #62c8c4; --good: #62cf92; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #10151b; --surface: #19212a; --fg: #e5eaf0; --muted: #98a5b3; --line: #2b3641; --accent: #62c8c4; --good: #62cf92; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.55 var(--sans); padding-block: 28px 48px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.wrap { max-width: 1500px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
.read { max-width: 68ch; display: flex; flex-direction: column; gap: 10px; }
h1 { font-size: 26px; line-height: 1.2; font-weight: 600; margin: 0; text-wrap: balance; }
h2 { font-size: 17px; font-weight: 600; margin: 0; }
p { margin: 0; } .muted { color: var(--muted); }
table { border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 4px 18px 4px 0; text-align: right; } th:first-child, td:first-child { text-align: left; } th { font-weight: 500; color: var(--muted); border-bottom: 1px solid var(--line); }
td.num { font-family: var(--mono); }
.key { display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: flex-end; margin-top: -14px; }
.key figure { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 2px; } .key img { height: auto; max-width: 100%; display: block; }
.key figcaption { font-size: 12px; color: var(--muted); }
.bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.bar button { font: 500 13px var(--sans); color: var(--fg); background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: 5px 10px; cursor: pointer; }
.bar button[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); } .bar button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 440px), 1fr)); gap: 22px 20px; }
.bear { min-width: 0; display: flex; flex-direction: column; gap: 4px; border-top: 1px solid var(--line); padding-top: 8px; }
.bear .head { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; } .bear .id { font-weight: 600; } .bear .d { font-family: var(--mono); color: var(--muted); }
.bear .cap { display: grid; grid-template-columns: repeat(3, 1fr); column-gap: __GAPPCT__%; font-size: 13px; color: var(--muted); } .cap b { font-family: var(--mono); font-weight: 400; color: var(--fg); }
.cap .win, .cap .win b { color: var(--good); font-weight: 600; } .bear .d.win { color: var(--good); font-weight: 600; }
.bear img { width: 100%; height: auto; display: block; }
</style>
<div class="wrap">
  <div class="read">
    <h1>Ours vs SHIC on __N__ LVIS bears</h1>
    <p class="muted">__DATE__. Ours = stage 1 only, trained with geodesic distances taken from the lifted 3D mesh of the amodal-completed bear, with the pixel-to-mesh mapping fix (pixels map to the outer skin of the lifted mesh only). One seed.</p>
    <table>
      <tr><th>error, lower is better</th><th>SHIC</th><th>ours</th></tr>
      <tr><td>mean</td><td class="num">__SM__</td><td class="num">__OM__</td></tr>
      <tr><td>median</td><td class="num">__SMED__</td><td class="num">__OMED__</td></tr>
    </table>
    <p>Bear by bear, counting a difference above 2 as a real one: ours is better on __WIN__, the two are the same on __TIE__, SHIC is better on __LOSE__.</p>
    <p class="muted">Error = geodesic distance on the canonical mesh between the predicted and the annotated point, averaged over the image's annotated points (__PTS__ per bear).</p>
  </div>
  <div class="read">
    <h2>How to read the colours</h2>
    <p>The canonical SHIC bear mesh is painted with a fixed patchwork, shown here. Every pixel of an image takes the colour of the mesh point it is matched to. A good result looks like the patchwork lying on the bear: whole patches, in the same order as on the mesh. Stripes, speckle and scrambled patches are wrong matches. The patchwork has 8 colours that repeat, so compare the pattern, not a single colour.</p>
  </div>
  <div class="key">__KEY__</div>
  <div class="bar" role="group" aria-label="Sort the bears"><span class="muted">Sort by</span><span id="btns"></span><span class="muted" id="count"></span></div>
  <div class="grid" id="grid"></div>
</div>
<script>
const DATA = __DATA__;
const SORTS = [['id', 'image id', r => r.n], ['d', 'ours − SHIC', r => r.o - r.s], ['o', 'ours', r => r.o], ['s', 'SHIC', r => r.s]];
let key = 'id', desc = false;
const f1 = x => x.toFixed(1);
function draw() {
  const get = SORTS.find(s => s[0] === key)[2], R = DATA.slice().sort((a, b) => (desc ? -1 : 1) * (get(a) - get(b)));
  document.getElementById('grid').innerHTML = R.map(r => {
    const d = r.o - r.s, ow = d < -2, sw = d > 2;
    return `<div class="bear"><div class="head"><span class="id">lvis ${r.id}</span><span class="d${ow ? ' win' : ''}">ours − SHIC ${d > 0 ? '+' : d < 0 ? '−' : ''}${f1(Math.abs(d))}</span></div>` +
      `<div class="cap"><span>image</span><span class="${sw ? 'win' : ''}">SHIC <b>${f1(r.s)}</b></span><span class="${ow ? 'win' : ''}">ours <b>${f1(r.o)}</b></span></div>` +
      `<img loading="lazy" width="__SW__" height="${r.h}" alt="lvis ${r.id}: image, SHIC, ours" src="bears/lvis${r.id}.webp"></div>`;
  }).join('');
  document.querySelectorAll('#btns button').forEach(b => { const on = b.dataset.k === key; b.setAttribute('aria-pressed', on); b.textContent = b.dataset.t + (on ? (desc ? ' ↓' : ' ↑') : ''); });
  document.getElementById('count').textContent = R.length + ' bears, green = the better of the two';
}
SORTS.forEach(([k, t]) => { const b = document.createElement('button'); b.id = 'sort-' + k; b.dataset.k = k; b.dataset.t = t; b.onclick = () => { desc = key === k ? !desc : false; key = k; draw(); }; document.getElementById('btns').appendChild(b); });
draw();
</script>
"""


def key_views(ply, out_dir, res=520):
    """The painted canonical mesh from VIEWS (orthographic, one scale), transparent background -> out_dir/key_<k>.webp."""
    import open3d as o3d
    from PIL import Image
    m = o3d.io.read_triangle_mesh(ply); V, F, C = np.asarray(m.vertices), np.asarray(m.triangles), np.asarray(m.vertex_colors)
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(V.astype(np.float32), F.astype(np.uint32))
    c = (V.min(0) + V.max(0)) / 2; ext = np.ptp(V, 0).max() * 1.06; g = (np.arange(res) + 0.5) / res - 0.5; gx, gy = np.meshgrid(g * ext, -g * ext)
    sizes = []
    for k, (nm, d, up) in enumerate(VIEWS):
        d = np.array(d, float); r = np.cross(d, np.array(up, float)); u = np.cross(r, d); o = c - 3 * d + gx.ravel()[:, None] * r + gy.ravel()[:, None] * u
        h = sc.cast_rays(o3d.core.Tensor(np.c_[o, np.tile(d, (len(o), 1))].astype(np.float32))); ok = np.isfinite(h['t_hit'].numpy())
        f = h['primitive_ids'].numpy()[ok]; uv = h['primitive_uvs'].numpy()[ok]; n = h['primitive_normals'].numpy()[ok]
        col = C[F[f]][np.arange(len(f)), np.c_[1 - uv.sum(1), uv].argmax(1)]   # the nearest corner's colour: flat patches, no blending
        img = np.zeros((res * res, 4)); img[ok, :3] = col * (0.55 + 0.45 * np.abs(n @ d))[:, None]; img[ok, 3] = 1; img = img.reshape(res, res, 4)
        ys, xs = np.where(img[:, :, 3] > 0); img = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        Image.fromarray((img * 255).astype(np.uint8)).save(os.path.join(out_dir, f'key_{k}.webp'), quality=85); sizes.append(img.shape[1])
    return sizes   # widths, px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='data/densepose_lvis/lifted_full'); ap.add_argument('--src', default='data/densepose_lvis/runs_full_poly', help='lvis<i>/lvis<i>.png = the image')
    ap.add_argument('--ours', default='stage1_tri/backproj/lvis{i}_lifted_amodal_backproj.png|stage1_tri/eval_all.json|lifted_amodal')
    ap.add_argument('--ply', default='demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.ply'); ap.add_argument('--date', default='11 Nov 2026')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    from PIL import Image
    os.makedirs(os.path.join(a.out, 'bears'), exist_ok=True); png, js, arm = a.ours.split('|'); data = []; npts = set()
    shic = {l.split()[0]: float(l.split()[1]) for l in open(os.path.join(a.root, 'summary/summary.txt')) if l.split() and l.split()[0].isdigit()}
    for d in sorted(glob.glob(os.path.join(a.root, 'lvis*')), key=lambda d: int(os.path.basename(d)[4:])):
        i = os.path.basename(d)[4:]; s = json.load(open(os.path.join(d, js)))['arms'][arm]['soft_snap']; npts.add(len(s['per_point']))
        ims = [Image.open(p).convert('RGB') for p in (f'{a.src}/lvis{i}/lvis{i}.png', f'{d}/backproj/lvis{i}_SHIC_backproj.png', os.path.join(d, png.format(i=i)))]
        h = round(W * ims[0].height / ims[0].width); strip = Image.new('RGBA', (3 * W + 2 * GAP, h), (0, 0, 0, 0))
        for k, im in enumerate(ims): strip.paste(im.resize((W, h), Image.LANCZOS), (k * (W + GAP), 0))
        strip.save(os.path.join(a.out, 'bears', f'lvis{i}.webp'), quality=80); data.append(dict(id=i, n=int(i), s=shic[i], o=round(s['all']['mean'], 2), h=h))
    kw = key_views(a.ply, a.out)
    S, O = np.array([r['s'] for r in data]), np.array([r['o'] for r in data])
    rep = dict(N=len(data), DATE=a.date, SM=f'{S.mean():.1f}', OM=f'{O.mean():.1f}', SMED=f'{np.median(S):.1f}', OMED=f'{np.median(O):.1f}', WIN=int((O < S - 2).sum()),
               LOSE=int((O > S + 2).sum()), TIE=int((abs(O - S) <= 2).sum()), PTS=f'{min(npts)} to {max(npts)}', GAPPCT=f'{100 * GAP / (3 * W + 2 * GAP):.2f}', SW=3 * W + 2 * GAP,
               KEY=''.join(f'<figure><img src="key_{k}.webp" width="{round(0.55 * kw[k])}" alt="painted mesh, {v[0]}"><figcaption>{v[0]}</figcaption></figure>' for k, v in enumerate(VIEWS)), DATA=json.dumps(data))
    page = PAGE
    for k, v in rep.items(): page = page.replace(f'__{k}__', str(v))
    open(os.path.join(a.out, 'index.html'), 'w').write(page)
    files = sorted(glob.glob(os.path.join(a.out, 'bears', '*.webp')) + glob.glob(os.path.join(a.out, 'key_*.webp')))
    print(f"{len(data)} bears | SHIC {rep['SM']} / {rep['SMED']} | ours {rep['OM']} / {rep['OMED']} | {rep['WIN']} / {rep['TIE']} / {rep['LOSE']} | points per bear {rep['PTS']} | "
          f"{len(files)} images, {sum(os.path.getsize(f) for f in files) / 1e6:.1f} MB -> {a.out}")


if __name__ == '__main__':
    main()
