#!/bin/bash
# Two-stage run on ONE instance with the LIFTED geodesic table (Pixal3D direction; Tal, 2026-10-26) + eval against the 2D-teacher two-stage.
# The training is the current LVIS two-stage recipe exactly as scripts/run_lvis_worker.py runs it (= the L2-NORM trainer, which the worker patches in) (global mu steps 1-149 with 8 in + 8 out,
# then per-segment aniso 16 + 0; mu lr 5e-2; cycle v2; LoRA-W all r4; alpha 0.5) -- ONLY --geo_table_2d_path / --geo_diag_2d change.
# Inputs: SRC = the instance's kept-intermediates run dir (features, mask, segments, gt, 2D two-stage under encoder_loraW_all_r4_phase2/),
#         LIFT = <tag>_lift.pth from external/pixal3d/lift.py.
# Steps: (1) analysis/build_lifted_geodesic_table.py (copies the 2D table's centres/mask, replaces the distances) (2) phase 2 (3) alpha export
#        (4) eval: zs / 2D stage 1 / 2D final / lifted stage 1 / lifted final.
# Usage: CLASS=bear TAG=lvis212408 SRC=data/densepose_lvis/runs_runai_crowd/lvis212408 LIFT=/workspace/pixal3d_out/geom/bear_lvis212408_lift.pth \
#        bash scripts/run_lifted_instance.sh          -> data/densepose_lvis/lifted/<tag>/ (table, run, eval_lifted.json, check png)
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
CLASS=${CLASS:?}; TAG=${TAG:?}; SRC=${SRC:?}; LIFT=${LIFT:?}
OBJ=./demo/shic/shapes/$CLASS.obj; NAME=shic_$CLASS; P1=./experiments/shic_$CLASS/encoder_dfd_crossview_phase1
GEO3D=./experiments/shic_$CLASS/geodesic_tables/shic_${CLASS}_geo_table_3d.pth
GEO228=data/densepose_lvis/eval_shic_$CLASS/${CLASS}_heat_geodesics_228.npy
# MODE=twostage (default) | perseg (per-segment aniso 16 + 0 from step 1, no stage 1). FINESEG=<other segment map> (must label the same pixels,
# e.g. a fillseg map -> the same centres, the run checks it); RUNTAG=<suffix> for the run dir. (Tal, 2026-10-26: horse 56069 study.)
MODE=${MODE:-twostage}; FINESEG=${FINESEG:-$SRC/${TAG}_fine_segments.pth}; RUNTAG=${RUNTAG:-}
PS=; [ $MODE = perseg ] && PS=_perseg   # (no $(...) with a failing test in an assignment: set -e would exit)
O=${OUT:-data/densepose_lvis/lifted}/$TAG; P2=$O/encoder_loraW_all_r4_phase2_lifted$PS$RUNTAG; mkdir -p $O
# T2D=<other 2D table> (a segment map that labels other pixels -> other centres; 2026-10-26, horse 164135 + VLPart 8-seg): the lifted
# table is then built from it and named with RUNTAG. S2DIR / S2STAGE1 = the 2D two-stage run to compare with (default: under SRC).
if [ -n "${T2D:-}" ]; then TL=$O/${TAG}_mask_geo_table_lifted_seed0$RUNTAG.pth; else T2D=$SRC/${TAG}_mask_geo_table_2d_seed0.pth; TL=$O/${TAG}_mask_geo_table_lifted_seed0.pth; fi
AMODAL=(); [ -f $SRC/${TAG}_amodal_mask.pth ] && AMODAL=(--geodesic_domain_mask_path $SRC/${TAG}_amodal_mask.pth)
t() { local s=$(date +%s); "$@"; echo "[time] $(( $(date +%s) - s )) s : $1 $2"; }

[ -f $TL ] || t python analysis/build_lifted_geodesic_table.py --lift_path $LIFT --table_2d $T2D --out_path $TL \
    --gt_path $SRC/${TAG}_gt.pth --check_png $O/${TAG}_lifted_vs_2d_rows.png
DIAG=$(python -c "import json; print(json.load(open('${TL%.pth}_meta.json'))['true_diameter_2d'])")
NSEG=$(python -c "import torch; print(int((torch.unique(torch.as_tensor(torch.load('$FINESEG'))) > 0).sum()))")
if [ $NSEG -eq 1 ]; then   # one segment: stage 1 only, all 16 neighbours inside it (as run_lvis_worker.py does)
  NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0 --mu_switch_step 150 --switch_nin 16 --switch_nout 0 --num_iters 149)
