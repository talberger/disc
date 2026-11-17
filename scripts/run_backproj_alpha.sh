#!/bin/bash
# Back-projection of the full alpha run (run_stage1_raycast.sh OUT=stage1_full) at another read-time alpha (Tal, 2026-11-17: alpha 1,
# every bear / horse / elephant, next to SHIC): pred_f rebuilt from the kept LoRA delta (<arm>/alpha/lora_state.pth, no retraining),
# the pixel features re-extracted (the run deleted them), then the backproj() of run_stage1_raycast.sh ->
# $O/backproj/lvis<i>_<arm>_a<alpha>_backproj.png. The pred_f and the features are deleted again (PVC space). Resumable; workers share
# the instance list through $O/.bplock, so start several (one exec each) on the workspaces that see the PVC.
# Usage (test: MAX=1): ALPHA=1 bash scripts/run_backproj_alpha.sh > /workspace/logs/bpalpha_<ws>_<n>.log 2>&1
set -uo pipefail   # no -e: one bad instance must not stop the pass
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; G=/workspace/pixal3d_out/geom_full; ALPHA=${ALPHA:-1}; OUT=${OUT:-stage1_full}; ARM=${ARM:-lifted_amodal}; MAX=${MAX:-0}; n=0   # MAX=1: one instance (a test)
for CLASS in bear horse elephant; do
  case $CLASS in bear) RUNS=$R/runs_full_poly; LROOT=$R/lifted_full;; *) RUNS=$R/runs_${CLASS}_poly; LROOT=$R/lifted_$CLASS;; esac
  OBJ=./demo/shic/shapes/$CLASS.obj; NAME=shic_$CLASS; P1=./experiments/shic_$CLASS/encoder_dfd_crossview_phase1
  CHK=demo/shic/colored_mesh/${CLASS}_mesh_checker16_uv_color.pth
  [ $CLASS = bear ] && CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
  for i in $(ls $G | sed -n "s/^${CLASS}_lvis\([0-9]*\)_amodal_lift.pth$/\1/p"); do
    d=$RUNS/lvis$i; O=$LROOT/lvis$i/$OUT; B=$O/backproj; tag=lvis$i; A=$O/$ARM/alpha; F=$d/${tag}_pix_sdsquare_fuse16.pth
    PNG=$B/lvis${i}_${ARM}_a${ALPHA}_backproj.png
    [ -f $PNG ] && continue
    [ -f $O/eval_all.json ] && [ ! -d $O/.lock ] || { echo "lvis$i: no finished run, skipped"; continue; }
    mkdir $O/.bplock 2>/dev/null || continue
    echo "##### $CLASS $tag #####"
    PF=$A/alpha$ALPHA/pred_f.pth
    [ -f $PF ] || python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
        --lora_checkpoint $A/lora_state.pth --alphas $ALPHA --out_dir $A > /dev/null || { echo "lvis$i export FAILED"; rmdir $O/.bplock; continue; }
    [ -f $F ] || python analysis/extract_dino_sd_features.py --img_path $d/$tag.png --save_dir $d --output_path $F --sd_frame square_pad \
        --cpu_postprocess > $O/features_bp.log 2>&1
    mkdir -p $B/soft_bp
    python analysis/run_in_one_process.py \
      analysis/color_mesh_from_soft_mapping.py --mask_path $d/${tag}_mask.pth --img_path $d/$tag.png --save_dir $B/soft_bp \
        --features_path $F --vertex_features_path $PF --obj_path $OBJ --name $NAME \
        --color_mode position --color_path $B/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
      analysis/color_image_from_knn.py --mask_path $d/${tag}_mask.pth --knn_dir $B/soft_bp \
        --knn_path $B/soft_bp/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
        --source_image_path $d/$tag.png --k 1 --save_dir $B --output_path $PNG --no_side_by_side >> $B/log.txt 2>&1 \
      || echo "lvis$i backproj FAILED"
    rm -rf $B/soft_bp; rm -f $F; [ -f $A/lora_state.pth ] && rm -f $PF; rmdir $O/.bplock   # no delta (the first ~11): keep pred_f
    [ -f $PNG ] && echo "BP DONE $CLASS $i"; n=$((n + 1)); [ $MAX -gt 0 ] && [ $n -ge $MAX ] && break 2
  done
done
echo "BPALPHA DONE"
