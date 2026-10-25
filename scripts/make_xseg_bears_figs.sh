#!/bin/bash
# Back-projection comparison for the 20-bear XSEG run (scripts/run_xseg_bears.sh; Tal, 2026-10-24): picks a few bears from its
# summary.json (largest Fonly gain vs twostage, largest loss, the median one, the largest |Fonly - nofeat|; or IDS="..."),
# builds the soft-snap checker back-projection of every arm (twostage / perseg / nofeat / Fonly) and composes one figure,
# one row per bear: colour key | photo | segment map | the four arms, mean soft-snap error in each title.
# Needs the run's kept intermediates (photo features) and demo/shic/colored_mesh/{bear_shic_normalized_mesh_checker16_uv_color.pth,
# checker16_uv_azim135.png}. Output: $XDEMO/backproj_compare_bears.png
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
NAME=${NAME:-runai_sub20}
RUNS_IN=data/densepose_lvis/runs_$NAME; XRUNS=data/densepose_lvis/runs_xseg_bears_$NAME; XDEMO=demo/shic/xseg_bears_$NAME
SUMMARY=$DISC_WS/logs/xseg_bears_$NAME/summary.json
OBJ=./demo/shic/shapes/bear.obj; CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
IDS=${IDS:-$(# SHIC (argmax, its released bear weights; Tal 2026-10-25): its back-projection per bear, error from its own eval (eval_shic_bear/results.json)
if [ "${SHIC:-1}" = 1 ]; then
  for id in $IDS; do
    tag=lvis$id; D=$RUNS_IN/$tag; O=$XDEMO/bear_$tag/backproj
    [ -f $O/${tag}_SHIC_backproj.png ] && continue
    mkdir -p $O/shic
    python analysis/run_in_one_process.py \
      analysis/shic_infer_correspondence.py --class_name bear --image_path $D/$tag.png --mask_path $D/${tag}_mask.pth --save_dir $O/shic --top_k 10 --- \
      analysis/color_image_from_knn.py --mask_path $D/${tag}_mask.pth --knn_dir $O/shic --knn_path $O/shic/${tag}_shic_pixel_to_vertex_nn.pth \
        --vertex_colors_path $CHK --source_image_path $D/$tag.png --k 1 --save_dir $O/shic --output_path $O/${tag}_SHIC_backproj.png --no_side_by_side \
      >> $O/log.txt 2>&1 && echo "  $tag SHIC done" || echo "  $tag SHIC FAILED, see $O/log.txt"
  done
fi
python analysis/make_xseg_bears_compare.py --shic_results data/densepose_lvis/eval_shic_bear/results.json --summary $SUMMARY --print_pick)}
echo "bears: $IDS"
for id in $IDS; do
  tag=lvis$id; D=$RUNS_IN/$tag; O=$XDEMO/bear_$tag/backproj; mkdir -p $O
  [ -f $O/${tag}_position_color.png ] || python analysis/pixel_coloring.py --img_path $D/$tag.png --mask_path $D/${tag}_mask.pth \
      --mode position --save_dir $O --output_path $O/${tag}_position_color.png > $O/log.txt 2>&1
  for arm in twostage perseg nofeat Fonly; do
    case $arm in twostage) pf=$D/encoder_loraW_all_r4_phase2/alpha/alpha0.5/pred_f.pth ;;
                 *) pf=$XRUNS/$tag/$arm/alpha/alpha0.5/pred_f.pth ;; esac
    [ -f $pf ] || { echo "  $tag $arm: no pred_f, skipped"; continue; }
    [ -f $O/${tag}_${arm}_backproj.png ] && continue
    mkdir -p $O/soft_$arm
    python analysis/run_in_one_process.py \
      analysis/color_mesh_from_soft_mapping.py --mask_path $D/${tag}_mask.pth --img_path $D/$tag.png --save_dir $O/soft_$arm \
        --features_path $D/${tag}_pix_sdsquare_fuse16.pth --vertex_features_path $pf --obj_path $OBJ --name shic_bear \
        --color_mode position --color_path $O/${tag}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
      analysis/color_image_from_knn.py --mask_path $D/${tag}_mask.pth --knn_dir $O/soft_$arm \
        --knn_path $O/soft_$arm/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
        --source_image_path $D/$tag.png --k 1 --save_dir $O --output_path $O/${tag}_${arm}_backproj.png --no_side_by_side >> $O/log.txt 2>&1
    echo "  $tag $arm done"
  done
done
python analysis/make_xseg_bears_compare.py --runs_in $RUNS_IN --xdemo $XDEMO --summary $SUMMARY --ids $IDS \
  --key demo/shic/colored_mesh/checker16_uv_azim135.png --out $XDEMO/backproj_compare_bears.png
