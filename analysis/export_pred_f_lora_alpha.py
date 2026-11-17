"""
LORA-W read-time alpha sweep (2026-09-17): rebuild the encoder as W_phase1 + alpha * B A for each alpha
and export pred_f, WITHOUT retraining. alpha=0 is phase-1 (ZS), alpha=1 is the trained LORA-W run.

cd $DISC_ROOT && python analysis/export_pred_f_lora_alpha.py --obj_path ./demo/shic/shapes/bear.obj --name shic_bear \
  --phase1_checkpoint experiments/shic_bear/encoder_dfd_crossview_phase1/encoder_checkpoint.pth \
  --lora_checkpoint <phase2 dir>/encoder_checkpoint.pth --alphas 0.25 0.5 0.75 --out_dir <phase2 dir>/alpha
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch

from analysis.verify_encoder_resume import seed_everything
from modules.encoder_l2norm import EncoderL2Norm
from modules.lora import merge_lora_into_state_dict
from modules.utils import device, load_state_dict, loadmesh
from phase2.train_mapping_loss import set_fourier_basis

parser = argparse.ArgumentParser()
parser.add_argument('--obj_path', required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--phase1_checkpoint', required=True)
parser.add_argument('--lora_checkpoint', required=True)
parser.add_argument('--alphas', type=float, nargs='+', required=True)
parser.add_argument('--out_dir', required=True)
parser.add_argument('--depth', type=int, default=4)
parser.add_argument('--width', type=int, default=2304)
parser.add_argument('--n_classes', type=int, default=2304)
parser.add_argument('--sigma', type=float, default=5.0)
parser.add_argument('--seed', type=int, default=0)
args = parser.parse_args()

vertices = loadmesh(dir=args.obj_path, name=args.name, load_rings=False).vertices
p1 = torch.load(args.phase1_checkpoint, map_location=device)
lc = torch.load(args.lora_checkpoint, map_location=device)
assert lc.get('lora_state'), 'not a LORA-W checkpoint (no lora_state)'
seed_everything(args.seed)  # the Fourier basis is not in the phase-1 state_dict
enc = EncoderL2Norm(args.depth, args.width, out_dim=args.n_classes, positional_encoding=True,
                    sigma=args.sigma, network_verbose=0).to(device)
set_fourier_basis(enc, lc.get('fourier_basis'))
os.makedirs(args.out_dir, exist_ok=True)
# the LoRA delta alone (~1 MB, 2026-11-17): any read-time alpha can be exported later without retraining (the runs delete the
# full checkpoint); rebuild with merge_lora_into_state_dict(phase-1 state, this, alpha) + the saved Fourier basis
torch.save({'lora_state': lc['lora_state'], 'fourier_basis': lc.get('fourier_basis')}, os.path.join(args.out_dir, 'lora_state.pth'))
with torch.no_grad():
    for a in args.alphas:
        load_state_dict(enc, merge_lora_into_state_dict(p1['encoder_state_dict'], lc['lora_state'], a))
        out = os.path.join(args.out_dir, 'alpha%g' % a, 'pred_f.pth')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        torch.save(enc(vertices), out)
        print('alpha %g -> %s' % (a, out))
