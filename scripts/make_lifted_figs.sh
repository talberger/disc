#!/bin/bash
# Back-projection comparison for the lifted-geodesic runs (scripts/run_lifted_instance.sh; Tal, 2026-10-26): per instance the soft-snap checker
# back-projection of ZS / 2D two-stage / lifted two-stage (+ SHIC argmax), then ONE figure, one row per instance, mean error in each title,
# and a summary table (+ means) of all eval_lifted.json.
# INSTANCES="class:tag:src_run_dir ..." (default: the crowded-parts set of 2026-10-26). Output: data/densepose_lvis/lifted/{backproj_compare.png,
# summary.txt, summary.json}; per instance data/densepose_lvis/lifted/<tag>/backproj/.
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
L=data/densepose_lvis/lifted
INSTANCES=${INSTANCES:-"horse:lvis56069:data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/lvis56069 bear:lvis117682:data/densepose_lvis/runs_runai_sub20/lvis117682 bear:lvis159218:data/densepose_lvis/runs_runai_crowd/lvis159218 bear:lvis212408:data/densepose_lvis/runs_runai_crowd/lvis212408 bear:lvis31383:data/densepose_lvis/runs_runai_crowd/lvis31383 bear:lvis154651:data/densepose_lvis/runs_runai_crowd/lvis154651"}
for it in $INSTANCES; do
  IFS=: read CLASS TAG D <<< "$it"
  OBJ=./demo/shic/shapes/$CLASS.obj; NAME=shic_$CLASS; P1=./experiments/shic_$CLASS/encoder_dfd_crossview_phase1
  if [ $CLASS = bear ]; then CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
  else CHK=demo/shic/colored_mesh/${CLASS}_mesh_checker16_uv_color.pth; fi
  O=$L/$TAG/backproj; mkdir -p $O
  [ -f $L/$TAG/eval_lifted.json ] || { echo "  $TAG: no eval_lifted.json, skipped"; continue; }
  [ -f $O/${TAG}_position_color.png ] || python analysis/pixel_coloring.py --img_path $D/$TAG.png --mask_path $D/${TAG}_mask.pth \
      --mode position --save_dir $O --output_path $O/${TAG}_position_color.png > $O/log.txt 2>&1
  for arm in zs 2d_final lifted_final; do
    case $arm in zs) pf=$P1/pred_f.pth ;; 2d_final) pf=$D/encoder_loraW_all_r4_phase2/alpha/alpha0.5/pred_f.pth ;;
                 lifted_final) pf=$L/$TAG/encoder_loraW_all_r4_phase2_lifted/alpha/alpha0.5/pred_f.pth ;; esac
    [ -f $O/${TAG}_${arm}_backproj.png ] && continue
    mkdir -p $O/soft_$arm
    python analysis/run_in_one_process.py \
      analysis/color_mesh_from_soft_mapping.py --mask_path $D/${TAG}_mask.pth --img_path $D/$TAG.png --save_dir $O/soft_$arm \
        --features_path $D/${TAG}_pix_sdsquare_fuse16.pth --vertex_features_path $pf --obj_path $OBJ --name $NAME \
        --color_mode position --color_path $O/${TAG}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
      analysis/color_image_from_knn.py --mask_path $D/${TAG}_mask.pth --knn_dir $O/soft_$arm \
        --knn_path $O/soft_$arm/${TAG}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
        --source_image_path $D/$TAG.png --k 1 --save_dir $O --output_path $O/${TAG}_${arm}_backproj.png --no_side_by_side >> $O/log.txt 2>&1 \
      && echo "  $TAG $arm done" || echo "  $TAG $arm FAILED, see $O/log.txt"
  done
  if [ ! -f $O/${TAG}_SHIC_backproj.png ] && [ -f demo/shic/weights/$CLASS.pth ]; then
    mkdir -p $O/shic
    python analysis/run_in_one_process.py \
      analysis/shic_infer_correspondence.py --class_name $CLASS --image_path $D/$TAG.png --mask_path $D/${TAG}_mask.pth --save_dir $O/shic --top_k 10 --- \
      analysis/color_image_from_knn.py --mask_path $D/${TAG}_mask.pth --knn_dir $O/shic --knn_path $O/shic/${TAG}_shic_pixel_to_vertex_nn.pth \
        --vertex_colors_path $CHK --source_image_path $D/$TAG.png --k 1 --save_dir $O/shic --output_path $O/${TAG}_SHIC_backproj.png --no_side_by_side \
      >> $O/log.txt 2>&1 && echo "  $TAG SHIC done" || echo "  $TAG SHIC FAILED, see $O/log.txt"
  fi
done
python analysis/make_lifted_compare.py --lifted_dir $L --instances $INSTANCES --out $L/backproj_compare.png --summary $L/summary
