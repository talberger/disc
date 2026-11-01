#!/bin/bash
# Stage 1 only, the ellipse isolated (Tal, 2026-11-01): does the lifted teacher lose because of its LEARNED global ellipse?
# Per bear of the full run, three stage-1 runs (149 steps, the same recipe as stage A of run_lifted_instance.sh, train seed 0):
#   lifted_mu2d : lifted table, the global ellipse FROZEN to the one the 2D run learned (its mu_aniso_stageA_end.pth)
#   lifted_mu1  : lifted table, the global ellipse FROZEN to the circle mu = 1
#   2d_mu1      : 2D table, mu = 1 (control: what mu = 1 does to the 2D teacher)
# scored together with the full run's 2d_stage1 / lifted_stage1 (learned ellipses) -> lifted_full/lvis<i>/stage1_mu/eval.json.
# The full-run cleanup deleted the features and both tables, so they are rebuilt first (same commands, seed 0) and deleted again after.
# Usage: IDS="186446 171627 32412 109595" bash scripts/run_stage1_mu_test.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; G=/workspace/pixal3d_out/geom_full
OBJ=./demo/shic/shapes/bear.obj; NAME=shic_bear; P1=./experiments/shic_bear/encoder_dfd_crossview_phase1
GEO3D=./experiments/shic_bear/geodesic_tables/shic_bear_geo_table_3d.pth; GEO228=$R/eval_shic_bear/bear_heat_geodesics_228.npy
t() { local s=$(date +%s); "$@"; echo "[time] $(( $(date +%s) - s )) s : $1 $2"; }
for i in ${IDS:?}; do
  d=$R/runs_full_poly/lvis$i; L=$R/lifted_full/lvis$i; O=$L/stage1_mu; mkdir -p $O; tag=lvis$i
  T2=$d/${tag}_mask_geo_table_2d_seed0.pth; TL=$O/${tag}_mask_geo_table_lifted_seed0.pth; F=$d/${tag}_pix_sdsquare_fuse16.pth
  echo "##### $tag #####"
  [ -f $F ] || t python analysis/extract_dino_sd_features.py --img_path $d/$tag.png --save_dir $d --output_path $F --sd_frame square_pad --cpu_postprocess > $O/features.log 2>&1
  cp $d/${tag}_mask_geo_table_2d_seed0_meta.json $O/meta_2d_fullrun.json
  [ -f $T2 ] || t python analysis/build_geodesic_tables.py --obj_path $OBJ --name $NAME --skip_3d --object_mask_path $d/${tag}_mask.pth \
      --fine_seg_path $d/${tag}_fine_segments.pth --num_center_pixels 2048 --seed 0 --true_diameter --out_dir $d > $O/table2d.log 2>&1
  [ -f $TL ] || t python analysis/build_lifted_geodesic_table.py --lift_path $G/bear_${tag}_full_lift.pth --table_2d $T2 --out_path $TL > $O/tablelifted.log 2>&1
  python -c "import json; a, b = json.load(open('$O/meta_2d_fullrun.json')), json.load(open('$d/${tag}_mask_geo_table_2d_seed0_meta.json')); print('2D diameter full run %.3f, rebuilt %.3f' % (a['true_diameter_2d'], b['true_diameter_2d']))"
  D2=$(python -c "import json; print(json.load(open('$d/${tag}_mask_geo_table_2d_seed0_meta.json'))['true_diameter_2d'])")
  DL=$(python -c "import json; print(json.load(open('${TL%.pth}_meta.json'))['true_diameter_2d'])")
  NSEG=$(python -c "import torch; print(int((torch.unique(torch.as_tensor(torch.load('$d/${tag}_fine_segments.pth'))) > 0).sum()))")
  if [ $NSEG -eq 1 ]; then NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0 --switch_nin 16 --switch_nout 0)
  else NB=(--num_neighbors_in_segment 8 --num_neighbors_out_segment 8 --switch_nin 16 --switch_nout 0); fi
  MU2=$d/encoder_loraW_all_r4_phase2/mu_aniso_stageA_end.pth; [ -f $MU2 ] || MU2=$d/encoder_loraW_all_r4_phase2/mu_aniso.pth
  declare -A ARM=([lifted_mu2d]="$TL $DL --stageA_fixed --switch_hybrid --mu_aniso_fixed_path $MU2"
                  [lifted_mu1]="$TL $DL --stageA_fixed_circle 1.0" [2d_mu1]="$T2 $D2 --stageA_fixed_circle 1.0")
  EV=(--arm zs=$P1/pred_f.pth --arm 2d_stage1=$d/encoder_loraW_all_r4_phase2/alpha_stageA_end/alpha0.5/pred_f.pth
      --arm lifted_stage1=$L/encoder_loraW_all_r4_phase2_lifted_full/alpha_stageA_end/alpha0.5/pred_f.pth)
  for k in lifted_mu2d lifted_mu1 2d_mu1; do
    read TAB DIAG EXTRA <<< "${ARM[$k]}"; P2=$O/$k
    [ -f $P2/alpha/alpha0.5/pred_f.pth ] || {
      [ -f $P2/encoder_checkpoint.pth ] || t env PYTHONUNBUFFERED=1 python phase2/train_relational_loss_l2norm.py --obj_path $OBJ --name $NAME --init_encoder_dir $P1 \
          --object_mask_path $d/${tag}_mask.pth --fine_seg_path $d/${tag}_fine_segments.pth --pix_dino_features_path $F \
          --width 2304 --n_classes 2304 --geodesic --temperature 0.01 --train_seed 0 --geo_diag_2d $DIAG \
          --geo_table_3d_path $GEO3D --geo_table_2d_path $TAB \
          --mu_mode learned --mu_scope global_then_segment_aniso --mu_lr 5e-2 --mu_fit_space abs "${NB[@]}" --mu_switch_step 150 --num_iters 149 $EXTRA \
          --cyc_weight 1.676e-05 --cyc_v2 --cyc_temperature 0.05 --cyc_return_all_pixels --cyc_return_stride 3 \
          --lora_w_rank 4 --lora_w_layers all --lora_w_lr 1e-3 --no_step_checkpoints --out_dir $P2 > $P2.train.log 2>&1
      python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
          --lora_checkpoint $P2/encoder_checkpoint.pth --alphas 0.5 --out_dir $P2/alpha > /dev/null
      rm -f $P2/encoder_checkpoint*.pth; }
    EV+=(--arm $k=$P2/alpha/alpha0.5/pred_f.pth)
  done
  python analysis/eval_lvis_ours.py --run_dir $d --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $O/eval.json "${EV[@]}" > $O/eval.log 2>&1
  python -c "
import json; r = json.load(open('$O/eval.json'))['arms']
print('STAGE1 MU $i: ' + ' | '.join('%s %.1f' % (a, v['soft_snap']['all']['mean']) for a, v in r.items()))"
  cp $O/meta_2d_fullrun.json $d/${tag}_mask_geo_table_2d_seed0_meta.json
  rm -f $T2 $TL $F                                                   # the PVC is ~90% full: tables (2.6 GB each) and features go again
  unset ARM
done
echo "ALL STAGE1 MU DONE"
