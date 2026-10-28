#!/bin/bash
# FULL BEAR RUN, lifted vs 2D (Tal, 2026-10-28). Every DensePose-LVIS bear (ds2_val, with GT points); object mask = the LVIS GT POLYGON
# (results marked *: isolates "does the lift help" from mask errors); fine segments SAM 1 (merge 1.5%, fillseg). Occluded instances (polygon
# split, largest part < 95%): pix2gestalt CONTENT completion -> amodal mask (2D distances through it) + the completed RGBA for the lift.
# Lifts cleaned with external/pixal3d/remesh_lift.py (the raw Pixal3D mesh has holes / loose pieces).
# Arms: 2D two-stage (its stage 1 = 2d_stage1) | 2D per-seg | lifted two-stage (lifted_stage1 = its stage-A end) | lifted hybrid; + ZS, SHIC.
# Centres always on VISIBLE pixels. Per bear after eval + back-projections: checkpoints, geo tables and features are deleted (Tal 10-28).
#   STEP=prep   (disc ws) crops + polygon masks, split check, pix2gestalt for the split ones, merged amodal masks
#   STEP=train2d (disc ws) 2D two-stage (run_lvis_worker.py, one worker per GPU) + 2D per-seg; then the RGBA inputs for the lift
#   STEP=lift   (pixal3d ws) lift.py, one process per GPU, then remesh_lift.py
#   STEP=train3d (disc ws) lifted two-stage + hybrid, eval, back-projections, cleanup; LANES per GPU (default 2)
#   STEP=figs   (disc ws) summary + figures (analysis/make_lifted_multi.py)
# Usage: STEP=prep bash scripts/run_full_lifted.sh      (IDS="..." to restrict; all steps resumable)
set -euo pipefail
R=data/densepose_lvis; RUNS=/workspace/disc/$R/runs_full_poly; RES=$R/results_full_poly; OUT=$R/lifted_full; PX=/workspace/pixal3d_out; G=$PX/geom_full
NGPU=${NGPU:-2}; LANES=${LANES:-2}; STEP=${STEP:?STEP=prep|train2d|lift|train3d|figs}
if [ $STEP != lift ]; then source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT; fi
cd /workspace/disc
IDS=${IDS:-$(python3 -c "
import json; d = json.load(open('$R/densepose_lvis_v1_ds2_val_v1.json')); cat = {c['id']: c['name'] for c in d['categories']}
print(' '.join(str(a['id']) for a in d['annotations'] if cat[a['category_id']] == 'bear' and a.get('dp_x')))")}
mkdir -p $RUNS $RES $OUT $G /workspace/logs/full_lifted
echo "##### $STEP: $(echo $IDS | wc -w) bears [$(date -u +%T)] #####"

case $STEP in
prep)
  for i in $IDS; do d=$RUNS/lvis$i; [ -f $d/lvis$i.png ] || python analysis/prep_lvis_instance.py --ann_id $i --class_name bear --out_dir $d --long_side 400 --mask_source polygon > /dev/null; done
  SPLIT=$(RUNS=$RUNS IDS="$IDS" python - <<'PY'
import os, torch, numpy as np
from scipy import ndimage
out = []
for i in os.environ['IDS'].split():
    m = torch.load(f"{os.environ['RUNS']}/lvis{i}/lvis{i}_mask.pth").numpy().astype(bool)
    lab, _ = ndimage.label(m, structure=np.ones((3, 3)))
    if np.bincount(lab[m]).max() / m.sum() < 0.95: out.append(i)
print(' '.join(out))
PY
)
  echo "split (pix2gestalt): $(echo $SPLIT | wc -w): $SPLIT" | tee $RES/split_ids.txt
  TODO=""; for i in $SPLIT; do [ -f $RUNS/lvis$i/lvis${i}_amodal_samples.npz ] || TODO="$TODO $i"; done
  for i in $TODO; do python analysis/prep_amodal_input.py --ann_id $i --class_name bear --out_dir $RUNS/lvis$i --mask_source polygon | tail -1; done
  if [ -n "$TODO" ]; then
    ( cd /workspace/pix2gestalt_repo/pix2gestalt && env -u PYTHONPATH -u CONDA_DEFAULT_ENV PATH=/workspace/pix2gestalt_repo/venv/bin:/usr/local/bin:/usr/bin:/bin \
        XDG_CACHE_HOME=/workspace/.cache PYTHONPATH=../stubs:taming-transformers:CLIP python ../run_amodal.py \
        --run_dirs $(for i in $TODO; do echo $RUNS/lvis$i; done) --tags $(for i in $TODO; do echo lvis$i; done) --n_samples 3 --steps 50 )
  fi
  for i in $SPLIT; do [ -f $RUNS/lvis$i/lvis${i}_amodal_mask.pth ] || python analysis/merge_amodal_mask.py --run_dir $RUNS/lvis$i --tag lvis$i | cut -c1-160; done
  for i in $IDS; do touch $RUNS/lvis$i/lvis${i}_amodal.done; done ;;

train2d)
  # 2D two-stage: the worker (prep again = same crop; amodal mask used where it exists); one worker per GPU over an interleaved share
  TODO=""; for i in $IDS; do [ -f $RES/lvis$i.json ] || TODO="$TODO $i"; done
  for g in $(seq 0 $((NGPU - 1))); do
    SH=$(echo $TODO | tr ' ' '\n' | awk -v g=$g -v n=$NGPU 'NF && (NR - 1) % n == g' | tr '\n' ' ')
    [ -n "$SH" ] && CUDA_VISIBLE_DEVICES=$g PYTHONUNBUFFERED=1 python scripts/run_lvis_worker.py --ann_ids $SH --class_name bear --results_dir $RES --runs_dir $RUNS \
        --mu_scope global_then_segment_aniso --mu_switch_step 150 --mu_lr 5e-2 --merge_below_frac 0.015 --fill_unlabelled_segments \
        --mask_source polygon --amodal_mask --amodal_wait 5 --keep_intermediates > /workspace/logs/full_lifted/worker2d_gpu$g.log 2>&1 &
  done; wait
  # 2D per-seg (same code path as the lifted arms, LIFT=none)
  one2d() { local i=$1 g=$2; CUDA_VISIBLE_DEVICES=$g CLASS=bear TAG=lvis$i SRC=$RUNS/lvis$i OUT=$OUT LIFT=none T2D=$RUNS/lvis$i/lvis${i}_mask_geo_table_2d_seed0.pth \
      MODE=perseg RUNTAG=_2dteacher bash scripts/run_lifted_instance.sh > /workspace/logs/full_lifted/perseg2d_$i.log 2>&1 || echo "lvis$i 2D per-seg FAILED"; }
  export -f one2d; export RUNS OUT
  k=0; for i in $IDS; do echo "$i $((k % NGPU))"; k=$((k + 1)); done | xargs -P $((NGPU * LANES)) -L 1 bash -c 'one2d $0 $1'
  # RGBA inputs for the lift: completed content where the mask is split, else crop + polygon
  for i in $IDS; do
    d=$RUNS/lvis$i; o=$PX/bear_lvis${i}_full_rgba.png; [ -f $o ] && continue
    if [ -f $d/lvis${i}_amodal_samples.npz ]; then python analysis/make_amodal_rgba.py --run_dir $d --tag lvis$i --sample auto --out_png $o | cut -c1-160
    else python - $d/lvis$i.png $d/lvis${i}_mask.pth $o <<'EOF'
