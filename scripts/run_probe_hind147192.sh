#!/bin/bash
# Horse 147192, why the two hind legs do not separate (Tal, 2026-11-17): the amodal stage-1 run of run_stage1_raycast.sh
# (ARMS="lifted_amodal=amodal" PIXMAP=triangle, seed 0) trained again WITH a checkpoint every 10 steps (each carries the global
# ellipse), then analysis/probe_pair_loss.py: rep = near hind cannon, same = lower on that leg, other = far hind cannon, and the
# two hind-leg regions -> $O/probe_hind.json. Inputs the volume lacks (fine segments, features, 2D table, lifted table) are rebuilt
# with the original commands (run_class_short.sh / run_stage1_raycast.sh); the run on Run:ai had them on its PVC.
# On a RunPod pod: bash scripts/run_probe_hind147192.sh > /workspace/logs/probe_hind147192.log 2>&1
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; d=$R/runs_horse_poly/lvis147192; O=$R/lifted_horse/lvis147192/stage1_legs; tag=lvis147192; mkdir -p $O
LIFT=/workspace/pixal3d_out/geom_full/horse_${tag}_amodal_lift.pth; TL=$O/${tag}_mask_geo_table_lifted_amodal_seed0.pth
T2=$d/${tag}_mask_geo_table_2d_seed0.pth; F=$d/${tag}_pix_sdsquare_fuse16.pth; P1=./experiments/shic_horse/encoder_dfd_crossview_phase1
OBJ=./demo/shic/shapes/horse.obj; GEO3D=./experiments/shic_horse/geodesic_tables/shic_horse_geo_table_3d.pth; P2=$O/traj
t() { local s=$(date +%s); "$@"; echo "[time] $(( $(date +%s) - s )) s : $1 $2"; }
[ -f $d/${tag}_fine_segments.pth ] || t python analysis/build_fine_segments.py --img_path $d/$tag.png --mask_path $d/${tag}_mask.pth \
    --save_dir $d --min_pixels_in_object 50 --merge_below_frac 0.015 --fill_unlabelled
[ -f $F ] || t python analysis/extract_dino_sd_features.py --img_path $d/$tag.png --save_dir $d --output_path $F --sd_frame square_pad --cpu_postprocess
AMODAL=(); [ -f $d/${tag}_amodal_mask.pth ] && AMODAL=(--geodesic_domain_mask_path $d/${tag}_amodal_mask.pth)
[ -f $T2 ] || t python analysis/build_geodesic_tables.py --obj_path $OBJ --name shic_horse --skip_3d --object_mask_path $d/${tag}_mask.pth \
    --fine_seg_path $d/${tag}_fine_segments.pth ${AMODAL[@]+"${AMODAL[@]}"} --num_center_pixels 2048 --seed 0 --true_diameter --out_dir $d
[ -f $TL ] || t python analysis/build_lifted_geodesic_table.py --lift_path $LIFT --table_2d $T2 --out_path $TL --pix_map triangle
DL=$(python -c "import json; print(json.load(open('${TL%.pth}_meta.json'))['true_diameter_2d'])"); echo "lifted diameter $DL"
NSEG=$(python -c "import torch; print(int((torch.unique(torch.as_tensor(torch.load('$d/${tag}_fine_segments.pth'))) > 0).sum()))"); echo "segments $NSEG"
if [ $NSEG -eq 1 ]; then NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0 --switch_nin 16 --switch_nout 0)
else NB=(--num_neighbors_in_segment 8 --num_neighbors_out_segment 8 --switch_nin 16 --switch_nout 0); fi
[ -f $P2/encoder_checkpoint_step149.pth ] || t env PYTHONUNBUFFERED=1 python phase2/train_relational_loss_l2norm.py --obj_path $OBJ --name shic_horse \
    --init_encoder_dir $P1 --object_mask_path $d/${tag}_mask.pth --fine_seg_path $d/${tag}_fine_segments.pth --pix_dino_features_path $F \
    --width 2304 --n_classes 2304 --geodesic --temperature 0.01 --train_seed 0 --geo_diag_2d $DL \
    --geo_table_3d_path $GEO3D --geo_table_2d_path $TL \
    --mu_mode learned --mu_scope global_then_segment_aniso --mu_lr 5e-2 --mu_fit_space abs "${NB[@]}" --mu_switch_step 150 --num_iters 149 \
    --cyc_weight 1.676e-05 --cyc_v2 --cyc_temperature 0.05 --cyc_return_all_pixels --cyc_return_stride 3 \
    --lora_w_rank 4 --lora_w_layers all --lora_w_lr 1e-3 ${AMODAL[@]+"${AMODAL[@]}"} --checkpoint_every 10 --out_dir $P2 > $P2.train.log 2>&1
grep "^step" $P2.train.log | tail -2
# the same run as the Run:ai one? its eval (amodal 48.9, zs 19.0) from the alpha-0.5 export of the last checkpoint
[ -f $P2/alpha/alpha0.5/pred_f.pth ] || python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name shic_horse \
    --phase1_checkpoint $P1/encoder_checkpoint.pth --lora_checkpoint $P2/encoder_checkpoint.pth --alphas 0.5 --out_dir $P2/alpha > /dev/null
python analysis/eval_lvis_ours.py --run_dir $d --tag $tag --obj_path $OBJ --name shic_horse --geodesics_path $R/eval_shic_horse/horse_heat_geodesics_228.npy \
    --out_json $O/eval_traj.json --arm zs=$P1/pred_f.pth --arm lifted_amodal=$P2/alpha/alpha0.5/pred_f.pth > $O/eval_traj.log 2>&1
python -c "import json; r = json.load(open('$O/eval_traj.json'))['arms']; print('EVAL ' + ' | '.join('%s %.1f' % (a, v['soft_snap']['all']['mean']) for a, v in r.items()))"
python analysis/probe_pair_loss.py --run_dir $P2 --phase1_dir $P1 --obj_path $OBJ --name shic_horse --features $F \
    --mask $d/${tag}_mask.pth --lift $LIFT --geo_table_3d $GEO3D --geo_diag_2d $DL \
    --pixel rep=200,38 --pixel same=235,30 --pixel other=205,62 --region near=185:215:31:45+215:245:22:40 --region far=185:248:54:84 \
    --out_json $O/probe_hind.json
echo "PROBE DONE"
