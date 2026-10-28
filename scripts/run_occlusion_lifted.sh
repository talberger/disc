#!/bin/bash
# OCCLUSION + LIFT (Tal, 2026-10-28): bears 206034 (behind a fence) and 237843 (cub behind a tree trunk). pix2gestalt's COMPLETED CONTENT
# (saved 10-08, until now only its mask was used) -> Pixal3D lifts the whole bear -> lifted geodesic table -> our training. Centres stay on
# the VISIBLE pixels only (--object_mask_path = the visible SAM 3 mask); the amodal mask is only the distance domain (as in every amodal run).
# Arms: 2D two-stage (fresh, today's recipe) | lifted from the occluded photo as is ("plain") | lifted from the completed content
# two-stage + hybrid; + SHIC, ZS.
#   STEP=prep   (disc env) inputs: run_lvis_sam3_batch.sh with --keep_intermediates (SAM 3 + amodal masks from the mask cache) -> 2D two-stage,
#               then the RGBA inputs (plain: crop + visible mask; p2g: analysis/make_amodal_rgba.py, sample SMP_<id>).
#               Needs <RUNS>/lvis<id>/lvis<id>_amodal_{input,samples}.npz copied in first (from the RunPod volume, s3get).
#   STEP=lift   (pixal3d env) both lifts of both bears, one call.
#   STEP=train  (disc env) lifted tables + runs (run_lifted_instance.sh), eval, back-projections, figure.
# Usage (Run:ai): STEP=prep bash scripts/run_occlusion_lifted.sh
set -euo pipefail
IDS=${IDS:-"206034 237843"}; declare -A SMP=([206034]=2 [237843]=0)   # Tal 10-28: fence = sample 3 (wires gone), tree = sample 1 (sample 3 has a hole)
R=data/densepose_lvis; RUNS=$R/runs_occ_lifted; RES=$R/results_occ_lifted; OUT=$R/lifted_occ; PX=/workspace/pixal3d_out
STEP=${STEP:?STEP=prep|lift|train}

case $STEP in
prep)
  source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
  for id in $IDS; do [ -f $RUNS/lvis$id/lvis${id}_amodal_samples.npz ] || { echo "lvis$id: no amodal samples in $RUNS/lvis$id (copy them first)"; exit 1; }; done
  CLASS=bear ANN_IDS="$IDS" RESULTS=$RES RUNS=$RUNS WORKER_ARGS=--keep_intermediates bash scripts/run_lvis_sam3_batch.sh
  for id in $IDS; do
    d=$RUNS/lvis$id
    python - $d/lvis$id.png $d/lvis${id}_mask.pth $PX/bear_lvis${id}_occplain_rgba.png <<'EOF'
import sys, numpy as np, torch
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('RGB')); m = torch.load(sys.argv[2]).numpy().astype(bool)
Image.fromarray(np.dstack([im, (m * 255).astype(np.uint8)])).save(sys.argv[3]); print('rgba', sys.argv[3])
EOF
    python analysis/make_amodal_rgba.py --run_dir $d --tag lvis$id --sample ${SMP[$id]} --out_png $PX/bear_lvis${id}_occp2g_rgba.png
  done ;;
lift)
  cd /workspace/pixal3d_repo && source /workspace/envs/pixal3d/bin/activate
  IM=(); TG=(); for id in $IDS; do for v in occplain occp2g; do IM+=($PX/bear_lvis${id}_${v}_rgba.png); TG+=(bear_lvis${id}_$v); done; done
  HF_HUB_OFFLINE=1 HF_HOME=/workspace/.cache/huggingface python /workspace/disc/external/pixal3d/lift.py --images "${IM[@]}" --tags "${TG[@]}" \
      --out_dir $PX/geom --low_vram ;;
