#!/bin/bash
# Amodal content BEFORE the lift, all bears of the full run (Tal, 2026-11-09; after 32412: the completed image gives a lift with the head in
# front instead of folded back). Arms per bear (stage 1, ray-cast table): lifted_ray (the full run's lift) and lifted_amodal (lift of the
# pix2gestalt-completed image). Bears whose mask was split already got the amodal content in the full run (run_full_lifted.sh): their amodal
# lift is a symlink to the full one and lifted_amodal reuses lifted_ray.
#   STEP=amodal (disc env + pix2gestalt venv, tberger3-disc-gpu3) per bear prep -> ONE pix2gestalt call (model loads once) -> merge ->
#               RGBA of the completed content (make_amodal_rgba.py --sample auto) -> $PX/bear_lvis<i>_amodal_rgba.png
#   STEP=lift   (pixal3d env, pixal3d-env2) lift.py on every RGBA without a lift (models load once) -> remesh_lift.py -> the raw lifts deleted
#   STEP=train  (disc env) run_stage1_raycast.sh ARMS="lifted_ray=full lifted_amodal=amodal", then the summary
# Every step is resumable (skips what exists). Ids = lifted_full/summary/summary.txt (the 132 bears of the full run), or IDS="...".
# Usage: STEP=amodal bash scripts/run_amodal_lift_all.sh
set -euo pipefail
STEP=${STEP:?STEP=amodal|lift|train}
R=data/densepose_lvis; PX=/workspace/pixal3d_out; G=$PX/geom_full; cd /workspace/disc
IDS=${IDS:-$(awk '$1 ~ /^[0-9]+$/ {print $1}' $R/lifted_full/summary/summary.txt)}
echo "$(echo $IDS | wc -w) bears"
case $STEP in
amodal)
  source /workspace/disc/env/activate.sh
  DIRS=(); TAGS=()
  for i in $IDS; do
    d=$R/runs_full_poly/lvis$i; tag=lvis$i
    if [ -f $d/${tag}_amodal_samples.npz ]; then                          # split mask: the full run's lift is already amodal
      ln -sfn bear_${tag}_full_lift.pth $G/bear_${tag}_amodal_lift.pth; continue; fi
    [ -f $PX/bear_${tag}_amodal_rgba.png ] && continue
    A=$(realpath -m $R/lifted_full/$tag/amodal); mkdir -p $A; cp $d/$tag.png $d/${tag}_mask.pth $A/
    [ -f $A/${tag}_amodal_input.npz ] || python analysis/prep_amodal_input.py --ann_id $i --class_name bear --out_dir $A > $A/prep.log 2>&1 \
      || { echo "lvis$i prep FAILED"; continue; }
    DIRS+=($A); TAGS+=($tag)
  done
  echo "pix2gestalt for ${#TAGS[@]} bears"
  todo=(); for k in "${!TAGS[@]}"; do [ -f ${DIRS[$k]}/${TAGS[$k]}_amodal_samples.npz ] || todo+=($k); done
  if [ ${#todo[@]} -gt 0 ]; then
    D2=(); T2=(); for k in "${todo[@]}"; do D2+=(${DIRS[$k]}); T2+=(${TAGS[$k]}); done
    ( cd $DISC_WS/pix2gestalt_repo/pix2gestalt && env -u PYTHONPATH -u CONDA_DEFAULT_ENV PATH=$DISC_WS/pix2gestalt_repo/venv/bin:/usr/local/bin:/usr/bin:/bin \
        PYTHONPATH=../stubs:taming-transformers:CLIP python ../run_amodal.py --run_dirs "${D2[@]}" --tags "${T2[@]}" --n_samples 3 --steps 50 ) 2>&1 \
        | grep -vE 'DDIM|Sampler|it/s' || true
  fi
  for k in "${!TAGS[@]}"; do
    A=${DIRS[$k]}; tag=${TAGS[$k]}
    [ -f $A/${tag}_amodal_samples.npz ] || { echo "$tag: no samples"; continue; }
    python analysis/merge_amodal_mask.py --run_dir $A --tag $tag > $A/merge.log 2>&1 \
      && python analysis/make_amodal_rgba.py --run_dir $A --tag $tag --sample auto --out_png $PX/bear_${tag}_amodal_rgba.png | cut -c1-160 \
      || echo "$tag merge/rgba FAILED"
  done
  echo "AMODAL ALL DONE" ;;
lift)
  cd /workspace/pixal3d_repo && source /workspace/envs/pixal3d/bin/activate
  IM=(); TG=(); for i in $IDS; do
    [ -e $G/bear_lvis${i}_amodal_lift.pth ] && continue; [ -f $PX/bear_lvis${i}_amodal_rgba.png ] || { echo "lvis$i: no amodal RGBA"; continue; }
    IM+=($PX/bear_lvis${i}_amodal_rgba.png); TG+=(bear_lvis${i}_amodal); done
  echo "lift ${#IM[@]} images"
  if [ ${#IM[@]} -gt 0 ]; then
    HF_HUB_OFFLINE=1 HF_HOME=/workspace/.cache/huggingface python /workspace/disc/external/pixal3d/lift.py --images "${IM[@]}" --tags "${TG[@]}" \
        --out_dir $G/raw --low_vram 2>&1 | grep -E '^\[lift\].*(mesh|IoU)|FAILED|DONE' || true
    RAW=(); for t in "${TG[@]}"; do [ -f $G/raw/${t}_lift.pth ] && RAW+=($G/raw/${t}_lift.pth); done
    [ ${#RAW[@]} -gt 0 ] && python /workspace/disc/external/pixal3d/remesh_lift.py --lifts "${RAW[@]}" --out_dir $G | grep -E "REMESH|Error"
    for t in "${TG[@]}"; do [ -f $G/${t}_lift.pth ] && rm -f $G/raw/${t}_lift.pth; done   # keep only the remeshed lift (PVC space)
  fi
  echo "LIFT ALL DONE" ;;
train)   # only bears whose amodal lift exists (run again after STEP=lift finishes for the rest)
  READY=$(for i in $IDS; do [ -e $G/bear_lvis${i}_amodal_lift.pth ] && echo $i; done); echo "train: $(echo $READY | wc -w) bears ready"
  IDS="$READY" ARMS="lifted_ray=full lifted_amodal=amodal" bash /workspace/disc/scripts/run_stage1_raycast.sh
  echo "TRAIN ALL DONE" ;;
esac
