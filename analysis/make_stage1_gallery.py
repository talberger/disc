"""Browsable gallery of a stage-1 run over all bears: one row per bear, one back-projection per arm with its score, sortable in the browser
(Tal, 2026-11-11: "the 3 GT points do not always tell the whole story, a back-projection shows the problem").
Output = one HTML next to the data (images by relative path, nothing copied); click a column to sort by its score, a "diff" button to sort by
the difference of two arms, type an id to filter.
  python analysis/make_stage1_gallery.py --root data/densepose_lvis/lifted_full --out data/densepose_lvis/lifted_full/summary/stage1_tri_gallery.html
--col "label|png under lvis<i>/ ({i} = id)|eval json under lvis<i>/|arm" (repeatable; json / arm empty = no score). SHIC's score: summary.txt.
"""
import argparse, glob, json, os

COLS = ['SHIC|backproj/lvis{i}_SHIC_backproj.png||', '2D|backproj/lvis{i}_2d_stage1_backproj.png|stage1_ray/eval_all.json|2d_stage1',
        'no amodal|backproj/lvis{i}_lifted_ray_backproj.png|stage1_ray/eval_all.json|lifted_ray',
        'amodal, before the fix|backproj/lvis{i}_lifted_amodal_backproj.png|stage1_ray/eval_all.json|lifted_amodal',
        'amodal, after the fix|stage1_tri/backproj/lvis{i}_lifted_amodal_backproj.png|stage1_tri/eval_all.json|lifted_amodal']
DIFFS = ['amodal, after the fix|amodal, before the fix', 'amodal, after the fix|2D', 'amodal, after the fix|SHIC', 'amodal, after the fix|no amodal']

