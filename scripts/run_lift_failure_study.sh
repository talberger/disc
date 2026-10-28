#!/bin/bash
# Why the lifted teacher did not help on 171627 / 117682 (Tal, 2026-10-28). CPU only, on the existing 10-26 runs (no training).
# Per bear -> data/densepose_lvis/lifted/<tag>/study/: study.png (analysis/study_lift_failure.py), paths.png (GT pt 1 -> pts 2, 3, 2D vs
# lifted, analysis/plot_lifted_geodesic_paths.py), ellipses_{2d,lifted}.png (analysis/plot_mu_ellipses.py), + the table builder's rows check.
# Usage: bash scripts/run_lift_failure_study.sh     (IDS="..." to change)
set -euo pipefail
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
IDS=${IDS:-"171627 117682"}; R=data/densepose_lvis
for id in $IDS; do
  tag=lvis$id; src=$R/runs_runai_sub20/$tag; L=$R/lifted/$tag; O=$L/study; mkdir -p $O
  LIFT=/workspace/pixal3d_out/geom/bear_${tag}_lift.pth; TL=$L/${tag}_mask_geo_table_lifted_seed0.pth
  python analysis/study_lift_failure.py --src $src --tag $tag --lift_path $LIFT --lifted_table $TL --eval_json $L/multi_eval.json \
      --out_png $O/study.png > $O/study.txt 2>&1 || echo "  $tag study FAILED ($O/study.txt)"
  P=$(python -c "import torch; g = torch.load('$src/${tag}_gt.pth'); print(' '.join(f'{r} {c}' for r, c in zip(g['rows'].tolist(), g['cols'].tolist())))")
  set -- $P
  python analysis/plot_lifted_geodesic_paths.py --lift_path $LIFT --mask_path $src/${tag}_mask.pth --img_path $src/$tag.png \
      --lifted_meta ${TL%.pth}_meta.json --centre $1 $2 --neighbours ${@:3} --out $O/paths.png > $O/paths.txt 2>&1 || echo "  $tag paths FAILED"
  for k in 2d lifted; do
    if [ $k = 2d ]; then RD=$src/encoder_loraW_all_r4_phase2; else RD=$L/encoder_loraW_all_r4_phase2_lifted; fi
    python analysis/plot_mu_ellipses.py --run_dir $RD --fine_seg_path $src/${tag}_fine_segments.pth --img_path $src/$tag.png \
        --output_path $O/ellipses_$k.png > $O/ellipses_$k.txt 2>&1 || echo "  $tag ellipses $k FAILED"
  done
  cp $L/${tag}_lifted_vs_2d_rows.png $O/ 2>/dev/null || true
  echo "  $tag done: $(ls $O | tr '\n' ' ')"
done
echo "LIFT FAILURE STUDY DONE [$(date -u +%T)]"
