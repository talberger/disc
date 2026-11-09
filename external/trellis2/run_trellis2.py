"""Plain TRELLIS.2 (microsoft/TRELLIS.2-4B) on our RGBA crops, geometry only, for a LOOK at the shape next to Pixal3D's (Tal, 2026-11-09;
32412: Pixal3D folds the head back). Pixal3D (branch master) is TRELLIS.2 + pixel-aligned conditioning; plain TRELLIS.2 builds the object in
its own canonical frame, NOT aligned to the photo, so this output is for viewing only (no pixel -> surface correspondence).
Only the geometry checkpoints are fetched (~9 GB of the 16 GB repo): a local pipeline.json without the texture models, DINOv3 from the
ungated mirror Pixal3D already uses, background removal stubbed (the alpha of our RGBA is the mask, as in lift.py).
Run in the Pixal3D env (pixal3d-env2):
  cd /workspace/trellis2_repo && source /workspace/envs/pixal3d/bin/activate
  HF_HOME=/workspace/.cache/huggingface python /workspace/disc/external/trellis2/run_trellis2.py --images <rgba.png> ... --out_dir <dir>
Out per image: <out_dir>/<tag>_trellis2.ply (fill_holes, decimated to --faces)."""
import argparse, json, os, sys, time
import numpy as np, torch
from PIL import Image
from huggingface_hub import hf_hub_download, snapshot_download

REPO = os.environ.get('TRELLIS2_REPO', '/workspace/trellis2_repo')
sys.path.insert(0, REPO)
from trellis2.pipelines import Trellis2ImageTo3DPipeline, rembg as rembg_mod


class NoRembg:
    def __init__(self, *a, **k): pass
    def to(self, *a, **k): return self
    def cuda(self): return self
    def cpu(self): return self
    def __call__(self, *a, **k): raise RuntimeError('needs an RGBA input (our mask as alpha); background removal is disabled')


for _name in dir(rembg_mod):
    if not _name.startswith('_') and isinstance(getattr(rembg_mod, _name), type):
        setattr(rembg_mod, _name, NoRembg)

GEOM = ['ckpts/ss_flow_img_dit_1_3B_64_bf16', 'ckpts/shape_dec_next_dc_f16c32_fp16',
        'ckpts/slat_flow_img2shape_dit_1_3B_512_bf16', 'ckpts/slat_flow_img2shape_dit_1_3B_1024_bf16']


def write_ply(path, V, F):
    fa = np.empty(len(F), dtype=[('n', 'u1'), ('i', '<i4', 3)]); fa['n'] = 3; fa['i'] = F
    hdr = (f'ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n'
           f'element face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n')
    with open(path, 'wb') as f:
        f.write(hdr.encode()); f.write(V.astype('<f4').tobytes()); f.write(fa.tobytes())


def local_pipeline():
    """Geometry-only copy of the HF repo: pipeline.json without the texture models, DINOv3 from the mirror."""
    src = snapshot_download('microsoft/TRELLIS.2-4B', allow_patterns=['pipeline.json'] + [g + ext for g in GEOM for ext in ('.json', '.safetensors')])
    hf_hub_download('microsoft/TRELLIS-image-large', 'ckpts/ss_dec_conv3d_16l8_fp16.json')
    hf_hub_download('microsoft/TRELLIS-image-large', 'ckpts/ss_dec_conv3d_16l8_fp16.safetensors')
    cfg = json.load(open(os.path.join(src, 'pipeline.json')))
    for k in [k for k in cfg['args']['models'] if k.startswith('tex_')]:
        del cfg['args']['models'][k]
    cfg['args']['image_cond_model']['args']['model_name'] = 'camenduru/dinov3-vitl16-pretrain-lvd1689m'
    dst = os.path.join(os.environ.get('HF_HOME', '/workspace/.cache/huggingface'), 'trellis2_geometry_only'); os.makedirs(dst, exist_ok=True)
    if not os.path.exists(os.path.join(dst, 'ckpts')):
        os.symlink(os.path.join(src, 'ckpts'), os.path.join(dst, 'ckpts'))
    json.dump(cfg, open(os.path.join(dst, 'pipeline.json'), 'w'), indent=1)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', nargs='+', required=True); ap.add_argument('--tags', nargs='+', default=None)
    ap.add_argument('--out_dir', required=True); ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--pipeline_type', default='1024_cascade'); ap.add_argument('--faces', type=int, default=1000000)
    a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
    tags = a.tags or [os.path.basename(p).replace('_rgba.png', '').replace('.png', '') for p in a.images]
    t0 = time.time()
    pipeline = Trellis2ImageTo3DPipeline.from_pretrained(local_pipeline()); pipeline.cuda()
    print(f'[trellis2] loaded in {time.time() - t0:.0f} s', flush=True)
    for p, tag in zip(a.images, tags):
        t = time.time(); img = Image.open(p); assert img.mode == 'RGBA', f'{p}: need RGBA'
        mesh = pipeline.run(img, seed=a.seed, pipeline_type=a.pipeline_type)[0]
        mesh.fill_holes(); mesh.simplify(a.faces)
        V, F = mesh.vertices.float().cpu().numpy(), mesh.faces.long().cpu().numpy()
        out = os.path.join(a.out_dir, f'{tag}_trellis2.ply'); write_ply(out, V, F)
        print(f'[trellis2] {tag}: {len(V)} vertices, {len(F)} faces -> {out} [{time.time() - t:.0f} s]', flush=True)
    print('TRELLIS2 DONE', flush=True)


if __name__ == '__main__':
    main()
