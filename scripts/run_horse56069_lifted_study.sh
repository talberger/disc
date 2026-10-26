#!/bin/bash
# Horse 56069 study with the LIFTED geodesic teacher (Tal, 2026-10-26). Two segment maps x the stages:
#   SAM 1 map (4 segs, the one used so far)          : ZS | stage 1 | stage 2 (= two-stage final) | per-seg only (stage 2 without stage 1)
#   VLPart pascal_part>=0.5 (5 segs, head split off) : same four
# + 2D-teacher references on the SAM 1 map (two-stage final, per-seg only). Outputs in data/densepose_lvis/lifted/lvis56069/study/:
#   backproj_study.png (rows = map / teacher, cols = photo | segments + centres | ZS | stage 1 | stage 2 | per-seg), ellipses_<run>.png (learned mu
#   per segment, scripts' plot_mu_ellipses.py), segments_centres.png, study_summary.txt (per point + mean).
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
TAG=lvis56069; CLASS=horse
SRC=data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/$TAG
VLP=data/densepose_lvis/fine_segments_vlpart/${TAG}_fine_segments_pascalpart_thr0.5.pth
VLP4=data/densepose_lvis/fine_segments_vlpart/${TAG}_fine_segments_partimagenet_thr0.3.pth   # 4 segs (pod 52's map)
LIFT=/workspace/pixal3d_out/geom/horse_${TAG}_lift.pth
L=data/densepose_lvis/lifted/$TAG; O=$L/study; mkdir -p $O
OBJ=./demo/shic/shapes/$CLASS.obj; NAME=shic_$CLASS; P1=./experiments/shic_$CLASS/encoder_dfd_crossview_phase1
CHK=demo/shic/colored_mesh/${CLASS}_mesh_checker16_uv_color.pth
GEO228=data/densepose_lvis/eval_shic_$CLASS/${CLASS}_heat_geodesics_228.npy

echo "##### training [$(date -u +%T)]"
run() { CLASS=$CLASS TAG=$TAG SRC=$SRC LIFT=$LIFT "$@" bash scripts/run_lifted_instance.sh; }
run env MODE=twostage                               # exists -> eval only
run env MODE=perseg
run env MODE=twostage FINESEG=$VLP RUNTAG=_vlpart5
run env MODE=perseg   FINESEG=$VLP RUNTAG=_vlpart5
# VLPart partimagenet>=0.3 (4 segs; Tal 10-26): the two trainings side by side on the GPU
run env MODE=twostage FINESEG=$VLP4 RUNTAG=_vlpart4 & run env MODE=perseg FINESEG=$VLP4 RUNTAG=_vlpart4 & wait
# HYBRID (Tal 2026-10-26): stage 1 + 2 together, one stage -- in-seg pairs on the segment ellipse, cross-seg pairs on one global ellipse
run env MODE=hybrid & run env MODE=hybrid FINESEG=$VLP RUNTAG=_vlpart5 & run env MODE=hybrid FINESEG=$VLP4 RUNTAG=_vlpart4 & wait