elif [ $MODE = perseg ]; then
  NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0)
else
  NB=(--num_neighbors_in_segment 8 --num_neighbors_out_segment 8 --mu_switch_step 150 --switch_nin 16 --switch_nout 0)
fi
if [ $MODE = perseg ]; then SCOPE=segment_aniso; STAGEA=; else SCOPE=global_then_segment_aniso; STAGEA=--save_stageA_end; fi
echo "##### $TAG: $NSEG segments, lifted diameter $DIAG #####"
[ -f $P2/encoder_checkpoint.pth ] || t env PYTHONUNBUFFERED=1 python phase2/train_relational_loss_l2norm.py --obj_path $OBJ --name $NAME --init_encoder_dir $P1 \
    --object_mask_path $SRC/${TAG}_mask.pth --fine_seg_path $FINESEG \
    --pix_dino_features_path $SRC/${TAG}_pix_sdsquare_fuse16.pth \
    --width 2304 --n_classes 2304 --geodesic --temperature 0.01 --train_seed 0 --geo_diag_2d $DIAG \
    --geo_table_3d_path $GEO3D --geo_table_2d_path $TL \
    --mu_mode learned --mu_scope $SCOPE --mu_lr 5e-2 --mu_fit_space abs "${NB[@]}" \
    --cyc_weight 1.676e-05 --cyc_v2 --cyc_temperature 0.05 --cyc_return_all_pixels --cyc_return_stride 3 \
    --lora_w_rank 4 --lora_w_layers all --lora_w_lr 1e-3 ${AMODAL[@]+"${AMODAL[@]}"} --no_step_checkpoints $STAGEA --out_dir $P2 \
    > $P2.train.log 2>&1
[ $NSEG -eq 1 ] && [ ! -f $P2/encoder_checkpoint_stageA_end.pth ] && cp $P2/encoder_checkpoint.pth $P2/encoder_checkpoint_stageA_end.pth
CKS=encoder_checkpoint; [ -f $P2/encoder_checkpoint_stageA_end.pth ] && CKS="$CKS encoder_checkpoint_stageA_end"
for ck in $CKS; do
  if [ $ck = encoder_checkpoint ]; then d=$P2/alpha; else d=$P2/alpha_stageA_end; fi
  [ -f $d/alpha0.5/pred_f.pth ] || python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
      --lora_checkpoint $P2/$ck.pth --alphas 0.5 --out_dir $d > /dev/null
done
S2=${S2DIR:-$SRC/encoder_loraW_all_r4_phase2}
ARMS=(--arm zs=$P1/pred_f.pth --arm lifted_final=$P2/alpha/alpha0.5/pred_f.pth)
[ -f $S2/alpha/alpha0.5/pred_f.pth ] && ARMS+=(--arm 2d_final=$S2/alpha/alpha0.5/pred_f.pth)
[ -f $P2/alpha_stageA_end/alpha0.5/pred_f.pth ] && ARMS+=(--arm lifted_stage1=$P2/alpha_stageA_end/alpha0.5/pred_f.pth)
S2S1=${S2STAGE1:-$S2/alpha_stageA_end/alpha0.5/pred_f.pth}
[ -f $S2S1 ] && ARMS+=(--arm 2d_stage1=$S2S1)
python analysis/eval_lvis_ours.py --run_dir $SRC --tag $TAG --obj_path $OBJ --name $NAME --geodesics_path $GEO228 \
    --out_json $P2.eval.json "${ARMS[@]}" > $P2.eval.log 2>&1
[ $MODE = twostage ] && [ -z "$RUNTAG" ] && cp $P2.eval.json $O/eval_lifted.json
python - $P2.eval.json data/densepose_lvis/eval_shic_$CLASS/results.json ${TAG#lvis} $(basename $P2) <<'EOF'
import json, sys
r = json.load(open(sys.argv[1]))['arms']
try: shic = json.load(open(sys.argv[2]))['bbox']['per_instance'].get(sys.argv[3])
except Exception: shic = None
print('LIFTED EVAL %s %s: ' % (sys.argv[3], sys.argv[4]) + ' | '.join('%s %.1f' % (a, v['soft_snap']['all']['mean']) for a, v in r.items())
      + (' | SHIC %.1f' % shic if shic is not None else ''))
EOF
