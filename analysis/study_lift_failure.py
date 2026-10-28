"""Why did the LIFTED teacher not help where it should have? (Tal, 2026-10-28; bears 171627, 117682 of the 20-bear subset)
One figure per instance:
  row 1: photo + GT points | Pixal3D depth of the visible surface (pix_depth) | the lifted mesh from the SIDE | from ABOVE
         (a frontal bear squashed in depth shows up in the side / top views)
  row 2: "stretch" map = per pixel, mean over centres of lifted distance / 2D distance (each normalised by its own diameter):
         red = the lift puts the pixel FARTHER from the rest than the 2D teacher did, blue = closer |
         scatter 2D vs lifted (normalised) for a random sample of (centre, pixel) pairs, same segment vs other segment |
         per-GT-point error of each arm (multi_eval.json)
Usage: python analysis/study_lift_failure.py --src <run dir> --tag lvis171627 --lift_path <lift.pth> --lifted_table <table.pth> \
           --eval_json <lifted/<tag>/multi_eval.json> --out_png <png>"""
import argparse, json
import numpy as np, torch
from PIL import Image

ARMS = [('zs', 'ZS'), ('2d_stage1', '2D stage 1'), ('2d_stage2', '2D two-stage'), ('lifted_stage1', 'lifted stage 1'),
        ('lifted_stage2', 'lifted two-stage'), ('lifted_perseg', 'lifted per-seg'), ('lifted_hybrid', 'lifted hybrid')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True); ap.add_argument('--tag', required=True); ap.add_argument('--lift_path', required=True)
    ap.add_argument('--lifted_table', required=True); ap.add_argument('--eval_json', required=True); ap.add_argument('--out_png', required=True)
    ap.add_argument('--n_pairs', type=int, default=20000)
    a = ap.parse_args(); S, T = a.src, a.tag
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    photo = np.array(Image.open(f'{S}/{T}.png').convert('RGB')); mask = torch.load(f'{S}/{T}_mask.pth').numpy().astype(bool)
    gt = torch.load(f'{S}/{T}_gt.pth', map_location='cpu'); pts = list(zip(gt['rows'].tolist(), gt['cols'].tolist()))
    seg = torch.as_tensor(torch.load(f'{S}/{T}_fine_segments.pth')).numpy()
    lift = torch.load(a.lift_path, map_location='cpu'); V = lift['vertices'].numpy()
    t2 = torch.load(f'{S}/{T}_mask_geo_table_2d_seed0.pth', map_location='cpu'); tl = torch.load(a.lifted_table, map_location='cpu')
    ev = json.load(open(a.eval_json))['arms']

    safe = t2['geodesic_safe_mask'].numpy().astype(bool); p2n = np.asarray(t2['pixel_to_node']); coords = np.asarray(t2['coords'])
    rows, cols = np.nonzero(safe); nodes = p2n[rows, cols]
    d2 = float(t2.get('true_diameter_2d') or t2['diagonal']); d3 = float(tl['true_diameter_2d'])
    A = t2['table'].numpy()[:, nodes] / d2; B = tl['table'].numpy()[:, nodes] / d3          # [centres, mask pixels], pixel order = rows/cols
    ok = A > 0.02                                                                            # skip the centre's own neighbourhood
    ratio = np.where(ok, B / np.maximum(A, 1e-6), np.nan)
    stretch = np.full(safe.shape, np.nan); stretch[rows, cols] = np.exp(np.nanmean(np.log(ratio), 0))
    rng = np.random.RandomState(0); ci = rng.randint(0, A.shape[0], a.n_pairs); pj = rng.randint(0, A.shape[1], a.n_pairs)
    same = seg[coords[ci, 0], coords[ci, 1]] == seg[rows[pj], cols[pj]]

    fig, ax = plt.subplots(2, 4, figsize=(22, 10.5))
    ax[0, 0].imshow(photo); ax[0, 0].imshow(np.where(mask, np.nan, 0.0), cmap='gray', alpha=0.5, vmin=0, vmax=1)
    for k, (r, c) in enumerate(pts):
        ax[0, 0].plot(c, r, 'o', ms=11, mfc='yellow', mec='k'); ax[0, 0].annotate(str(k + 1), (c + 7, r - 7), color='yellow', fontsize=14, weight='bold')
    ax[0, 0].set_title(f'{T}: photo, GT points'); ax[0, 0].axis('off')
    dep = lift['pix_depth'].numpy().copy(); dep[~np.isfinite(dep)] = np.nan
    im = ax[0, 1].imshow(dep, cmap='viridis'); plt.colorbar(im, ax=ax[0, 1], fraction=0.046)
    ax[0, 1].set_title(f'Pixal3D depth of the visible surface (IoU {float(lift.get("iou", float("nan"))):.2f})'); ax[0, 1].axis('off')
    sub = rng.choice(len(V), min(30000, len(V)), replace=False)
    ax[0, 2].scatter(V[sub, 1], V[sub, 2], s=0.3, c=V[sub, 0], cmap='coolwarm'); ax[0, 2].set_aspect('equal')
    ax[0, 2].set_title('mesh from the SIDE (camera on the left; colour = image x)'); ax[0, 2].set_xlabel('depth'); ax[0, 2].set_ylabel('up')
    ax[0, 3].scatter(V[sub, 0], V[sub, 1], s=0.3, c=V[sub, 2], cmap='coolwarm'); ax[0, 3].set_aspect('equal')
    ax[0, 3].set_title('mesh from ABOVE (camera at the bottom; colour = height)'); ax[0, 3].set_xlabel('image x'); ax[0, 3].set_ylabel('depth')
    ext = np.ptp(V, 0); fig.text(0.01, 0.51, f'mesh extent x / depth / up = {ext[0]:.2f} / {ext[1]:.2f} / {ext[2]:.2f} (depth/width {ext[1] / ext[0]:.2f})',
                                 fontsize=12, family='monospace')

    ax[1, 0].imshow(photo, alpha=0.35); im = ax[1, 0].imshow(np.log2(stretch), cmap='RdBu_r', vmin=-1, vmax=1)
    cb = plt.colorbar(im, ax=ax[1, 0], fraction=0.046); cb.set_label('log2(lifted / 2D), mean over centres')
    ax[1, 0].set_title('stretch: red = farther with the lift, blue = closer'); ax[1, 0].axis('off')
    x, y = A[ci, pj], B[ci, pj]
    ax[1, 1].scatter(x[~same], y[~same], s=1, alpha=0.3, c='tab:orange', label='other segment')
    ax[1, 1].scatter(x[same], y[same], s=1, alpha=0.3, c='tab:blue', label='same segment')
    ax[1, 1].plot([0, 1], [0, 1], 'k--', lw=1); ax[1, 1].set_xlim(0, 1.05); ax[1, 1].set_ylim(0, 1.05)
    rs = np.corrcoef(x, y)[0, 1]; ax[1, 1].set_xlabel('2D geodesic / diameter'); ax[1, 1].set_ylabel('lifted geodesic / diameter')
    ax[1, 1].set_title(f'(centre, pixel) pairs, Pearson r = {rs:.2f}'); ax[1, 1].legend(markerscale=8, loc='upper left')

    arms = [(k, n) for k, n in ARMS if k in ev]; npt = len(pts); w = 0.8 / max(1, len(arms))
    for j, (k, n) in enumerate(arms):
        e = ev[k]['soft_snap']['per_point']
        ax[1, 2].bar(np.arange(npt) + j * w, e, w, label=f'{n} ({np.mean(e):.1f})')
    ax[1, 2].set_xticks(np.arange(npt) + 0.4 - w / 2); ax[1, 2].set_xticklabels([f'pt {k + 1}' for k in range(npt)])
    ax[1, 2].set_ylabel('soft-snap geodesic error (228)'); ax[1, 2].legend(fontsize=9); ax[1, 2].set_title('error per GT point (mean in the legend)')

    ax[1, 3].axis('off')
    lines = [f'{"pair":8s} {"2D":>6s} {"lifted":>7s}']
    for i in range(npt):
        for j in range(i + 1, npt):
            ci_ = int(np.argmin((coords[:, 0] - pts[i][0]) ** 2 + (coords[:, 1] - pts[i][1]) ** 2))
            n_ = p2n[pts[j][0], pts[j][1]]
            if n_ >= 0:
                lines.append(f'pt{i + 1}-pt{j + 1}  {t2["table"][ci_, n_].item() / d2:6.2f} {tl["table"][ci_, n_].item() / d3:7.2f}')
    lines += ['', f'mean stretch inside the mask: {np.nanmean(np.log2(stretch)):+.2f} (log2)',
              f'same-segment pairs: lifted/2D median {np.median(y[same] / np.maximum(x[same], 1e-6)):.2f}',
              f'other-segment pairs: lifted/2D median {np.median(y[~same] / np.maximum(x[~same], 1e-6)):.2f}']
    ax[1, 3].text(0, 1, 'geodesic / diameter between GT points\n\n' + '\n'.join(lines), va='top', family='monospace', fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 1)); plt.savefig(a.out_png, dpi=80); print('\n'.join(lines)); print('saved', a.out_png)


if __name__ == '__main__':
    main()
