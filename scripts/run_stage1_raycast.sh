#!/bin/bash
# Stage 1 with the RAY-CAST pixel -> mesh mapping (Tal, 2026-11-08): lift.py's vertex splat maps some front pixels to the bear's back
# (171627 rep 3 -> x3, analysis/lifted_pixel_vertex_check.py); build_lifted_geodesic_table.py now ray casts instead.
# Per bear and per arm of ARMS (name=lift suffix, default "lifted_ray=full"): the lifted table from $G/bear_lvis<i>_<suffix>_lift.pth,
# one stage-1 run (149 steps, learned global ellipse = the full run's stage A, train seed 0), its back-projection
# (lifted_full/lvis<i>/backproj/lvis<i>_<arm>_backproj.png); then ONE eval of every arm with zs / 2d_stage1 / lifted_stage1 (splat) of
# the full run -> lifted_full/lvis<i>/stage1_ray/eval_all.json.
# 2026-11-09 (amodal, all bears): ARMS="lifted_ray=full lifted_amodal=amodal". A lift that is a SYMLINK to an earlier arm's lift (bears whose
# full-run lift already came from the amodal content) is not trained again: the arm points at that arm's run.
# Features and the 2D table were deleted by the full-run cleanup: rebuilt once per bear (same commands, seed 0) and deleted again after.
# Resumable: a bear with eval_all.json and every arm's back-projection is skipped. Several workers may run at once (2026-11-09): a bear is
# locked by its worker (stage1_ray/.lock, taken over when older than 60 min = a worker that died with the workspace).
# 2026-11-11 (double shell, 151955): PIXMAP=triangle = build_lifted_geodesic_table.py --pix_map triangle (a vertex of the decimated triangle
# the ray hits, never the inner skin); give it its own OUT (e.g. OUT=stage1_tri: runs, tables, eval_all.json and backproj/ all under it).
# Usage: IDS="171627 186446 32412 109595" [ARMS="lifted_ray=full lifted_amodal=amodal"] [PIXMAP=triangle OUT=stage1_tri] bash scripts/run_stage1_raycast.sh
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
R=data/densepose_lvis; G=/workspace/pixal3d_out/geom_full; ARMS=${ARMS:-lifted_ray=full}
PIXMAP=${PIXMAP:-nearest}; OUT=${OUT:-stage1_ray}
OBJ=./demo/shic/shapes/bear.obj; NAME=shic_bear; P1=./experiments/shic_bear/encoder_dfd_crossview_phase1
GEO3D=./experiments/shic_bear/geodesic_tables/shic_bear_geo_table_3d.pth; GEO228=$R/eval_shic_bear/bear_heat_geodesics_228.npy
CHK=demo/shic/colored_mesh/bear_shic_normalized_mesh_checker16_uv_color.pth
t() { local s=$(date +%s); "$@"; echo "[time] $(( $(date +%s) - s )) s : $1 $2"; }
for i in ${IDS:?}; do
  d=$R/runs_full_poly/lvis$i; L=$R/lifted_full/lvis$i; O=$L/$OUT; B=$L/backproj; [ $OUT = stage1_ray ] || B=$O/backproj; mkdir -p $O $B; tag=lvis$i
  T2=$d/${tag}_mask_geo_table_2d_seed0.pth; F=$d/${tag}_pix_sdsquare_fuse16.pth
  # split-mask bears: the full run's amodal mask is the geodesic domain of the 2D table AND of the training (as run_lvis_worker.py /
  # run_lifted_instance.sh); without it the training stops at "segment 1 has no out-of-segment pixel" (7107, 206034; 2026-11-09)
  AMODAL=(); [ -f $d/${tag}_amodal_mask.pth ] && AMODAL=(--geodesic_domain_mask_path $d/${tag}_amodal_mask.pth)
  done_all=1; for a in $ARMS; do [ -f $B/lvis${i}_${a%%=*}_backproj.png ] || done_all=0; done
  [ $done_all = 1 ] && [ -f $O/eval_all.json ] && { echo "lvis$i: done, skipped"; continue; }
  if ! mkdir $O/.lock 2>/dev/null; then
    [ -n "$(find $O/.lock -maxdepth 0 -mmin +60)" ] || { echo "lvis$i: locked by another worker, skipped"; continue; }
    echo "lvis$i: stale lock taken over"
  fi
  trap "rmdir $O/.lock 2>/dev/null" EXIT
  echo "##### $tag #####"
  [ -f $F ] || t python analysis/extract_dino_sd_features.py --img_path $d/$tag.png --save_dir $d --output_path $F --sd_frame square_pad --cpu_postprocess > $O/features.log 2>&1
  [ -f $O/meta_2d_fullrun.json ] || cp $d/${tag}_mask_geo_table_2d_seed0_meta.json $O/meta_2d_fullrun.json
  [ -f $T2 ] || t python analysis/build_geodesic_tables.py --obj_path $OBJ --name $NAME --skip_3d --object_mask_path $d/${tag}_mask.pth \
      --fine_seg_path $d/${tag}_fine_segments.pth ${AMODAL[@]+"${AMODAL[@]}"} --num_center_pixels 2048 --seed 0 --true_diameter --out_dir $d > $O/table2d.log 2>&1
  NSEG=$(python -c "import torch; print(int((torch.unique(torch.as_tensor(torch.load('$d/${tag}_fine_segments.pth'))) > 0).sum()))")
  if [ $NSEG -eq 1 ]; then NB=(--num_neighbors_in_segment 16 --num_neighbors_out_segment 0 --switch_nin 16 --switch_nout 0)
  else NB=(--num_neighbors_in_segment 8 --num_neighbors_out_segment 8 --switch_nin 16 --switch_nout 0); fi
  EV=(--arm zs=$P1/pred_f.pth --arm 2d_stage1=$d/encoder_loraW_all_r4_phase2/alpha_stageA_end/alpha0.5/pred_f.pth
      --arm lifted_stage1=$L/encoder_loraW_all_r4_phase2_lifted_full/alpha_stageA_end/alpha0.5/pred_f.pth)
  declare -A RUN_OF=()                                                  # lift file -> the arm that trained on it
  for a in $ARMS; do
    ARM=${a%%=*}; LIFT=$G/bear_${tag}_${a#*=}_lift.pth; P2=$O/$ARM
    [ -e $LIFT ] || { echo "lvis$i $ARM: no lift $LIFT, skipped"; continue; }
    real=$(realpath $LIFT)
    if [ -n "${RUN_OF[$real]:-}" ]; then                                # same lift as an earlier arm: reuse its run
      EV+=(--arm $ARM=$O/${RUN_OF[$real]}/alpha/alpha0.5/pred_f.pth)
      [ -f $B/lvis${i}_${ARM}_backproj.png ] || cp $B/lvis${i}_${RUN_OF[$real]}_backproj.png $B/lvis${i}_${ARM}_backproj.png
      echo "lvis$i $ARM: same lift as ${RUN_OF[$real]}, reused"; continue
    fi
    RUN_OF[$real]=$ARM
    TL=$O/${tag}_mask_geo_table_${ARM}_seed0.pth
    if [ ! -f $P2/alpha/alpha0.5/pred_f.pth ]; then
      [ -f ${TL%.pth}_meta.json ] && [ -f $TL ] || t python analysis/build_lifted_geodesic_table.py --lift_path $LIFT --table_2d $T2 --out_path $TL --pix_map $PIXMAP > $O/tablelifted_$ARM.log 2>&1
      DL=$(python -c "import json; print(json.load(open('${TL%.pth}_meta.json'))['true_diameter_2d'])")
      [ -f $P2/encoder_checkpoint.pth ] || t env PYTHONUNBUFFERED=1 python phase2/train_relational_loss_l2norm.py --obj_path $OBJ --name $NAME --init_encoder_dir $P1 \
          --object_mask_path $d/${tag}_mask.pth --fine_seg_path $d/${tag}_fine_segments.pth --pix_dino_features_path $F \
          --width 2304 --n_classes 2304 --geodesic --temperature 0.01 --train_seed 0 --geo_diag_2d $DL \
          --geo_table_3d_path $GEO3D --geo_table_2d_path $TL \
          --mu_mode learned --mu_scope global_then_segment_aniso --mu_lr 5e-2 --mu_fit_space abs "${NB[@]}" --mu_switch_step 150 --num_iters 149 \
          --cyc_weight 1.676e-05 --cyc_v2 --cyc_temperature 0.05 --cyc_return_all_pixels --cyc_return_stride 3 \
          --lora_w_rank 4 --lora_w_layers all --lora_w_lr 1e-3 ${AMODAL[@]+"${AMODAL[@]}"} --no_step_checkpoints --out_dir $P2 > $P2.train.log 2>&1
      python analysis/export_pred_f_lora_alpha.py --obj_path $OBJ --name $NAME --phase1_checkpoint $P1/encoder_checkpoint.pth \
          --lora_checkpoint $P2/encoder_checkpoint.pth --alphas 0.5 --out_dir $P2/alpha > /dev/null
      rm -f $P2/encoder_checkpoint*.pth $TL
    fi
    EV+=(--arm $ARM=$P2/alpha/alpha0.5/pred_f.pth)
    if [ ! -f $B/lvis${i}_${ARM}_backproj.png ]; then
      mkdir -p $B/soft_$ARM
      python analysis/run_in_one_process.py \
        analysis/color_mesh_from_soft_mapping.py --mask_path $d/${tag}_mask.pth --img_path $d/$tag.png --save_dir $B/soft_$ARM \
          --features_path $F --vertex_features_path $P2/alpha/alpha0.5/pred_f.pth --obj_path $OBJ --name shic_bear \
          --color_mode position --color_path $B/lvis${i}_position_color.png --k_vertices_per_pixel 10 --temperature 0.01 --- \
        analysis/color_image_from_knn.py --mask_path $d/${tag}_mask.pth --knn_dir $B/soft_$ARM \
          --knn_path $B/soft_$ARM/${tag}_mask_soft_snap_correspondence.pth --vertex_colors_path $CHK \
          --source_image_path $d/$tag.png --k 1 --save_dir $B --output_path $B/lvis${i}_${ARM}_backproj.png --no_side_by_side >> $B/log.txt 2>&1 \
        || echo "lvis$i backproj $ARM FAILED"
      rm -rf $B/soft_$ARM
    fi
  done
  unset RUN_OF
  python analysis/eval_lvis_ours.py --run_dir $d --tag $tag --obj_path $OBJ --name $NAME --geodesics_path $GEO228 --out_json $O/eval_all.json \
      "${EV[@]}" > $O/eval_all.log 2>&1
  python -c "
import json; r = json.load(open('$O/eval_all.json'))['arms']
print('STAGE1 RAY $i: ' + ' | '.join('%s %.1f' % (a, v['soft_snap']['all']['mean']) for a, v in r.items()))"
  cp $O/meta_2d_fullrun.json $d/${tag}_mask_geo_table_2d_seed0_meta.json
  rm -f $T2 $F
  rmdir $O/.lock; trap - EXIT
done
echo "ALL STAGE1 RAY DONE"
