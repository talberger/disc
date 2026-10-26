#!/bin/bash
# Horse 164135 (LEG COLLISION: seg 3 of the old SAM 1 map = the front leg, correct mesh leg = x-) with the LIFTED geodesic teacher (Tal, 2026-10-26).
# Inputs = the 09-28 ones (data/densepose_lvis/runs/lvis164135/), 2D reference = the 09-28 two-stage sw150 run. Two segment maps:
#   sam1 = the old SAM 1 map (its own 2D table)   |   vlp8 = VLPart partimagenet>=0.3, 8 segs, every leg its own segment (its own 2D table)
# Runs (lifted teacher): two-stage + per-seg only on each map; the two maps' runs go side by side on the GPU.
# Outputs data/densepose_lvis/lifted/lvis164135/study/: leg_seg3.png (diag_seg_mapping.py, the 2D two-stage run FIRST so seg 3 = the old-map
# front leg -- the TRAP in the notes), backproj_study.png, segments_centres.png, ellipses_*.png, study_summary.txt.
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
TAG=lvis164135; CLASS=horse; SRC=data/densepose_lvis/runs/$TAG
V=data/densepose_lvis/fine_segments_vlpart; VLP8=$V/${TAG}_fine_segments_partimagenet_thr0.3.pth; T2D8=$V/geo_lvis164135_vlpart8/${TAG}_mask_geo_table_2d_seed0.pth
TS=experiments/shic_horse/lvis/$TAG/encoder_mu_globalthenaniso_perseg_cycv2T0.05_c1.676e-05_retstride3_loraW_all_r4_lr1e-3_T0.01_seed0_mulr5e-2_in8out8_sw150_phase2
LIFT=/workspace/pixal3d_out/geom/horse_${TAG}_lift.pth
L=data/densepose_lvis/lifted/$TAG; O=$L/study; mkdir -p $O
OBJ=./demo/shic/shapes/$CLASS.obj; NAME=shic_$CLASS; P1=./experiments/shic_$CLASS/encoder_dfd_crossview_phase1
CHK=demo/shic/colored_mesh/${CLASS}_mesh_checker16_uv_color.pth; GEO228=data/densepose_lvis/eval_shic_$CLASS/${CLASS}_heat_geodesics_228.npy

run() { CLASS=$CLASS TAG=$TAG SRC=$SRC LIFT=$LIFT S2DIR=$TS S2STAGE1=$TS/step150_alpha/alpha0.5/pred_f.pth "$@" bash scripts/run_lifted_instance.sh; }
echo "##### training [$(date -u +%T)]"
run env MODE=twostage & run env MODE=twostage FINESEG=$VLP8 T2D=$T2D8 RUNTAG=_vlpart8 & wait     # each builds its own lifted table
run env MODE=perseg   & run env MODE=perseg   FINESEG=$VLP8 T2D=$T2D8 RUNTAG=_vlpart8 & wait

R=$L/encoder_loraW_all_r4_phase2_lifted
declare -A PF SEG MU
PF[zs]=$P1/pred_f.pth
PF[sam1_2d_stage1]=$TS/step150_alpha/alpha0.5/pred_f.pth;   SEG[sam1_2d_stage1]=$SRC/${TAG}_fine_segments.pth
PF[sam1_2d_stage2]=$TS/alpha/alpha0.5/pred_f.pth;           SEG[sam1_2d_stage2]=$SRC/${TAG}_fine_segments.pth; MU[sam1_2d_stage2]=$TS
PF[sam1_lifted_stage1]=$R/alpha_stageA_end/alpha0.5/pred_f.pth; SEG[sam1_lifted_stage1]=$SRC/${TAG}_fine_segments.pth
PF[sam1_lifted_stage2]=$R/alpha/alpha0.5/pred_f.pth;            SEG[sam1_lifted_stage2]=$SRC/${TAG}_fine_segments.pth; MU[sam1_lifted_stage2]=$R
PF[sam1_lifted_perseg]=${R}_perseg/alpha/alpha0.5/pred_f.pth;   SEG[sam1_lifted_perseg]=$SRC/${TAG}_fine_segments.pth; MU[sam1_lifted_perseg]=${R}_perseg
PF[vlp8_lifted_stage1]=${R}_vlpart8/alpha_stageA_end/alpha0.5/pred_f.pth; SEG[vlp8_lifted_stage1]=$VLP8
PF[vlp8_lifted_stage2]=${R}_vlpart8/alpha/alpha0.5/pred_f.pth;            SEG[vlp8_lifted_stage2]=$VLP8; MU[vlp8_lifted_stage2]=${R}_vlpart8
PF[vlp8_lifted_perseg]=${R}_perseg_vlpart8/alpha/alpha0.5/pred_f.pth;     SEG[vlp8_lifted_perseg]=$VLP8; MU[vlp8_lifted_perseg]=${R}_perseg_vlpart8

