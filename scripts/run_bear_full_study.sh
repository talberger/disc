#!/bin/bash
# Failure study for bears of the FULL run (Tal, 2026-10-29: 186446, 237843, 109595 = bad scores; 32412 = score better, looks worse).
# Per bear, into data/densepose_lvis/lifted_full/lvis<i>/study/: the segment map with the learned mu ellipses of the lifted and the 2D
# two-stage run (plot_mu_ellipses.py), and the lift mesh the table was built on (the remeshed one) as a PLY for MeshLab.
# The back-projections (SHIC, ZS, stage 1, stage 2, 2D) are already in lifted_full/lvis<i>/backproj/. No training.
# Usage: IDS="186446 237843 109595 32412" bash scripts/run_bear_full_study.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; G=/workspace/pixal3d_out/geom_full
for i in ${IDS:?}; do
  d=$R/runs_full_poly/lvis$i; L=$R/lifted_full/lvis$i; O=$L/study; mkdir -p $O
  declare -A MU=([lifted_stage2]=$L/encoder_loraW_all_r4_phase2_lifted_full [2d_stage2]=$d/encoder_loraW_all_r4_phase2)
  for k in "${!MU[@]}"; do
    python analysis/plot_mu_ellipses.py --run_dir ${MU[$k]} --fine_seg_path $d/lvis${i}_fine_segments.pth --img_path $d/lvis$i.png \
        --output_path $O/ellipses_$k.png --title "lvis$i $k" > $O/ellipses_$k.txt 2>&1 || echo "  lvis$i $k ellipses FAILED"
  done
  python - $G/bear_lvis${i}_full_lift.pth $O/lvis${i}_lift.ply <<'EOF'
import sys, numpy as np, torch
L = torch.load(sys.argv[1], map_location='cpu'); V = L['vertices'].numpy().astype('<f4'); F = L['faces'].numpy().astype('<i4')
fa = np.empty(len(F), dtype=[('n', 'u1'), ('i', '<i4', 3)]); fa['n'] = 3; fa['i'] = F
hdr = (f'ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n'
       f'element face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n').encode()
open(sys.argv[2], 'wb').write(hdr + V.tobytes() + fa.tobytes()); print('ply', sys.argv[2], len(V), len(F), L.get('remesh', {}).get('after'))
EOF
  echo "lvis$i STUDY DONE"
done