import sys, numpy as np, torch
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('RGB')); m = torch.load(sys.argv[2]).numpy().astype(bool)
Image.fromarray(np.dstack([im, (m * 255).astype(np.uint8)])).save(sys.argv[3])
EOF
    fi
  done ;;

lift)
  cd /workspace/pixal3d_repo && source /workspace/envs/pixal3d/bin/activate
  TODO=(); for i in $IDS; do [ -f $G/bear_lvis${i}_full_lift.pth ] || TODO+=($i); done
  for g in $(seq 0 $((NGPU - 1))); do
    IM=(); TG=(); for k in "${!TODO[@]}"; do [ $((k % NGPU)) -eq $g ] || continue; IM+=($PX/bear_lvis${TODO[$k]}_full_rgba.png); TG+=(bear_lvis${TODO[$k]}_full); done
    [ ${#IM[@]} -gt 0 ] && CUDA_VISIBLE_DEVICES=$g HF_HUB_OFFLINE=1 HF_HOME=/workspace/.cache/huggingface python /workspace/disc/external/pixal3d/lift.py \
        --images "${IM[@]}" --tags "${TG[@]}" --out_dir $G/raw --low_vram > /workspace/logs/full_lifted/lift_gpu$g.log 2>&1 &
  done; wait
  RAW=(); for i in $IDS; do [ -f $G/raw/bear_lvis${i}_full_lift.pth ] && [ ! -f $G/bear_lvis${i}_full_lift.pth ] && RAW+=($G/raw/bear_lvis${i}_full_lift.pth); done
  [ ${#RAW[@]} -gt 0 ] && python /workspace/disc/external/pixal3d/remesh_lift.py --lifts "${RAW[@]}" --out_dir $G | grep -E "REMESH|Error" ;;

train3d)
  one3d() {
    local i=$1 g=$2 d=$RUNS/lvis$1 L=$OUT/lvis$1
    local LF=$G/bear_lvis${i}_full_lift.pth T2=$d/lvis${i}_mask_geo_table_2d_seed0.pth
    [ -f $L/multi_eval.json ] && { echo "lvis$i already done"; return 0; }
    [ -f $LF ] && [ -f $T2 ] || { echo "lvis$i: no lift or no 2D table, skipped"; return 0; }
    run() { CUDA_VISIBLE_DEVICES=$g CLASS=bear TAG=lvis$i SRC=$d OUT=$OUT LIFT=$LF T2D=$T2 RUNTAG=_full "$@" bash scripts/run_lifted_instance.sh; }
    run env MODE=twostage >> /workspace/logs/full_lifted/lifted_$i.log 2>&1 || echo "lvis$i lifted two-stage FAILED"
    run env MODE=hybrid >> /workspace/logs/full_lifted/lifted_$i.log 2>&1 || echo "lvis$i lifted hybrid FAILED"
    local P=$L/encoder_loraW_all_r4_phase2_lifted S2=$d/encoder_loraW_all_r4_phase2
    declare -A PF=([zs]=$P1/pred_f.pth [2d_stage1]=$S2/alpha_stageA_end/alpha0.5/pred_f.pth [2d_stage2]=$S2/alpha/alpha0.5/pred_f.pth
                   [2d_perseg]=${P}_perseg_2dteacher/alpha/alpha0.5/pred_f.pth [lifted_stage1]=${P}_full/alpha_stageA_end/alpha0.5/pred_f.pth
                   [lifted_stage2]=${P}_full/alpha/alpha0.5/pred_f.pth [lifted_hybrid]=${P}_hybrid_full/alpha/alpha0.5/pred_f.pth)
    local ARMS=() k; for k in "${!PF[@]}"; do [ -f ${PF[$k]} ] && ARMS+=(--arm $k=${PF[$k]}); done
    CUDA_VISIBLE_DEVICES=$g python analysis/eval_lvis_ours.py --run_dir $d --tag lvis$i --obj_path $OBJ --name shic_bear --geodesics_path $GEO228 \
        --out_json $L/multi_eval.json.tmp "${ARMS[@]}" > $L/multi_eval.log 2>&1 && mv $L/multi_eval.json.tmp $L/multi_eval.json || { echo "lvis$i eval FAILED"; return 0; }
    local B=$L/backproj; mkdir -p $B; export CUDA_VISIBLE_DEVICES=$g
    [ -f $B/lvis${i}_position_color.png ] || python analysis/pixel_coloring.py --img_path $d/lvis$i.png --mask_path $d/lvis${i}_mask.pth \
        --mode position --save_dir $B --output_path $B/lvis${i}_position_color.png > $B/log.txt 2>&1
    for k in "${!PF[@]}"; do
      [ -f ${PF[$k]} ] && [ ! -f $B/lvis${i}_${k}_backproj.png ] || continue
      mkdir -p $B/soft_$k
      python analysis/run_in_one_process.py \
        analysis/color_mesh_from_soft_mapping.py --mask_path $d/lvis${i}_mask.pth --img_path $d/lvis$i.png --save_dir $B/soft_$k \
          --features_path $d/lvis${i}_pix_sdsquare_fuse16.pth --vertex_features_path ${PF[$k]} --obj_path $OBJ --name shic_bear \
          --color_mode position --color_path $B/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
        analysis/color_image_from_knn.py --mask_path $d/lvis${i}_mask.pth --knn_dir $B/soft_$k \
          --knn_path $B/soft_$k/lvis${i}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
          --source_image_path $d/lvis$i.png --k 1 --save_dir $B --output_path $B/lvis${i}_${k}_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
        || echo "lvis$i backproj $k FAILED"
      rm -rf $B/soft_$k
    done
    if [ ! -f $B/lvis${i}_SHIC_backproj.png ]; then
      mkdir -p $B/shic
      python analysis/run_in_one_process.py \
        analysis/shic_infer_correspondence.py --class_name bear --image_path $d/lvis$i.png --mask_path $d/lvis${i}_mask.pth --save_dir $B/shic --top_k 10 --- \
        analysis/color_image_from_knn.py --mask_path $d/lvis${i}_mask.pth --knn_dir $B/shic --knn_path $B/shic/lvis${i}_shic_pixel_to_vertex_nn.pth \
          --vertex_colors_path $CHK --source_image_path $d/lvis$i.png --k 1 --save_dir $B/shic --output_path $B/lvis${i}_SHIC_backproj.png --no_side_by_side \
        >> $B/log.txt 2>&1 || echo "lvis$i SHIC FAILED"
      rm -rf $B/shic
    fi
    # CLEANUP (Tal 10-28): keep every pred_f, eval, back-projections, the lift; drop checkpoints, tables, features
    find $d $L -name 'encoder_checkpoint*.pth' -delete; rm -f $d/lvis${i}_pix_sdsquare_fuse16.pth $T2 $L/lvis${i}_mask_geo_table_lifted_seed0*.pth
    echo "lvis$i DONE [$(date -u +%T)]"
  }
  export -f one3d; export RUNS OUT G
  export OBJ=./demo/shic/shapes/bear.obj P1=./experiments/shic_bear/encoder_dfd_crossview_phase1 GEO228=$R/eval_shic_bear/bear_heat_geodesics_228.npy \
         CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
  k=0; for i in $IDS; do echo "$i $((k % NGPU))"; k=$((k + 1)); done | xargs -P $((NGPU * LANES)) -L 1 bash -c 'one3d $0 $1' ;;

figs)
  python analysis/make_lifted_multi.py --ids $IDS --crowd $IDS --crowd_name "all bears, GT polygon mask (*)" --out_dir $OUT/summary --lifted_dir $OUT \
      --src_sub $RUNS --src_crowd $RUNS \
      --arms SHIC zs 2d_stage1 2d_stage2 2d_perseg lifted_stage1 lifted_stage2 lifted_hybrid \
      --panels "SHIC=SHIC" "zs=ZS" "2d_stage2=2D two-stage" "2d_perseg=2D per-seg" "lifted_stage1=lifted stage 1" \
               "lifted_stage2=lifted two-stage" "lifted_hybrid=lifted hybrid" ;;
esac
echo "FULL LIFTED $STEP DONE [$(date -u +%T)]"
