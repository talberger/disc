#!/bin/bash
# SHORT RUN OF A WHOLE CLASS (Tal, 2026-11-11: "the other animals", horse then elephant; every DensePose-LVIS ds2_val instance with GT
# points). Per instance: crop + LVIS polygon mask + fine segments (SAM 1, merge 1.5%, fill) -> pix2gestalt content completion -> Pixal3D
# lift of the completed image (remeshed) -> stage 1 ONLY (global ellipse, 149 steps) on the lifted teacher with --pix_map triangle
# (run_stage1_raycast.sh, arm lifted_amodal) -> back-projection + eval (arms zs, lifted_amodal). As the bears: the amodal mask is the
# geodesic domain only where the visible mask is split. No 2D arm, no SHIC back-projection here (later passes, they need only the inputs).
# Three ROLES that hand over through files on the PVC, so each runs in its own workspace and all can be started at once:
#   ROLE=prep  (disc image)    PARTS / NPART = this run's share of the list (index % NPART in PARTS); NGPU GPUs, PLANES processes per GPU.
#              -> $PX/<class>_lvis<i>_amodal_rgba.png + .ready ; $ST/prep_part<k>.done when a part is finished
#   ROLE=lift  (pixal3d image) NGPU GPUs, each takes ready images in batches under a claim folder ($ST/lift_claim_<i>: several workspaces may
#              lift the same list; the models take minutes to load: waits for MINB images while prep still runs), lift.py --low_vram -> remesh_lift.py -> $G/<class>_lvis<i>_amodal_lift.pth
#              -> $ST/lift.done when prep is done and nothing is left
#   ROLE=train (disc image)    NGPU GPUs x LANES workers; every worker walks the WHOLE list (instances are locked per worker, so several
#              workspaces share it) and trains what has a lift; ends when lift.done exists and nothing is left.
# Kept per instance: inputs, lift (~30 MB), eval_all.json, back-projection, ellipse; pred_f deleted (LEAN=1). Everything is resumable.
# Assets of the class first: scripts/run_shicclass_setup.sh (+ the 3D geodesic table). State + logs: /workspace/logs/short_<class><RUNTAG>/.
# Usage: CLASS=horse ROLE=prep PARTS="0" NPART=4 NGPU=1 bash scripts/run_class_short.sh
#        CLASS=horse ROLE=lift NGPU=2 bash scripts/run_class_short.sh ;  CLASS=horse ROLE=train NGPU=1 LANES=6 bash scripts/run_class_short.sh
#        a test: IDS="..." RUNTAG=_test (its own state folder; the instances it finishes are skipped by the full run)
set -uo pipefail   # no -e: one bad instance must not stop the night
ROLE=${ROLE:?ROLE=prep|lift|train}; CLASS=${CLASS:?CLASS=horse|elephant}
R=data/densepose_lvis; RUNS=$R/runs_${CLASS}_poly; LROOT=$R/lifted_$CLASS; PX=/workspace/pixal3d_out; G=$PX/geom_full
ST=/workspace/logs/short_$CLASS${RUNTAG:-}; NGPU=${NGPU:-1}; NPART=${NPART:-1}; PARTS=${PARTS:-0}
cd /workspace/disc; mkdir -p $ST $RUNS $LROOT $G/raw
if [ ! -s $ST/ids.txt ]; then
  if [ -n "${IDS:-}" ]; then echo $IDS | tr ' ' '\n' > $ST/ids.txt.$$
  else python3 -c "
import json; d = json.load(open('$R/densepose_lvis_v1_ds2_val_v1.json')); cat = {c['id']: c['name'] for c in d['categories']}
print('\n'.join(str(i) for i in sorted(a['id'] for a in d['annotations'] if cat[a['category_id']] == '$CLASS' and a.get('dp_x'))))" > $ST/ids.txt.$$
  fi
  mv -n $ST/ids.txt.$$ $ST/ids.txt; rm -f $ST/ids.txt.$$
