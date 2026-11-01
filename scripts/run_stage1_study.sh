#!/bin/bash
# Stage-1 study, 2D vs lifted teacher (Tal, 2026-11-01): analysis/lifted_vs_2d_stage1_study.py per bear of the FULL run.
# Out: data/densepose_lvis/lifted_full/lvis<i>/study/lvis<i>_stage1_study.{png,txt}. No training.
# Usage: IDS="186446 171627 32412 109595" bash scripts/run_stage1_study.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; G=/workspace/pixal3d_out/geom_full
for i in ${IDS:?}; do
  d=$R/runs_full_poly/lvis$i; L=$R/lifted_full/lvis$i; b=$L/backproj/lvis${i}_
  M2=$d/encoder_loraW_all_r4_phase2; ML=$L/encoder_loraW_all_r4_phase2_lifted_full
  MUL=$ML/mu_aniso_stageA_end.pth; [ -f $MUL ] || MUL=$ML/mu_aniso.pth          # one segment: the run is stage 1 only
  MU2=$M2/mu_aniso_stageA_end.pth; [ -f $MU2 ] || MU2=$M2/mu_aniso.pth
  read SH ZS S2 SL < <(awk -v i=$i '$1 == i {print $2, $3, $4, $7; exit}' $R/lifted_full/summary/summary.txt)
  python analysis/lifted_vs_2d_stage1_study.py --tag lvis$i --src_dir $d --lift_path $G/bear_lvis${i}_full_lift.pth \
      --lifted_meta $L/lvis${i}_mask_geo_table_lifted_seed0_full_meta.json --mu_2d $MU2 --mu_lifted $MUL \
      --panel ${b}SHIC_backproj.png "SHIC\nscore $SH" --panel ${b}zs_backproj.png "zero-shot\nscore $ZS" \
      --panel ${b}2d_stage1_backproj.png "2D stage 1\nscore $S2" --panel ${b}lifted_stage1_backproj.png "3D lift stage 1\nscore $SL" \
      --out_dir $L/study
  echo "lvis$i STAGE1 STUDY DONE"
done