PAGE = """<!doctype html><meta charset="utf-8"><title>__TITLE__</title>
<style>
body{font:14px -apple-system,Helvetica,sans-serif;margin:12px;background:#fafafa;color:#111}
#bar{position:sticky;top:0;background:#fafafa;padding:6px 0;border-bottom:1px solid #ccc;z-index:2}
button{font:13px inherit;margin:2px;padding:3px 8px;cursor:pointer} button.on{background:#1565c0;color:#fff}
.row{display:grid;grid-template-columns:110px repeat(__N__,1fr);gap:6px;align-items:start;padding:6px 0;border-bottom:1px solid #ddd}
.row img{width:100%;height:auto;display:block} .cap{font-size:12px;margin-bottom:2px} .id{font-weight:600} .best{color:#1b7a1b;font-weight:600}
.neg{color:#1b7a1b} .pos{color:#b71c1c} #stat{margin-left:10px;color:#555}
</style>
<div id="bar"><b>__TITLE__</b> &nbsp; sort: <span id="btns"></span> <input id="q" placeholder="id" size="8"><span id="stat"></span></div><div id="rows"></div>
<script>
const COLS = __COLS__, DIFFS = __DIFFS__, DATA = __DATA__;
let key = null, desc = false;
const val = (r, k) => k.includes('|') ? r.s[k.split('|')[0]] - r.s[k.split('|')[1]] : r.s[k];
const f1 = x => x == null || isNaN(x) ? '-' : x.toFixed(1);
function draw() {
  const q = document.getElementById('q').value.trim();
  let R = DATA.filter(r => !q || r.id.includes(q));
  if (key) R = R.slice().sort((a, b) => (desc ? -1 : 1) * (val(a, key) - val(b, key)));
  const scored = COLS.filter(c => DATA[0].s[c] != null);
  document.getElementById('stat').textContent = R.length + ' bears | mean: ' + scored.map(c => c + ' ' + f1(R.reduce((t, r) => t + r.s[c], 0) / R.length)).join(' | ');
  document.getElementById('rows').innerHTML = R.map(r => {
    const best = Math.min(...scored.map(c => r.s[c]));
    const d = DIFFS.map(k => { const v = val(r, k); return `<div class="${v < -2 ? 'neg' : v > 2 ? 'pos' : ''}">${k.split('|').map(s => s.replace('amodal, ', '').replace(' the fix', '')).join(' - ')}: ${v > 0 ? '+' : ''}${f1(v)}</div>`; }).join('');
    return `<div class="row"><div><div class="id">lvis${r.id}</div><div class="cap">${d}</div></div>` + COLS.map(c =>
      `<div><div class="cap"><span class="${r.s[c] === best ? 'best' : ''}">${c} ${f1(r.s[c])}</span>${r.p[c] ? ' (' + r.p[c].map(f1).join(' / ') + ')' : ''}</div><img loading="lazy" src="${r.img[c]}"></div>`).join('') + '</div>';
  }).join('');
  document.querySelectorAll('#btns button').forEach(b => { b.className = b.dataset.k === key ? 'on' : ''; b.textContent = b.dataset.t + (b.dataset.k === key ? (desc ? ' ↓' : ' ↑') : ''); });
}
const btns = document.getElementById('btns');
[['id', null]].concat(COLS.filter(c => DATA[0].s[c] != null).map(c => [c, c]), DIFFS.map(k => ['diff: ' + k.split('|').join(' - '), k])).forEach(([t, k]) => {
  const b = document.createElement('button'); b.dataset.t = t; b.dataset.k = k; b.onclick = () => { desc = key === k ? !desc : false; key = k; draw(); }; btns.appendChild(b); });
document.querySelectorAll('#btns button')[0].dataset.k = ''; document.querySelectorAll('#btns button')[0].onclick = () => { key = null; draw(); };
document.getElementById('q').oninput = draw; draw();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='the folder of the lvis<i>/ folders'); ap.add_argument('--out', required=True)
    ap.add_argument('--col', action='append', help='label|png|eval json|arm; default: SHIC, 2D, no amodal, amodal before / after the fix')
    ap.add_argument('--diff', action='append', help='label a|label b: a sort button + a per-bear line for score(a) - score(b)')
    ap.add_argument('--title', default='stage 1, 132 bears (soft-snap mean of the GT points, lower = better)')
    a = ap.parse_args()
    cols = [c.split('|') for c in (a.col or COLS)]; names = [c[0] for c in cols]; diffs = [d for d in (a.diff or DIFFS) if all(s in names for s in d.split('|'))]
    shic = {l.split()[0]: float(l.split()[1]) for l in open(os.path.join(a.root, 'summary/summary.txt')) if l.split() and l.split()[0].isdigit()}
    rel = os.path.relpath(a.root, os.path.dirname(os.path.abspath(a.out))); data = []
    for d in sorted(glob.glob(os.path.join(a.root, 'lvis*')), key=lambda d: int(os.path.basename(d)[4:])):
        i = os.path.basename(d)[4:]; r = dict(id=i, s={}, p={}, img={}); cache = {}
        for nm, png, js, arm in cols:
            if not os.path.exists(os.path.join(d, png.format(i=i))): break
            r['img'][nm] = f'{rel}/lvis{i}/' + png.format(i=i)
            if js:
                if not os.path.exists(os.path.join(d, js)): break
                s = cache.setdefault(js, json.load(open(os.path.join(d, js)))['arms'])[arm]['soft_snap']; r['s'][nm] = s['all']['mean']; r['p'][nm] = s['per_point']
            elif nm == 'SHIC': r['s'][nm] = shic.get(i)
        else: data.append(r)
    page = PAGE.replace('__TITLE__', a.title).replace('__N__', str(len(cols))).replace('__COLS__', json.dumps(names)).replace('__DIFFS__', json.dumps(diffs)).replace('__DATA__', json.dumps(data))
    open(a.out, 'w').write(page); print(f'{len(data)} bears, {len(cols)} columns -> {a.out}')


if __name__ == '__main__':
    main()