# run dirs: name | pred_f | segment map | mu run dir (for the ellipses)
R=$L/encoder_loraW_all_r4_phase2_lifted
declare -A PF SEG MU
PF[zs]=$P1/pred_f.pth
PF[sam1_lifted_stage1]=$R/alpha_stageA_end/alpha0.5/pred_f.pth;            SEG[sam1_lifted_stage1]=$SRC/${TAG}_fine_segments.pth
PF[sam1_lifted_stage2]=$R/alpha/alpha0.5/pred_f.pth;                       SEG[sam1_lifted_stage2]=$SRC/${TAG}_fine_segments.pth; MU[sam1_lifted_stage2]=$R
PF[sam1_lifted_perseg]=${R}_perseg/alpha/alpha0.5/pred_f.pth;              SEG[sam1_lifted_perseg]=$SRC/${TAG}_fine_segments.pth; MU[sam1_lifted_perseg]=${R}_perseg
PF[vlp_lifted_stage1]=${R}_vlpart5/alpha_stageA_end/alpha0.5/pred_f.pth;   SEG[vlp_lifted_stage1]=$VLP
PF[vlp_lifted_stage2]=${R}_vlpart5/alpha/alpha0.5/pred_f.pth;              SEG[vlp_lifted_stage2]=$VLP; MU[vlp_lifted_stage2]=${R}_vlpart5
PF[vlp_lifted_perseg]=${R}_perseg_vlpart5/alpha/alpha0.5/pred_f.pth;       SEG[vlp_lifted_perseg]=$VLP; MU[vlp_lifted_perseg]=${R}_perseg_vlpart5
PF[vlp4_lifted_stage1]=${R}_vlpart4/alpha_stageA_end/alpha0.5/pred_f.pth;   SEG[vlp4_lifted_stage1]=$VLP4
PF[vlp4_lifted_stage2]=${R}_vlpart4/alpha/alpha0.5/pred_f.pth;              SEG[vlp4_lifted_stage2]=$VLP4; MU[vlp4_lifted_stage2]=${R}_vlpart4
PF[vlp4_lifted_perseg]=${R}_perseg_vlpart4/alpha/alpha0.5/pred_f.pth;       SEG[vlp4_lifted_perseg]=$VLP4; MU[vlp4_lifted_perseg]=${R}_perseg_vlpart4
PF[sam1_lifted_hybrid]=${R}_hybrid/alpha/alpha0.5/pred_f.pth;          SEG[sam1_lifted_hybrid]=$SRC/${TAG}_fine_segments.pth; MU[sam1_lifted_hybrid]=${R}_hybrid
PF[vlp_lifted_hybrid]=${R}_hybrid_vlpart5/alpha/alpha0.5/pred_f.pth;     SEG[vlp_lifted_hybrid]=$VLP; MU[vlp_lifted_hybrid]=${R}_hybrid_vlpart5
PF[vlp4_lifted_hybrid]=${R}_hybrid_vlpart4/alpha/alpha0.5/pred_f.pth;    SEG[vlp4_lifted_hybrid]=$VLP4; MU[vlp4_lifted_hybrid]=${R}_hybrid_vlpart4
PF[sam1_2d_stage2]=$SRC/encoder_loraW_all_r4_phase2/alpha/alpha0.5/pred_f.pth; SEG[sam1_2d_stage2]=$SRC/${TAG}_fine_segments.pth; MU[sam1_2d_stage2]=$SRC/encoder_loraW_all_r4_phase2
PF[sam1_2d_perseg]=data/densepose_lvis/runs_xseg/$TAG/perseg/alpha/alpha0.5/pred_f.pth; SEG[sam1_2d_perseg]=$SRC/${TAG}_fine_segments.pth; MU[sam1_2d_perseg]=data/densepose_lvis/runs_xseg/$TAG/perseg
[ -f $SRC/encoder_loraW_all_r4_phase2/alpha_stageA_end/alpha0.5/pred_f.pth ] && PF[sam1_2d_stage1]=$SRC/encoder_loraW_all_r4_phase2/alpha_stageA_end/alpha0.5/pred_f.pth

echo "##### eval of every arm [$(date -u +%T)]"
ARMS=(); for k in "${!PF[@]}"; do [ -f ${PF[$k]} ] && ARMS+=(--arm $k=${PF[$k]}); done
python analysis/eval_lvis_ours.py --run_dir $SRC --tag $TAG --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $O/study_eval.json "${ARMS[@]}" > $O/eval.log 2>&1

echo "##### back-projections [$(date -u +%T)]"
B=$O/backproj; mkdir -p $B
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

echo "##### ellipses [$(date -u +%T)]"
for k in "${!MU[@]}"; do
  [ -f ${MU[$k]}/mu_aniso.pth ] || { echo "  $k: no mu_aniso.pth"; continue; }
  python analysis/plot_mu_ellipses.py --run_dir ${MU[$k]} --fine_seg_path ${SEG[$k]} --img_path $SRC/$TAG.png \
      --output_path $O/ellipses_$k.png --title "$k" > $O/ellipses_$k.txt 2>&1 && echo "  $k" || echo "  $k FAILED ($O/ellipses_$k.txt)"
done

echo "##### compose [$(date -u +%T)]"
python analysis/make_horse_lifted_study.py --src $SRC --tag $TAG --study_dir $O --table $L/${TAG}_mask_geo_table_lifted_seed0.pth \
    --maps sam1=$SRC/${TAG}_fine_segments.pth vlp=$VLP vlp4=$VLP4 --shic_results data/densepose_lvis/eval_shic_$CLASS/results.json
echo "STUDY DONE [$(date -u +%T)]"
