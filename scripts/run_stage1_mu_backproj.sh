#!/bin/bash
# Back-projections of the stage-1 ellipse test arms (scripts/run_stage1_mu_test.sh; Tal, 2026-11-01), the same commands as run_full_lifted.sh.
# The features were deleted again after the test, so they are rebuilt here and deleted after.
# Out: lifted_full/lvis<i>/backproj/lvis<i>_{lifted_mu2d,lifted_mu1,2d_mu1}_backproj.png
# Usage: IDS="186446 171627 32412 109595" bash scripts/run_stage1_mu_backproj.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; OBJ=./demo/shic/shapes/bear.obj; CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
for i in ${IDS:?}; do
  d=$R/runs_full_poly/lvis$i; L=$R/lifted_full/lvis$i; B=$L/backproj; F=$d/lvis${i}_pix_sdsquare_fuse16.pth
  [ -f $F ] || python analysis/extract_dino_sd_features.py --img_path $d/lvis$i.png --save_dir $d --output_path $F --sd_frame square_pad --cpu_postprocess > $B/features_mu.log 2>&1
  for k in lifted_mu2d lifted_mu1 2d_mu1; do
    [ -f $B/lvis${i}_${k}_backproj.png ] && continue
    mkdir -p $B/soft_$k
    python analysis/run_in_one_process.py \
      analysis/color_mesh_from_soft_mapping.py --mask_path $d/lvis${i}_mask.pth --img_path $d/lvis$i.png --save_dir $B/soft_$k \
        --features_path $F --vertex_features_path $L/stage1_mu/$k/alpha/alpha0.5/pred_f.pth --obj_path $OBJ --name shic_bear \
        --color_mode position --color_path $B/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
      analysis/color_image_from_knn.py --mask_path $d/lvis${i}_mask.pth --knn_dir $B/soft_$k \
        --knn_path $B/soft_$k/lvis${i}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
        --source_image_path $d/lvis$i.png --k 1 --save_dir $B --output_path $B/lvis${i}_${k}_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
      || echo "lvis$i backproj $k FAILED"
    rm -rf $B/soft_$k
  done
  rm -f $F
  echo "lvis$i MU BACKPROJ DONE"
done
