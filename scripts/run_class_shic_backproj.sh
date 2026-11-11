#!/bin/bash
# SHIC's back-projection of every instance of a class short run (scripts/run_class_short.sh), to sit next to ours (Tal, 2026-11-11):
# $LROOT/lvis<i>/stage1_tri/backproj/lvis<i>_SHIC_backproj.png. The commands of run_full_lifted.sh; needs only the instance's inputs and
# demo/shic/weights/<class>{,_cse,_lbo}.pth. SHIC's scores are already in data/densepose_lvis/eval_shic_<class>/results.json ('bbox' = the
# bears' SHIC column). NGPU GPUs x LANES workers (worker w takes every N-th instance), resumable: an instance with the picture is skipped.
# Usage: CLASS=horse NGPU=3 LANES=2 bash scripts/run_class_shic_backproj.sh        (a few: IDS="772 843")
set -uo pipefail   # no -e: one bad instance must not stop the pass
source "${DISC_ROOT:-/workspace/disc}/env/activate.sh"; cd $DISC_ROOT
CLASS=${CLASS:?CLASS=horse|elephant}; R=data/densepose_lvis; RUNS=$R/runs_${CLASS}_poly; LROOT=$R/lifted_$CLASS
IDS=${IDS:-$(cat /workspace/logs/short_$CLASS/ids.txt)}; NGPU=${NGPU:-1}; LANES=${LANES:-2}; N=$((NGPU * LANES))
CHK=demo/shic/colored_mesh/${CLASS}_mesh_checker16_uv_color.pth
echo "##### $CLASS SHIC back-projection: $(echo $IDS | wc -w) instances, $N workers [$(date -u +%FT%T)] #####"
worker() {
  local w=$1 k=0 i d B; export CUDA_VISIBLE_DEVICES=$((w % NGPU))
  for i in $IDS; do k=$((k + 1)); [ $((k % N)) -eq $w ] || continue
    d=$RUNS/lvis$i; B=$LROOT/lvis$i/stage1_tri/backproj
    [ -f $B/lvis${i}_SHIC_backproj.png ] || [ ! -f $d/lvis${i}_mask.pth ] && continue
    mkdir -p $B/shic
    python analysis/run_in_one_process.py \
      analysis/shic_infer_correspondence.py --class_name $CLASS --image_path $d/lvis$i.png --mask_path $d/lvis${i}_mask.pth --save_dir $B/shic --top_k 10 --- \
      analysis/color_image_from_knn.py --mask_path $d/lvis${i}_mask.pth --knn_dir $B/shic --knn_path $B/shic/lvis${i}_shic_pixel_to_vertex_nn.pth \
        --vertex_colors_path $CHK --source_image_path $d/lvis$i.png --k 1 --save_dir $B/shic --output_path $B/lvis${i}_SHIC_backproj.png --no_side_by_side \
      >> $B/log.txt 2>&1 || echo "lvis$i SHIC FAILED"
    rm -rf $B/shic
  done
}
for w in $(seq 0 $((N - 1))); do worker $w & done; wait
echo "SHIC BACKPROJ DONE: $(ls $LROOT/lvis*/stage1_tri/backproj/lvis*_SHIC_backproj.png 2>/dev/null | wc -l) pictures [$(date -u +%T)]"