echo "##### eval [$(date -u +%T)]"
ARMS=(); for k in "${!PF[@]}"; do [ -f ${PF[$k]} ] && ARMS+=(--arm $k=${PF[$k]}); done
python analysis/eval_lvis_ours.py --run_dir $SRC --tag $TAG --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $O/study_eval.json "${ARMS[@]}" > $O/eval.log 2>&1

echo "##### leg (seg 3 of the old map) [$(date -u +%T)]"
python analysis/diag_seg_mapping.py --seg 3 --cols 2 3 4 --fs 18 --out $O/leg_seg3.png \
    --run_dirs $TS $R ${R}_perseg ${R}_vlpart8 ${R}_perseg_vlpart8 \
    --labels "2D two-stage (09-28)" "lifted two-stage" "lifted per-seg" "lifted two-stage, VLPart 8" "lifted per-seg, VLPart 8" > $O/leg_seg3.txt 2>&1 \
    || echo "  leg figure FAILED ($O/leg_seg3.txt)"

echo "##### back-projections (+ SHIC) [$(date -u +%T)]"
B=$O/backproj; mkdir -p $B $L/backproj
[ -f $B/${TAG}_position_color.png ] || python analysis/pixel_coloring.py --img_path $SRC/$TAG.png --mask_path $SRC/${TAG}_mask.pth \
    --mode position --save_dir $B --output_path $B/${TAG}_position_color.png > $B/log.txt 2>&1
for k in "${!PF[@]}"; do
  [ -f ${PF[$k]} ] && [ ! -f $B/${TAG}_${k}_backproj.png ] || continue
  mkdir -p $B/soft_$k
  python analysis/run_in_one_process.py \
    analysis/color_mesh_from_soft_mapping.py --mask_path $SRC/${TAG}_mask.pth --img_path $SRC/$TAG.png --save_dir $B/soft_$k \
      --features_path $SRC/${TAG}_pix_sdsquare_fuse16.pth --vertex_features_path ${PF[$k]} --obj_path $OBJ --name $NAME \
      --color_mode position --color_path $B/${TAG}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
    analysis/color_image_from_knn.py --mask_path $SRC/${TAG}_mask.pth --knn_dir $B/soft_$k \
      --knn_path $B/soft_$k/${TAG}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
      --source_image_path $SRC/$TAG.png --k 1 --save_dir $B --output_path $B/${TAG}_${k}_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
    && echo "  $k done" || echo "  $k FAILED (see $B/log.txt)"
done
if [ ! -f $L/backproj/${TAG}_SHIC_backproj.png ]; then
  mkdir -p $L/backproj/shic
  python analysis/run_in_one_process.py \
    analysis/shic_infer_correspondence.py --class_name $CLASS --image_path $SRC/$TAG.png --mask_path $SRC/${TAG}_mask.pth --save_dir $L/backproj/shic --top_k 10 --- \
    analysis/color_image_from_knn.py --mask_path $SRC/${TAG}_mask.pth --knn_dir $L/backproj/shic --knn_path $L/backproj/shic/${TAG}_shic_pixel_to_vertex_nn.pth \
      --vertex_colors_path $CHK --source_image_path $SRC/$TAG.png --k 1 --save_dir $L/backproj/shic --output_path $L/backproj/${TAG}_SHIC_backproj.png --no_side_by_side \
    >> $B/log.txt 2>&1 && echo "  SHIC done" || echo "  SHIC FAILED"
fi

echo "##### ellipses [$(date -u +%T)]"
for k in "${!MU[@]}"; do
  [ -f ${MU[$k]}/mu_aniso.pth ] || { echo "  $k: no mu_aniso.pth"; continue; }
  python analysis/plot_mu_ellipses.py --run_dir ${MU[$k]} --fine_seg_path ${SEG[$k]} --img_path $SRC/$TAG.png \
      --output_path $O/ellipses_$k.png --title "$k" > $O/ellipses_$k.txt 2>&1 && echo "  $k" || echo "  $k FAILED"
done

echo "##### compose [$(date -u +%T)]"
python analysis/make_horse_lifted_study.py --src $SRC --tag $TAG --study_dir $O --table $L/${TAG}_mask_geo_table_lifted_seed0.pth \
    --maps sam1=$SRC/${TAG}_fine_segments.pth vlp8=$VLP8 --shic_results data/densepose_lvis/eval_shic_$CLASS/results.json \
    --rows_json '[["SAM 1 map, lifted teacher", "sam1", ["zs", "sam1_lifted_stage1", "sam1_lifted_stage2", "sam1_lifted_perseg"]],
                  ["VLPart 8-seg map, lifted teacher", "vlp8", ["zs", "vlp8_lifted_stage1", "vlp8_lifted_stage2", "vlp8_lifted_perseg"]],
                  ["SAM 1 map, 2D teacher (09-28)", "sam1", ["zs", "sam1_2d_stage1", "sam1_2d_stage2", "none"]]]'
echo "HORSE 164135 DONE [$(date -u +%T)]"
