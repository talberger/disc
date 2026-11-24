"""Run SHIC inference and write its dense image->mesh correspondence in THIS project's format.

Why a wrapper rather than their notebook: `shic.ipynb` predicts the corresponding vertex for ONE
clicked pixel and renders an interactive trimesh viewer. Figure 6 of the paper is the dense version
-- every object pixel gets a vertex, a textured mesh is pulled back onto the image. This script
produces exactly that, and writes it with the same keys `analysis/pixel_to_vertex_nn.py` emits, so
`analysis/color_image_from_knn.py` can back-project it with no changes and the SHIC and ours
comparisons are rendered by identical code.

SHIC's model (src/model.py, src/shape_model.py, weights from the authors' Google Drive):
  image side : DINOv2 ViT-S/14 (frozen) + a learned decoder -> [1, 16, 224, 224] dense embedding
  shape side : CSE = LBO functional basis [V, 64] @ learned weight matrix [64, 16] -> [V, 16]
  match      : cosine/dot between a pixel embedding and every vertex embedding
Their transform is `Resize((224, 224))` -- NOT aspect preserving. To get correspondence at the
photo's own resolution the [16, 224, 224] map is bilinearly upsampled back to (H, W), which is the
continuous version of the notebook's own `x * 224 / w` index mapping.

The mask comes from --mask_path, else from the PNG's ALPHA channel if it is a real cutout. NOTE (checked
2026-11-24): SHIC's demo images are RGBA but fully OPAQUE (0 transparent pixels) -- they are NOT cutouts, and
SHIC itself has no foreground head; their paper uses masks only to sample training points. So pass --mask_path.

Run:
  python analysis/shic_infer_correspondence.py --class_name bear \
    --image_path demo/shic/images/bear3.png --save_dir demo/shic/bear3 --top_k 10
"""
import argparse, os, sys
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

SHIC_RUN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'demo', 'shic', 'run')


