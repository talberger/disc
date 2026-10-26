#!/bin/bash
# The LIFTED-teacher comparison on many bears (Tal, 2026-10-26): the 20-bear subset (data/densepose_lvis/subset20_bear.json) + the 4 crowded
# bears of 10-26, SAM 1 segment map. Per bear, all with the lifted (Pixal3D mesh) geodesic teacher: stage 1 (global ellipse, end of the
# two-stage), stage 2 (two-stage final), per-seg only, hybrid (stage 1 + 2 together) -- vs SHIC, ZS and the 2D-teacher runs that exist
# (two-stage stage 1 / final; per-seg only on the subset, from the XSEG run of 10-24).
#   STEP=rgba   the RGBA inputs for external/pixal3d/lift.py (crop + our mask as alpha) -> /workspace/pixal3d_out/bear_lvis<id>_rgba.png
#   STEP=train  per bear: two-stage (builds the lifted table) then per-seg + hybrid side by side; LANES bears at a time (default 2). Resumable.
#   STEP=eval   one eval_lvis_ours.py per bear with every arm -> data/densepose_lvis/lifted/<tag>/multi_eval.json
#   STEP=figs   back-projections per arm (+ SHIC) and the figures + summary (analysis/make_lifted_multi.py)
# Usage (disc env, Run:ai tberger3-disc-gpu2): STEP=train bash scripts/run_lifted_bears.sh     (IDS="..." to restrict)
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
SUB=$(python -c "import json; print(' '.join(map(str, json.load(open('data/densepose_lvis/subset20_bear.json'))['ann_ids'])))")
CROWD="159218 212408 31383 154651"
IDS=${IDS:-"$SUB $CROWD"}; LANES=${LANES:-2}; STEP=${STEP:?STEP=rgba|train|eval|figs}
export CLASS=bear
src_of() { case " $CROWD " in *" $1 "*) echo data/densepose_lvis/runs_runai_crowd/lvis$1 ;; *) echo data/densepose_lvis/runs_runai_sub20/lvis$1 ;; esac; }
export -f src_of; export CROWD

case $STEP in
rgba)
  for id in $IDS; do
    out=/workspace/pixal3d_out/bear_lvis${id}_rgba.png; [ -f $out ] && continue
    python - $(src_of $id) $id $out <<'EOF'
import sys, numpy as np, torch
from PIL import Image
d, i, out = sys.argv[1:]
im = np.array(Image.open(f'{d}/lvis{i}.png').convert('RGB')); m = torch.load(f'{d}/lvis{i}_mask.pth').numpy().astype(bool)
Image.fromarray(np.dstack([im, (m * 255).astype(np.uint8)])).save(out); print('rgba', i, im.shape)
EOF
  done ;;
train)
  one_bear() {
    local id=$1 src; src=$(src_of $id)
    local lift=/workspace/pixal3d_out/geom/bear_lvis${id}_lift.pth
    [ -f $lift ] || { echo "lvis$id: NO LIFT, skipped"; return 0; }
    run() { TAG=lvis$id SRC=$src LIFT=$lift "$@" bash scripts/run_lifted_instance.sh; }
    run env MODE=twostage || echo "lvis$id twostage FAILED"
    run env MODE=perseg & run env MODE=hybrid & wait
    echo "BEAR DONE lvis$id"
  }
  export -f one_bear
  printf '%s\n' $IDS | xargs -P $LANES -I{} bash -c 'one_bear {}' ;;
eval|figs)
  OBJ=./demo/shic/shapes/bear.obj; NAME=shic_bear; P1=./experiments/shic_bear/encoder_dfd_crossview_phase1
  GEO228=data/densepose_lvis/eval_shic_bear/bear_heat_geodesics_228.npy
  CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
  for id in $IDS; do
    tag=lvis$id; src=$(src_of $id); L=data/densepose_lvis/lifted/$tag; R=$L/encoder_loraW_all_r4_phase2_lifted; S2=$src/encoder_loraW_all_r4_phase2
    declare -A PF=([zs]=$P1/pred_f.pth [lifted_stage1]=$R/alpha_stageA_end/alpha0.5/pred_f.pth [lifted_stage2]=$R/alpha/alpha0.5/pred_f.pth
                   [lifted_perseg]=${R}_perseg/alpha/alpha0.5/pred_f.pth [lifted_hybrid]=${R}_hybrid/alpha/alpha0.5/pred_f.pth
                   [2d_stage1]=$S2/alpha_stageA_end/alpha0.5/pred_f.pth [2d_stage2]=$S2/alpha/alpha0.5/pred_f.pth
                   [2d_perseg]=data/densepose_lvis/runs_xseg_bears_runai_sub20/$tag/perseg/alpha/alpha0.5/pred_f.pth)
    if [ $STEP = eval ]; then
      ARMS=(); for k in "${!PF[@]}"; do [ -f ${PF[$k]} ] && ARMS+=(--arm $k=${PF[$k]}); done
      python analysis/eval_lvis_ours.py --run_dir $src --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 \
          --out_json $L/multi_eval.json "${ARMS[@]}" > $L/multi_eval.log 2>&1 && echo "  $tag eval: ${#ARMS[@]} args" || echo "  $tag eval FAILED"
    else
      B=$L/backproj; mkdir -p $B
      [ -f $B/${tag}_position_color.png ] || python analysis/pixel_coloring.py --img_path $src/$tag.png --mask_path $src/${tag}_mask.pth \
          --mode position --save_dir $B --output_path $B/${tag}_position_color.png > $B/log.txt 2>&1
      for k in zs lifted_stage1 lifted_stage2 lifted_perseg lifted_hybrid 2d_stage2; do
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
      echo "  $tag figs"
    fi
    unset PF
  done
  if [ $STEP = figs ]; then
    python analysis/make_lifted_multi.py --ids $IDS --crowd $CROWD --out_dir data/densepose_lvis/lifted/multi \
        --src_sub data/densepose_lvis/runs_runai_sub20 --src_crowd data/densepose_lvis/runs_runai_crowd
  fi ;;
esac
echo "LIFTED BEARS $STEP DONE [$(date -u +%T)]"
