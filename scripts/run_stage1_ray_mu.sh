#!/bin/bash
# Stage 1, ray-cast lifted table, the ellipse isolated again (Tal, 2026-11-09): run_stage1_mu_test.sh's arms on the fixed table.
#   lifted_ray_mu2d : ray-cast lifted table, global ellipse FROZEN to the 2D run's (mu_aniso_stageA_end.pth)
#   lifted_ray_mu1  : ray-cast lifted table, global ellipse FROZEN to the circle mu = 1
# scored with every stage-1 arm so far (zs, 2d_stage1, 2d_mu1, lifted_stage1 / _mu2d / _mu1 = splat table, lifted_ray = learned ellipse)
# -> lifted_full/lvis<i>/stage1_ray/eval_mu.json, + back-projections lifted_full/lvis<i>/backproj/lvis<i>_lifted_ray_mu{2d,1}_backproj.png.
# Features and both tables rebuilt (seed 0) and deleted again after (PVC ~90% full).
# Usage: IDS="171627 186446 32412 109595" bash scripts/run_stage1_ray_mu.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; G=/workspace/pixal3d_out/geom_full
OBJ=./demo/shic/shapes/bear.obj; NAME=shic_bear; P1=./experiments/shic_bear/encoder_dfd_crossview_phase1
GEO3D=./experiments/shic_bear/geodesic_tables/shic_bear_geo_table_3d.pth; GEO228=$R/eval_shic_bear/bear_heat_geodesics_228.npy
CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
t() { local s=$(date +%s); "$@"; echo "[time] $(( $(date +%s) - s )) s : $1 $2"; }
for i in ${IDS:?}; do
  d=$R/runs_full_poly/lvis$i; L=$R/lifted_full/lvis$i; O=$L/stage1_ray; B=$L/backproj; mkdir -p $O; tag=lvis$i
  T2=$d/${tag}_mask_geo_table_2d_seed0.pth; TL=$O/${tag}_mask_geo_table_lifted_ray_seed0.pth; F=$d/${tag}_pix_sdsquare_fuse16.pth
  echo "##### $tag #####"
  [ -f $F ] || t python analysis/extract_dino_sd_features.py --img_path $d/$tag.png --save_dir $d --output_path $F --sd_frame square_pad --cpu_postprocess > $O/features.log 2>&1
  cp $d/${tag}_mask_geo_table_2d_seed0_meta.json $O/meta_2d_fullrun.json
  [ -f $T2 ] || t python analysis/build_geodesic_tables.py --obj_path $OBJ --name $NAME --skip_3d --object_mask_path $d/${tag}_mask.pth \
      --fine_seg_path $d/${tag}_fine_segments.pth --num_center_pixels 2048 --seed 0 --true_diameter --out_dir $d > $O/table2d.log 2>&1
  [ -f $TL ] || t python analysis/build_lifted_geodesic_table.py --lift_path $G/bear_${tag}_full_lift.pth --table_2d $T2 --out_path $TL > $O/tablelifted.log 2>&1
  DL=$(python -c "import json; print(json.load(open('${TL%.pth}_meta.json'))['true_diameter_2d'])")
  NSEG=$(python -c "import torch; print(int((torch.unique(torch.as_tensor(torch.load('$d/${tag}_fine_segments.pth'))) > 0).sum()))")
  if [ $NSEG -eq 1 ]; then NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0 --switch_nin 16 --switch_nout 0)
  else NB=(--num_neighbors_in_segment 8 --num_neighbors_out_segment 8 --switch_nin 16 --switch_nout 0); fi
  MU2=$d/encoder_loraW_all_r4_phase2/mu_aniso_stageA_end.pth; [ -f $MU2 ] || MU2=$d/encoder_loraW_all_r4_phase2/mu_aniso.pth
  declare -A ARM=([lifted_ray_mu2d]="--stageA_fixed --switch_hybrid --mu_aniso_fixed_path $MU2" [lifted_ray_mu1]="--stageA_fixed_circle 1.0")
  M=$L/stage1_mu; EV=(--arm zs=$P1/pred_f.pth --arm 2d_stage1=$d/encoder_loraW_all_r4_phase2/alpha_stageA_end/alpha0.5/pred_f.pth
      --arm 2d_mu1=$M/2d_mu1/alpha/alpha0.5/pred_f.pth
      --arm lifted_stage1=$L/encoder_loraW_all_r4_phase2_lifted_full/alpha_stageA_end/alpha0.5/pred_f.pth
      --arm lifted_mu2d=$M/lifted_mu2d/alpha/alpha0.5/pred_f.pth --arm lifted_mu1=$M/lifted_mu1/alpha/alpha0.5/pred_f.pth
      --arm lifted_ray=$O/lifted_ray/alpha/alpha0.5/pred_f.pth)
  for k in lifted_ray_mu2d lifted_ray_mu1; do
    P2=$O/$k
    [ -f $P2/alpha/alpha0.5/pred_f.pth ] || {
      [ -f $P2/encoder_checkpoint.pth ] || t env PYTHONUNBUFFERED=1 python phase2/train_relational_loss_l2norm.py --obj_path $OBJ --name $NAME --init_encoder_dir $P1 \
          --object_mask_path $d/${tag}_mask.pth --fine_seg_path $d/${tag}_fine_segments.pth --pix_dino_features_path $F \
          --width 2304 --n_classes 2304 --geodesic --temperature 0.01 --train_seed 0 --geo_diag_2d $DL \
          --geo_table_3d_path $GEO3D --geo_table_2d_path $TL \
          --mu_mode learned --mu_scope global_then_segment_aniso --mu_lr 5e-2 --mu_fit_space abs "${NB[@]}" --mu_switch_step 150 --num_iters 149 ${ARM[$k]} \
          --cyc_weight 1.676e-05 --cyc_v2 --cyc_temperature 0.05 --cyc_return_all_pixels --cyc_return_stride 3 \
          --lora_w_rank 4 --lora_w_layers all --lora_w_lr 1e-3 --no_step_checkpoints --out_dir $P2 > $P2.train.log 2>&1
      python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
          --lora_checkpoint $P2/encoder_checkpoint.pth --alphas 0.5 --out_dir $P2/alpha > /dev/null
      rm -f $P2/encoder_checkpoint*.pth; }
    EV+=(--arm $k=$P2/alpha/alpha0.5/pred_f.pth)
    if [ ! -f $B/lvis${i}_${k}_backproj.png ]; then
      mkdir -p $B/soft_$k
      python analysis/run_in_one_process.py \
        analysis/color_mesh_from_soft_mapping.py --mask_path $d/${tag}_mask.pth --img_path $d/$tag.png --save_dir $B/soft_$k \
          --features_path $F --vertex_features_path $P2/alpha/alpha0.5/pred_f.pth --obj_path $OBJ --name shic_bear \
          --color_mode position --color_path $B/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
        analysis/color_image_from_knn.py --mask_path $d/${tag}_mask.pth --knn_dir $B/soft_$k \
          --knn_path $B/soft_$k/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
          --source_image_path $d/$tag.png --k 1 --save_dir $B --output_path $B/lvis${i}_${k}_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
        || echo "lvis$i backproj $k FAILED"
      rm -rf $B/soft_$k
    fi
  done
  python analysis/eval_lvis_ours.py --run_dir $d --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $O/eval_mu.json "${EV[@]}" > $O/eval_mu.log 2>&1
  python -c "
import json; r = json.load(open('$O/eval_mu.json'))['arms']
print('STAGE1 RAY MU $i: ' + ' | '.join('%s %.1f' % (a, v['soft_snap']['all']['mean']) for a, v in r.items()))"
  cp $O/meta_2d_fullrun.json $d/${tag}_mask_geo_table_2d_seed0_meta.json
  rm -f $T2 $TL $F
  unset ARM
done
echo "ALL STAGE1 RAY MU DONE"