train)
  source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
  OBJ=./demo/shic/shapes/bear.obj; NAME=shic_bear; P1=./experiments/shic_bear/encoder_dfd_crossview_phase1
  GEO228=$R/eval_shic_bear/bear_heat_geodesics_228.npy; CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
  for id in $IDS; do
    tag=lvis$id; src=$RUNS/$tag; T2=$src/${tag}_mask_geo_table_2d_seed0.pth
    run() { CLASS=bear TAG=$tag SRC=$src OUT=$OUT T2D=$T2 "$@" bash scripts/run_lifted_instance.sh; }
    run env MODE=twostage LIFT=$PX/geom/bear_${tag}_occplain_lift.pth RUNTAG=_plain || echo "$tag plain FAILED"
    run env MODE=twostage LIFT=$PX/geom/bear_${tag}_occp2g_lift.pth RUNTAG=_p2g || echo "$tag p2g FAILED"
    run env MODE=hybrid   LIFT=$PX/geom/bear_${tag}_occp2g_lift.pth RUNTAG=_p2g || echo "$tag p2g hybrid FAILED"
    L=$OUT/$tag; P=$L/encoder_loraW_all_r4_phase2_lifted; S2=$src/encoder_loraW_all_r4_phase2
    declare -A PF=([zs]=$P1/pred_f.pth [2d_stage1]=$S2/alpha_stageA_end/alpha0.5/pred_f.pth [2d_stage2]=$S2/alpha/alpha0.5/pred_f.pth
                   [plain_stage2]=${P}_plain/alpha/alpha0.5/pred_f.pth [p2g_stage1]=${P}_p2g/alpha_stageA_end/alpha0.5/pred_f.pth
                   [p2g_stage2]=${P}_p2g/alpha/alpha0.5/pred_f.pth [p2g_hybrid]=${P}_hybrid_p2g/alpha/alpha0.5/pred_f.pth)
    ARMS=(); for k in "${!PF[@]}"; do [ -f ${PF[$k]} ] && ARMS+=(--arm $k=${PF[$k]}); done
    python analysis/eval_lvis_ours.py --run_dir $src --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 \
        --out_json $L/multi_eval.json "${ARMS[@]}" > $L/multi_eval.log 2>&1 && echo "  $tag eval: ${#ARMS[@]} args" || echo "  $tag eval FAILED"
    B=$L/backproj; mkdir -p $B
    [ -f $B/${tag}_position_color.png ] || python analysis/pixel_coloring.py --img_path $src/$tag.png --mask_path $src/${tag}_mask.pth \
        --mode position --save_dir $B --output_path $B/${tag}_position_color.png > $B/log.txt 2>&1
    for k in "${!PF[@]}"; do
      [ -f ${PF[$k]} ] && [ ! -f $B/${tag}_${k}_backproj.png ] || continue
      mkdir -p $B/soft_$k
      python analysis/run_in_one_process.py \
        analysis/color_mesh_from_soft_mapping.py --mask_path $src/${tag}_mask.pth --img_path $src/$tag.png --save_dir $B/soft_$k \
          --features_path $src/${tag}_pix_sdsquare_fuse16.pth --vertex_features_path ${PF[$k]} --obj_path $OBJ --name $NAME \
          --color_mode position --color_path $B/${tag}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
        analysis/color_image_from_knn.py --mask_path $src/${tag}_mask.pth --knn_dir $B/soft_$k \
          --knn_path $B/soft_$k/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
          --source_image_path $src/$tag.png --k 1 --save_dir $B --output_path $B/${tag}_${k}_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
        || echo "  $tag $k FAILED"
    done
    if [ ! -f $B/${tag}_SHIC_backproj.png ]; then
      mkdir -p $B/shic
      python analysis/run_in_one_process.py \
        analysis/shic_infer_correspondence.py --class_name bear --image_path $src/$tag.png --mask_path $src/${tag}_mask.pth --save_dir $B/shic --top_k 10 --- \
        analysis/color_image_from_knn.py --mask_path $src/${tag}_mask.pth --knn_dir $B/shic --knn_path $B/shic/${tag}_shic_pixel_to_vertex_nn.pth \
          --vertex_colors_path $CHK --source_image_path $src/$tag.png --k 1 --save_dir $B/shic --output_path $B/${tag}_SHIC_backproj.png --no_side_by_side \
        >> $B/log.txt 2>&1 || echo "  $tag SHIC FAILED"
    fi
    unset PF
  done
  python analysis/make_lifted_multi.py --ids $IDS --crowd $IDS --crowd_name "occluded bears" --out_dir $OUT/summary --lifted_dir $OUT \
      --src_sub $RUNS --src_crowd $RUNS \
      --arms SHIC zs 2d_stage1 2d_stage2 plain_stage2 p2g_stage1 p2g_stage2 p2g_hybrid \
      --panels "SHIC=SHIC" "zs=ZS" "2d_stage2=2D two-stage" "plain_stage2=lifted, occluded photo" "p2g_stage1=lifted completed, stage 1" \
               "p2g_stage2=lifted completed, two-stage" "p2g_hybrid=lifted completed, hybrid" ;;
esac
echo "OCCLUSION LIFTED $STEP DONE [$(date -u +%T)]"
