"""SHIC on one DensePose-LVIS instance: per GT point error + predicted vertex (json on stdout). Usage: python analysis/shic_one.py <ann_id> <class>"""
import sys, json, numpy as np, torch, torch.nn.functional as F
from PIL import Image
sys.path.insert(0, 'analysis')
import eval_densepose_lvis as E
aid = int(sys.argv[1]); cls = sys.argv[2] if len(sys.argv) > 2 else 'bear'
anns, imgs = E.load_instances(cls); a = [x for x in anns if x['id'] == aid][0]
enc, sf, verts, faces = E.load_shic(cls, torch.device('cpu')); G = np.load(f'data/densepose_lvis/eval_shic_{cls}/{cls}_heat_geodesics_228.npy')
img = E.get_image(imgs[a['image_id']]); crop, (cx, cy, cw, ch) = E.make_crop(img, a, 'bbox')
with torch.no_grad(): f = enc(E.TF(crop.resize((224, 224), Image.BILINEAR)).unsqueeze(0))
bx, by, bw, bh = a['bbox']; px = bx + np.array(a['dp_x']) / 256 * bw; py = by + np.array(a['dp_y']) / 256 * bh
g = torch.tensor(np.stack([(px - cx) / cw * 2 - 1, (py - cy) / ch * 2 - 1], -1), dtype=torch.float32)[None, None]
emb = F.grid_sample(f, g, mode='bilinear', align_corners=False)[0, :, 0].T; pred = (emb @ sf.T).argmax(1).numpy()
e = G[np.array(a['dp_vertex']), pred]
print(json.dumps({'per_point': e.tolist(), 'pred_vertex': pred.tolist(), 'gt_vertex': list(a['dp_vertex']), 'mean': float(e.mean()), 'n_verts': len(verts)}))
