"""The full bear run's rule for the geodesic domain (scripts/run_full_lifted.sh, STEP=prep), for one instance whose amodal mask was made in
a separate folder: if the visible mask is SPLIT (its largest connected piece < 95% of it) the merged amodal mask is copied next to the run's
inputs, <run_dir>/<tag>_amodal_mask.pth = the domain of the 2D table and of the training (scripts/run_stage1_raycast.sh). Else nothing.
Usage: python analysis/amodal_domain_if_split.py --run_dir <runs>/lvis<i> --amodal_dir <lifted>/lvis<i>/amodal --tag lvis<i>"""
import argparse, os, shutil
import numpy as np, torch
from scipy import ndimage

ap = argparse.ArgumentParser(); ap.add_argument('--run_dir', required=True); ap.add_argument('--amodal_dir', required=True)
ap.add_argument('--tag', required=True); ap.add_argument('--min_largest', type=float, default=0.95)
a = ap.parse_args()
m = torch.load(f'{a.run_dir}/{a.tag}_mask.pth').numpy().astype(bool)
lab, _ = ndimage.label(m, structure=np.ones((3, 3)))
largest = float(np.bincount(lab[m]).max() / m.sum()); src = f'{a.amodal_dir}/{a.tag}_amodal_mask.pth'
split = largest < a.min_largest and os.path.exists(src)
if split:
    shutil.copyfile(src, f'{a.run_dir}/{a.tag}_amodal_mask.pth')
print(f'{a.tag}: largest piece {largest:.3f} of the visible mask -> ' + ('SPLIT, amodal mask = geodesic domain' if split else 'one piece, no amodal domain'))
