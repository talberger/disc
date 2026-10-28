#!/bin/bash
# The horse-style lifted study for ONE bear of the 10-26 20-bear run (Tal, 2026-10-28: 171627, where the lift made it worse): segment map +
# centres, back-projections and ellipses of every arm, lifted teacher vs 2D teacher, with analysis/make_horse_lifted_study.py. No training.
# Out: data/densepose_lvis/lifted/<tag>/study2/{backproj_study.png, segments_centres.png, ellipses_study.png, study_summary.txt}
# Usage: ID=171627 bash scripts/run_bear_lifted_study.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
ID=${ID:?}; TAG=lvis$ID; R=data/densepose_lvis; SRC=$R/runs_runai_sub20/$TAG; L=$R/lifted/$TAG; O=$L/study2; mkdir -p $O/backproj
OBJ=./demo/shic/shapes/bear.obj; NAME=shic_bear; CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
P=$L/encoder_loraW_all_r4_phase2_lifted; S2=$SRC/encoder_loraW_all_r4_phase2; X=$R/runs_xseg_bears_runai_sub20/$TAG/perseg
cp $L/multi_eval.json $O/study_eval.json
for f in $L/backproj/${TAG}_*_backproj.png; do ln -sf $(realpath $f) $O/backproj/; done
# the one back-projection the 10-26 figures did not make: 2D stage 1
if [ ! -f $O/backproj/${TAG}_2d_stage1_backproj.png ]; then
  B=$L/backproj; mkdir -p $B/soft_2d_stage1
  python analysis/run_in_one_process.py \
    analysis/color_mesh_from_soft_mapping.py --mask_path $SRC/${TAG}_mask.pth --img_path $SRC/$TAG.png --save_dir $B/soft_2d_stage1 \
      --features_path $SRC/${TAG}_pix_sdsquare_fuse16.pth --vertex_features_path $S2/alpha_stageA_end/alpha0.5/pred_f.pth --obj_path $OBJ --name $NAME \
      --color_mode position --color_path $B/${TAG}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
    analysis/color_image_from_knn.py --mask_path $SRC/${TAG}_mask.pth --knn_dir $B/soft_2d_stage1 \
      --knn_path $B/soft_2d_stage1/${TAG}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
      --source_image_path $SRC/$TAG.png --k 1 --save_dir $B --output_path $O/backproj/${TAG}_2d_stage1_backproj.png --no_side_by_side > $O/log.txt 2>&1
fi
declare -A MU=([lifted_stage2]=$P [lifted_perseg]=${P}_perseg [lifted_hybrid]=${P}_hybrid [2d_stage2]=$S2 [2d_perseg]=$X)
for k in "${!MU[@]}"; do
  [ -f ${MU[$k]}/mu_aniso.pth ] || { echo "  $k: no mu_aniso.pth"; continue; }
  python analysis/plot_mu_ellipses.py --run_dir ${MU[$k]} --fine_seg_path $SRC/${TAG}_fine_segments.pth --img_path $SRC/$TAG.png \
      --output_path $O/ellipses_$k.png --title "$k" > $O/ellipses_$k.txt 2>&1 || echo "  $k ellipses FAILED"
done
python analysis/make_horse_lifted_study.py --src $SRC --tag $TAG --study_dir $O --table $L/${TAG}_mask_geo_table_lifted_seed0.pth \
    --maps sam1=$SRC/${TAG}_fine_segments.pth --shic_results $R/eval_shic_bear/results.json \
    --rows_json '[["SAM 1 map, lifted teacher", "sam1", ["zs", "lifted_stage1", "lifted_stage2", "lifted_perseg", "lifted_hybrid"]],
                  ["SAM 1 map, 2D teacher", "sam1", ["zs", "2d_stage1", "2d_stage2", "2d_perseg", "none"]]]'
echo "BEAR STUDY $TAG DONE"