def load_shic(class_name, device):
    """SHIC resolves 'models/shapes/<class>.obj' RELATIVE TO THE CWD (src/shape_utils.py), so this
    chdir's into demo/shic/run/, which holds symlinks to shapes/ and weights/. Restored after."""
    prev = os.getcwd()
    os.chdir(SHIC_RUN_DIR)
    sys.path.insert(0, SHIC_RUN_DIR)
    try:
        from src.model import DinoV2
        from src.shape_model import CSE
        enc = DinoV2(16)
        enc.load_state_dict(torch.load(f'./models/weights/{class_name}.pth', map_location=device))
        cse = CSE(class_name=class_name, num_basis=64, device=device)
        cse.load_state_dict(torch.load(f'./models/weights/{class_name}_cse.pth', map_location=device))
        cse.functional_basis = torch.load(f'./models/weights/{class_name}_lbo.pth',
                                          map_location=device).to(device)
        cse.weight_matrix = cse.weight_matrix.to(device)
        enc = enc.to(device).eval()
        shape_feats = cse().to(device)                      # [V, 16]
        verts = cse.shape['verts'].cpu().numpy().copy()     # bbox-centred, max extent 1
        faces = cse.shape['faces'].cpu().numpy().copy()
    finally:
        os.chdir(prev)
    return enc, shape_feats, verts, faces


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--class_name', required=True, choices=['bear', 'horse', 'elephant'])
    ap.add_argument('--image_path', required=True)
    ap.add_argument('--save_dir', required=True)
    ap.add_argument('--top_k', type=int, default=10)
    ap.add_argument('--mask_path', default=None, help='used only if the image has no alpha channel')
    ap.add_argument('--alpha_thresh', type=int, default=128)
    ap.add_argument('--chunk', type=int, default=20000)
    ap.add_argument('--save_raw_features', action='store_true',
                    help='also save the dense [H,W,16] pixel embedding and [V,16] vertex '
                         '(shape) embedding as bare float32 tensors, in the exact format '
                         'analysis/pixel_to_vertex_nn.py::load_features/load_vertex_features '
                         'expect -- so analysis/color_mesh_from_soft_mapping.py (softmax-weighted '
                         'top-k, i.e. soft-snap) works on SHIC\'s own features completely '
                         'unmodified, the same way it already does for this project\'s own '
                         'DINO+SD features. Off by default: the dense grid is ~50-100 MB.')
    ap.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = ap.parse_args()

    device = torch.device(args.device)
    os.makedirs(args.save_dir, exist_ok=True)

    pil = Image.open(args.image_path)
    W, H = pil.size
    # --mask_path WINS over alpha. It used to be the other way round, which silently ignored an
    # explicitly passed mask (2026-09-03): SHIC's demo PNGs carry an alpha channel that is fully
    # OPAQUE, so the alpha branch returned the whole frame and the run looked successful.
    if args.mask_path:
        mask = torch.load(args.mask_path, map_location='cpu').bool()
        mask_src = args.mask_path
    elif 'A' in pil.getbands() and (np.array(pil.getchannel('A')) < args.alpha_thresh).any():
        mask = torch.from_numpy(np.array(pil.getchannel('A')) >= args.alpha_thresh)
        mask_src = f'{args.image_path} (alpha >= {args.alpha_thresh})'
    else:
        raise SystemExit('image has no usable alpha cutout -- pass --mask_path '
                         '(see analysis/segment_shic_image.py)')
    if mask.shape != (H, W):
        raise SystemExit(f'mask {tuple(mask.shape)} does not match image {(H, W)}')
    rgb = pil.convert('RGB')

    enc, shape_feats, verts, faces = load_shic(args.class_name, device)
    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                                  std=[0.229, 0.224, 0.225])])
    with torch.no_grad():
        feats = enc(tf(rgb).unsqueeze(0).to(device))                     # [1, 16, 224, 224]
        full = F.interpolate(feats, size=(H, W), mode='bilinear', align_corners=False)[0]

    rows, cols = torch.nonzero(mask, as_tuple=True)
    pix = full[:, rows, cols].T.contiguous()                             # [N, 16]
    full_saved = full.permute(1, 2, 0).contiguous().float().cpu() if args.save_raw_features else None
    del full, feats

    k = min(args.top_k, shape_feats.shape[0])
    idx_all, sim_all = [], []
    with torch.no_grad():
        for s in range(0, pix.shape[0], args.chunk):
            sim = pix[s:s + args.chunk] @ shape_feats.T                  # [chunk, V]
            v, i = torch.topk(sim, k, dim=1)
            sim_all.append(v.cpu()); idx_all.append(i.cpu())
    topk_sim = torch.cat(sim_all); topk_idx = torch.cat(idx_all)

    out = {
        'pixel_row': rows.cpu(), 'pixel_col': cols.cpu(),
        'top1_vertex_idx': topk_idx[:, 0], 'top1_similarity': topk_sim[:, 0],
        'topk_vertex_idx': topk_idx, 'topk_similarity': topk_sim,
        'top_k': k, 'num_vertices': int(shape_feats.shape[0]), 'mask_shape': (H, W),
        'vertex_features_path': f'SHIC CSE embedding, class={args.class_name}',
        'features_path': f'SHIC DinoV2 decoder, {args.image_path}',
        'mask_path': mask_src,
    }
    base = os.path.splitext(os.path.basename(args.image_path))[0]
    knn_path = os.path.join(args.save_dir, f'{base}_shic_pixel_to_vertex_nn.pth')
    torch.save(out, knn_path)

    raw_feat_path = raw_vert_path = None
    if args.save_raw_features:
        # [H, W, 16] and [V, 16], float32, bare tensors -- pixel_to_vertex_nn.py's own
        # load_features/load_vertex_features accept exactly this, no shim needed.
        raw_feat_path = os.path.join(args.save_dir, f'{base}_shic_pix_features.pth')
        raw_vert_path = os.path.join(args.save_dir, f'{args.class_name}_shic_vertex_features.pth')
        torch.save(full_saved, raw_feat_path)
        torch.save(shape_feats.float().cpu(), raw_vert_path)
    mask_out = os.path.join(args.save_dir, f'{base}_shic_mask.pth')
    torch.save(mask, mask_out)
    obj_out = os.path.join(args.save_dir, f'{args.class_name}_shic_normalized.obj')
    with open(obj_out, 'w') as f:
        for v in verts:
            f.write(f'v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n')
        for fc in faces:
            f.write(f'f {fc[0]+1} {fc[1]+1} {fc[2]+1}\n')

    cov = int(torch.unique(topk_idx[:, 0]).numel())
    print(f'image        : {args.image_path}  {H}x{W}')
    print(f'mask         : {mask_src}  -> {rows.shape[0]} pixels ({100*rows.shape[0]/(H*W):.1f}%)')
    print(f'mesh         : {args.class_name}  V={shape_feats.shape[0]}  F={len(faces)}')
    print(f'coverage     : {cov}/{shape_feats.shape[0]} = {100*cov/shape_feats.shape[0]:.2f}% '
          f'(vertices hit by top-1)')
    print(f'similarity   : min={topk_sim[:,0].min():.4f} max={topk_sim[:,0].max():.4f} '
          f'mean={topk_sim[:,0].mean():.4f}')
    print(f'saved        : {knn_path}\n               {mask_out}\n               {obj_out}')
    if args.save_raw_features:
        print(f'raw features : {raw_feat_path}\n               {raw_vert_path}')


if __name__ == '__main__':
    main()
