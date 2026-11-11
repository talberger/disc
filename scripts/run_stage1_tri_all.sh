#!/bin/bash
# Full run of the AMODAL arm with the double-shell fix (Tal, 2026-11-11): run_stage1_raycast.sh PIXMAP=triangle OUT=stage1_tri on the 132
# bears of lifted_full/summary/summary.txt (9 test bears: amodal 59.4 -> 56.0, 151955 38.6 -> 16.9). Resumable; bears are locked per worker.
# WORKER=1 from the start of the list, 2 from the end, 3 from the middle.
# Usage: WORKER=1 bash scripts/run_stage1_tri_all.sh
set -euo pipefail
cd "${DISC_ROOT:-/workspace/disc}"
IDS=$(awk '$1 ~ /^[0-9]+$/ {print $1}' data/densepose_lvis/lifted_full/summary/summary.txt); n=$(echo $IDS | wc -w)
case ${WORKER:-1} in
  2) IDS=$(echo $IDS | tr ' ' '\n' | tac) ;;
  3) IDS=$(echo $IDS | tr ' ' '\n' | awk -v h=$((n / 2)) 'NR > h {print} NR <= h {a[NR] = $0} END {for (k = 1; k <= h; k++) print a[k]}') ;;
esac
echo "$n bears, worker ${WORKER:-1}"
IDS="$(echo $IDS)" ARMS="lifted_amodal=amodal" PIXMAP=triangle OUT=stage1_tri bash scripts/run_stage1_raycast.sh
