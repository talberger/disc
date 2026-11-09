#!/bin/bash
# Amodal completion BEFORE the lift, one bear (Tal, 2026-11-09; 32412: the branch + grass cut the mask and Pixal3D folds the head back).
# The full run lifted the visible mask as is (the amodal step only ran for split masks; 32412's is in one piece).
#   STEP=amodal (disc env + pix2gestalt venv, tberger3-disc-gpu3) pix2gestalt FORCED: input -> 3 samples -> merged mask -> RGBA of the
#               completed content (analysis/make_amodal_rgba.py --sample auto) -> /workspace/pixal3d_out/bear_lvis<i>_amodal_rgba.png
#   STEP=lift   (pixal3d env, pixal3d-env2) lift.py + remesh_lift.py, as the full run -> $G/bear_lvis<i>_amodal_lift.pth
#   STEP=train  (disc env) ray-cast table + stage 1 + eval + back-projection (run_stage1_raycast.sh LIFT_SUFFIX=amodal ARM=lifted_amodal)
#               + the stage-1 path study on the new lift + its depth map. Centres and table columns stay on the VISIBLE mask, as every arm.
# Usage: I=32412 STEP=amodal bash scripts/run_amodal_lift_one.sh
set -euo pipefail
I=${I:?}; STEP=${STEP:?STEP=amodal|lift|train}; tag=lvis$I
R=data/densepose_lvis; PX=/workspace/pixal3d_out; G=$PX/geom_full; RGBA=$PX/bear_${tag}_amodal_rgba.png
case $STEP in
amodal)
  source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
  d=$R/runs_full_poly/$tag; A=$R/lifted_full/$tag/amodal; mkdir -p $A
  cp $d/$tag.png $d/${tag}_mask.pth $A/
  python analysis/prep_amodal_input.py --ann_id $I --class_name bear --out_dir $A
  ( cd $DISC_WS/pix2gestalt_repo/pix2gestalt && env -u PYTHONPATH -u CONDA_DEFAULT_ENV PATH=$DISC_WS/pix2gestalt_repo/venv/bin:/usr/local/bin:/usr/bin:/bin \
      PYTHONPATH=../stubs:taming-transformers:CLIP python ../run_amodal.py --run_dirs $(realpath $A) --tags $tag --n_samples 3 --steps 50 )
  python analysis/merge_amodal_mask.py --run_dir $A --tag $tag
  python analysis/make_amodal_rgba.py --run_dir $A --tag $tag --sample auto --out_png $RGBA
  echo "AMODAL RGBA DONE $RGBA" ;;
lift)
  cd /workspace/pixal3d_repo && source /workspace/envs/pixal3d/bin/activate
  HF_HUB_OFFLINE=1 HF_HOME=/workspace/.cache/huggingface python /workspace/disc/external/pixal3d/lift.py --images $RGBA \
      --tags bear_${tag}_amodal --out_dir $G/raw --low_vram
  python /workspace/disc/external/pixal3d/remesh_lift.py --lifts $G/raw/bear_${tag}_amodal_lift.pth --out_dir $G
  echo "AMODAL LIFT DONE $G/bear_${tag}_amodal_lift.pth" ;;
train)
  source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
  IDS=$I LIFT_SUFFIX=amodal ARM=lifted_amodal bash scripts/run_stage1_raycast.sh
  echo "AMODAL TRAIN DONE" ;;
esac
