#!/bin/bash
# Stage 1 with the RAY-CAST pixel -> mesh mapping (Tal, 2026-11-08): lift.py's vertex splat maps some front pixels to the bear's back
# (171627 rep 3 -> x3, analysis/lifted_pixel_vertex_check.py); build_lifted_geodesic_table.py --pix_map raycast fixes that.
# Per bear: the lifted table rebuilt with --pix_map raycast, one stage-1 run (149 steps, learned global ellipse = the full run's stage A,
# train seed 0), scored with zs / 2d_stage1 / lifted_stage1 (splat) of the full run -> lifted_full/lvis<i>/stage1_ray/eval.json,
# and its back-projection -> lifted_full/lvis<i>/backproj/lvis<i>_lifted_ray_backproj.png.
# Features and the 2D table were deleted by the full-run cleanup: rebuilt (same commands, seed 0) and deleted again after (PVC ~90% full).
# Usage: IDS="171627 186446 32412 109595" bash scripts/run_stage1_raycast.sh
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
  [ -f $TL ] || t python analysis/build_lifted_geodesic_table.py --lift_path $G/bear_${tag}_full_lift.pth --table_2d $T2 --out_path $TL --pix_map raycast > $O/tablelifted.log 2>&1
  DL=$(python -c "import json; print(json.load(open('${TL%.pth}_meta.json'))['true_diameter_2d'])")
  echo "lifted diameter: splat $(python -c "import json; print(json.load(open('$L/${tag}_mask_geo_table_lifted_seed0_full_meta.json'))['true_diameter_2d'])"), ray $DL"
  NSEG=$(python -c "import torch; print(int((torch.unique(torch.as_tensor(torch.load('$d/${tag}_fine_segments.pth'))) > 0).sum()))")
  if [ $NSEG -eq 1 ]; then NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0 --switch_nin 16 --switch_nout 0)
  else NB=(--num_neighbors_in_segment 8 --num_neighbors_out_segment 8 --switch_nin 16 --switch_nout 0); fi
  P2=$O/lifted_ray
  [ -f $P2/alpha/alpha0.5/pred_f.pth ] || {
    [ -f $P2/encoder_checkpoint.pth ] || t env PYTHONUNBUFFERED=1 python phase2/train_relational_loss_l2norm.py --obj_path $OBJ --name $NAME --init_encoder_dir $P1 \
        --object_mask_path $d/${tag}_mask.pth --fine_seg_path $d/${tag}_fine_segments.pth --pix_dino_features_path $F \
        --width 2304 --n_classes 2304 --geodesic --temperature 0.01 --train_seed 0 --geo_diag_2d $DL \
        --geo_table_3d_path $GEO3D --geo_table_2d_path $TL \
        --mu_mode learned --mu_scope global_then_segment_aniso --mu_lr 5e-2 --mu_fit_space abs "${NB[@]}" --mu_switch_step 150 --num_iters 149 \
        --cyc_weight 1.676e-05 --cyc_v2 --cyc_temperature 0.05 --cyc_return_all_pixels --cyc_return_stride 3 \
        --lora_w_rank 4 --lora_w_layers all --lora_w_lr 1e-3 --no_step_checkpoints --out_dir $P2 > $P2.train.log 2>&1
    python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
        --lora_checkpoint $P2/encoder_checkpoint.pth --alphas 0.5 --out_dir $P2/alpha > /dev/null
    rm -f $P2/encoder_checkpoint*.pth; }
  python analysis/eval_lvis_ours.py --run_dir $d --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $O/eval.json \
      --arm zs=$P1/pred_f.pth --arm 2d_stage1=$d/encoder_loraW_all_r4_phase2/alpha_stageA_end/alpha0.5/pred_f.pth \
      --arm lifted_stage1=$L/encoder_loraW_all_r4_phase2_lifted_full/alpha_stageA_end/alpha0.5/pred_f.pth \
      --arm lifted_ray=$P2/alpha/alpha0.5/pred_f.pth > $O/eval.log 2>&1
  python -c "
import json; r = json.load(open('$O/eval.json'))['arms']
print('STAGE1 RAY $i: ' + ' | '.join('%s %.1f' % (a, v['soft_snap']['all']['mean']) for a, v in r.items()))"
  if [ ! -f $B/lvis${i}_lifted_ray_backproj.png ]; then
    mkdir -p $B/soft_ray
    python analysis/run_in_one_process.py \
      analysis/color_mesh_from_soft_mapping.py --mask_path $d/${tag}_mask.pth --img_path $d/$tag.png --save_dir $B/soft_ray \
        --features_path $F --vertex_features_path $P2/alpha/alpha0.5/pred_f.pth --obj_path $OBJ --name shic_bear \
        --color_mode position --color_path $B/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
      analysis/color_image_from_knn.py --mask_path $d/${tag}_mask.pth --knn_dir $B/soft_ray \
        --knn_path $B/soft_ray/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
        --source_image_path $d/$tag.png --k 1 --save_dir $B --output_path $B/lvis${i}_lifted_ray_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
      || echo "lvis$i backproj lifted_ray FAILED"
    rm -rf $B/soft_ray
  fi
  cp $O/meta_2d_fullrun.json $d/${tag}_mask_geo_table_2d_seed0_meta.json
  rm -f $T2 $TL $F
done
echo "ALL STAGE1 RAY DONE"