fi
ALL=$(cat $ST/ids.txt); N=$(echo $ALL | wc -w)
echo "##### $CLASS $ROLE: $N instances, $NGPU GPU(s) [$(date -u +%FT%T)] #####"
export CLASS R RUNS LROOT PX G ST

case $ROLE in
prep)
  source env/activate.sh
  PLANES=${PLANES:-2}; CHUNK=${CHUNK:-40}
  echo $NPART > $ST/nparts
  MINE=$(echo $ALL | tr ' ' '\n' | awk -v n=$NPART -v p=" $PARTS " 'index(p, " " ((NR - 1) % n) " ")')
  echo "prep: $(echo $MINE | wc -w) instances (parts $PARTS of $NPART)"
  prep_one() {   # crop + polygon mask + GT, fine segments, the pix2gestalt input
    local i=$1 tag=lvis$1; local d=$RUNS/$tag A=$LROOT/$tag/amodal
    [ -f $PX/${CLASS}_${tag}_amodal.ready ] && return 0
    [ -f $d/${tag}_fine_segments.pth ] && [ -f $A/${tag}_amodal_input.npz ] && return 0
    mkdir -p $d $A
    python analysis/run_in_one_process.py \
      analysis/prep_lvis_instance.py --ann_id $i --class_name $CLASS --out_dir $d --long_side 400 --mask_source polygon --- \
      analysis/build_fine_segments.py --img_path $d/$tag.png --mask_path $d/${tag}_mask.pth --save_dir $d --min_pixels_in_object 50 \
        --merge_below_frac 0.015 --fill_unlabelled --- \
      analysis/prep_amodal_input.py --ann_id $i --class_name $CLASS --out_dir $A > $d/prep.log 2>&1 || echo "lvis$i prep FAILED"
  }
  finish_one() {   # merged amodal mask, the completed RGBA for the lift, the amodal domain where the mask is split; else the visible RGBA
    local i=$1 tag=lvis$1; local d=$RUNS/$tag A=$LROOT/$tag/amodal; local o=$PX/${CLASS}_${tag}_amodal_rgba.png
    [ -f $PX/${CLASS}_${tag}_amodal.ready ] && return 0
    [ -f $d/${tag}_fine_segments.pth ] || return 0
    cp $d/$tag.png $d/${tag}_mask.pth $A/
    if [ -f $A/${tag}_amodal_samples.npz ] && python analysis/run_in_one_process.py \
        analysis/merge_amodal_mask.py --run_dir $A --tag $tag --- \
        analysis/make_amodal_rgba.py --run_dir $A --tag $tag --sample auto --out_png $o --- \
        analysis/amodal_domain_if_split.py --run_dir $d --amodal_dir $A --tag $tag > $A/merge.log 2>&1; then :
    else
      echo "lvis$i: no amodal content, lift of the visible crop"; touch $A/FALLBACK_VISIBLE; rm -f $d/${tag}_amodal_mask.pth
      python -c "
import sys, numpy as np, torch
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('RGB')); m = torch.load(sys.argv[2]).numpy().astype(bool)
Image.fromarray(np.dstack([im, (m * 255).astype(np.uint8)])).save(sys.argv[3])" $d/$tag.png $d/${tag}_mask.pth $o || { echo "lvis$i RGBA FAILED"; return 0; }
    fi
    touch $PX/${CLASS}_${tag}_amodal.ready
  }
  export -f prep_one finish_one
  gpu_lane() {
    local g=$1; shift; export CUDA_VISIBLE_DEVICES=$g
    while [ $# -gt 0 ]; do
      local ids="${*:1:$CHUNK}"; shift $(( $# < CHUNK ? $# : CHUNK ))
      echo $ids | tr ' ' '\n' | xargs -P $PLANES -I{} bash -c 'prep_one {}'
      local D2=() T2=() i
      for i in $ids; do prep_one $i; done   # one at a time: whoever failed in parallel (SAM out of GPU memory); a no-op for the rest
      for i in $ids; do local A=$LROOT/lvis$i/amodal
        [ -f $PX/${CLASS}_lvis${i}_amodal.ready ] && continue
        [ -f $A/lvis${i}_amodal_input.npz ] && [ ! -f $A/lvis${i}_amodal_samples.npz ] && { D2+=($(realpath $A)); T2+=(lvis$i); }
      done
      if [ ${#T2[@]} -gt 0 ]; then
        ( cd $DISC_WS/pix2gestalt_repo/pix2gestalt && env -u PYTHONPATH -u CONDA_DEFAULT_ENV PATH=$DISC_WS/pix2gestalt_repo/venv/bin:/usr/local/bin:/usr/bin:/bin \
            PYTHONPATH=../stubs:taming-transformers:CLIP python ../run_amodal.py --run_dirs "${D2[@]}" --tags "${T2[@]}" --n_samples 3 --steps 50 ) 2>&1 \
            | grep -vE 'DDIM|Sampler|it/s'
      fi
      echo $ids | tr ' ' '\n' | xargs -P $PLANES -I{} bash -c 'finish_one {}'
      echo "gpu $g: chunk done, $(ls $PX | grep -c "^${CLASS}_.*_amodal.ready$") ready in all [$(date -u +%T)]"
    done
  }
  for g in $(seq 0 $((NGPU - 1))); do
    gpu_lane $g $(echo $MINE | tr ' ' '\n' | awk -v g=$g -v n=$NGPU '(NR - 1) % n == g') > $ST/prep_p$(echo $PARTS | tr -d ' ')_gpu$g.log 2>&1 &
  done; wait
  for k in $PARTS; do touch $ST/prep_part$k.done; done
  echo "PREP DONE [$(date -u +%T)]" ;;

lift)
  cd /workspace/pixal3d_repo && source /workspace/envs/pixal3d/bin/activate
  MINB=${MINB:-20}; BATCH=${BATCH:-40}
  remesh() {   # raw lifts -> the cleaned lift; the raw one deleted (PVC space)
    [ $# -gt 0 ] || return 0
    python /workspace/disc/external/pixal3d/remesh_lift.py --lifts "$@" --out_dir $G | grep -E "REMESH|Error"
    local r; for r in "$@"; do [ -f $G/$(basename $r) ] && rm -f $r; done
  }
  claim() {   # one lane of one workspace per image (several lift runs may share the list); a claim older than 3 h is taken over
    local c=$ST/lift_claim_$1
    [ -d $c ] && [ -n "$(find $c -maxdepth 0 -mmin +180)" ] && rmdir $c 2>/dev/null
    mkdir $c 2>/dev/null
  }
  gpu_lane() {
    local g=$1 t i left; export CUDA_VISIBLE_DEVICES=$g
    while :; do
      local IM=() TG=() RAW=(); left=0
      for i in $ALL; do t=${CLASS}_lvis${i}_amodal
        [ -e $G/${t}_lift.pth ] || [ -f $ST/lift_failed_$i ] && continue
        left=$((left + 1)); [ -f $PX/$t.ready ] && [ ${#IM[@]} -lt $BATCH ] && claim $i || continue
        if [ -f $G/raw/${t}_lift.pth ]; then RAW+=($G/raw/${t}_lift.pth); TG+=($t)   # left by a run that stopped between lift and remesh
        else IM+=($PX/${t}_rgba.png); TG+=($t); fi
      done
      local prepdone=0; [ $(ls $ST | grep -c '^prep_part.*\.done$') -ge $(cat $ST/nparts 2>/dev/null || echo 1) ] && prepdone=1
      if [ $left -eq 0 ] && [ $prepdone = 1 ]; then break; fi
      if [ ${#TG[@]} -lt $MINB ] && { [ $prepdone = 0 ] || [ ${#TG[@]} -eq 0 ]; }; then   # too few yet, or the rest is held by another lane
        for t in "${TG[@]+"${TG[@]}"}"; do i=${t#${CLASS}_lvis}; rmdir $ST/lift_claim_${i%_amodal}; done; sleep 60; continue
      fi
      echo "gpu $g: lift ${#IM[@]} images [$(date -u +%T)]"
      [ ${#IM[@]} -gt 0 ] && HF_HUB_OFFLINE=1 HF_HOME=/workspace/.cache/huggingface python /workspace/disc/external/pixal3d/lift.py --images "${IM[@]}" \
          --tags "${TG[@]:${#RAW[@]}}" --out_dir $G/raw --low_vram 2>&1 | grep -E '^\[lift\].*(loaded|mesh|IoU)|FAILED|DONE|Error'
      RAW=(); for t in "${TG[@]}"; do [ -f $G/raw/${t}_lift.pth ] && RAW+=($G/raw/${t}_lift.pth); done
      remesh "${RAW[@]+"${RAW[@]}"}"
      for t in "${TG[@]}"; do i=${t#${CLASS}_lvis}; i=${i%_amodal}
        [ -e $G/${t}_lift.pth ] || { echo "lvis$i: NO LIFT"; touch $ST/lift_failed_$i; }; done
    done
    echo "gpu $g: LIFT LANE DONE [$(date -u +%T)]"
  }
  for g in $(seq 0 $((NGPU - 1))); do gpu_lane $g > $ST/lift_$(hostname)_gpu$g.log 2>&1 & done; wait
  touch $ST/lift.done; echo "LIFT DONE [$(date -u +%T)]" ;;

train)
  LANES=${LANES:-3}
  worker() {
    local g=$1 w=$2 i did idle=0; export CUDA_VISIBLE_DEVICES=$g
    while :; do
      did=0
      for i in $(echo $ALL | tr ' ' '\n' | awk -v o=$((RANDOM % N)) '{a[NR] = $0} END {for (k = 0; k < NR; k++) print a[(k + o) % NR + 1]}'); do
        local O=$LROOT/lvis$i/stage1_tri
        [ -f $O/eval_all.json ] && continue
        [ -e $G/${CLASS}_lvis${i}_amodal_lift.pth ] || continue
        [ -d $O/.lock ] && [ -z "$(find $O/.lock -maxdepth 0 -mmin +60)" ] && continue
        [ $(cat $ST/train_failed_$i 2>/dev/null | wc -l) -ge 2 ] && continue
        IDS=$i ARMS="lifted_amodal=amodal" PIXMAP=triangle OUT=stage1_tri LEAN=1 bash scripts/run_stage1_raycast.sh 2>&1 | grep -E "^STAGE1|FAILED|Error|error:"
        if [ -f $O/eval_all.json ]; then did=1; elif [ ! -d $O/.lock ]; then echo "lvis$i FAILED (gpu $g worker $w)"; echo x >> $ST/train_failed_$i; fi
      done
      [ $did = 1 ] && { idle=0; continue; }
      [ -f $ST/lift.done ] && break
      idle=$((idle + 1)); [ $idle -gt 180 ] && { echo "gpu $g worker $w: nothing to train for 3 h, stop"; break; }
      sleep 60
    done
    echo "gpu $g worker $w: DONE [$(date -u +%T)]"
  }
  for g in $(seq 0 $((NGPU - 1))); do for w in $(seq 1 $LANES); do worker $g $w > $ST/train_$(hostname)_gpu${g}_w$w.log 2>&1 & done; done; wait
  n=$(ls $LROOT/lvis*/stage1_tri/eval_all.json 2>/dev/null | wc -l); echo "TRAIN DONE: $n of $N evaluated [$(date -u +%T)]" ;;
esac
