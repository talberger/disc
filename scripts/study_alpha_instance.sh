#!/bin/bash
# One instance of the full alpha run, studied over read-time alpha (Tal, 2026-11-18: elephant 28733, alpha 0.5 50.9 -> alpha 1 93.0):
# pred_f at each alpha from the kept LoRA delta (no retraining), eval per GT point (+ pred vertex), back-projection per alpha with the
# per-pixel correspondences kept, SHIC's per-point prediction. -> $O/study_alpha/ (eval.json, shic.json, bp_a<alpha>.png, soft_a<alpha>/).
# Usage: I=28733 CLASS=elephant [ALPHAS="0.25 0.5 0.75 1 1.25 1.5"] bash scripts/study_alpha_instance.sh > /workspace/logs/study_<I>.log 2>&1
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; CLASS=${CLASS:?}; i=${I:?}; ALPHAS=${ALPHAS:-0.25 0.5 0.75 1 1.25 1.5}; OUT=${OUT:-stage1_full}; ARM=${ARM:-lifted_amodal}
case $CLASS in bear) RUNS=$R/runs_full_poly; LROOT=$R/lifted_full;; *) RUNS=$R/runs_${CLASS}_poly; LROOT=$R/lifted_$CLASS;; esac
OBJ=./demo/shic/shapes/$CLASS.obj; NAME=shic_$CLASS; P1=./experiments/shic_$CLASS/encoder_dfd_crossview_phase1; GEO228=$R/eval_shic_$CLASS/${CLASS}_heat_geodesics_228.npy
CHK=demo/shic/colored_mesh/${CLASS}_mesh_checker16_uv_color.pth; [ $CLASS = bear ] && CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
d=$RUNS/lvis$i; tag=lvis$i; O=$LROOT/lvis$i/$OUT; A=$O/$ARM/alpha; S=$O/study_alpha; F=$d/${tag}_pix_sdsquare_fuse16.pth; mkdir -p $S
[ -f $F ] || python analysis/extract_dino_sd_features.py --img_path $d/$tag.png --save_dir $d --output_path $F --sd_frame square_pad --cpu_postprocess > $S/features.log 2>&1
python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
    --lora_checkpoint $A/lora_state.pth --alphas $ALPHAS --out_dir $S/alpha > /dev/null
EV=(--arm zs=$P1/pred_f.pth); for x in $ALPHAS; do EV+=(--arm a$x=$S/alpha/alpha$x/pred_f.pth); done
python analysis/eval_lvis_ours.py --run_dir $d --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $S/eval.json "${EV[@]}" > $S/eval.log 2>&1
python analysis/shic_one.py $i $CLASS > $S/shic.json 2> $S/shic.log || echo "SHIC FAILED"
for x in zs $ALPHAS; do
  PF=$S/alpha/alpha$x/pred_f.pth; [ $x = zs ] && PF=$P1/pred_f.pth; K=$S/soft_a$x; mkdir -p $K
  python analysis/run_in_one_process.py \
    analysis/color_mesh_from_soft_mapping.py --mask_path $d/${tag}_mask.pth --img_path $d/$tag.png --save_dir $K \
      --features_path $F --vertex_features_path $PF --obj_path $OBJ --name $NAME \
      --color_mode position --color_path $O/backproj/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
    analysis/color_image_from_knn.py --mask_path $d/${tag}_mask.pth --knn_dir $K \
      --knn_path $K/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
      --source_image_path $d/$tag.png --k 1 --save_dir $S --output_path $S/bp_a$x.png --no_side_by_side >> $S/bp.log 2>&1 || echo "bp $x FAILED"
  find $K -type f ! -name '*correspondence.pth' -delete
done
rm -f $F $S/alpha/alpha*/pred_f.pth
python -c "
import json; r = json.load(open('$S/eval.json'))['arms']
for a, v in r.items(): print(a, round(v['soft_snap']['all']['mean'], 1), [round(e) for e in v['soft_snap']['per_point']])"
echo "STUDY DONE"
