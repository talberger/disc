#!/bin/bash
# Move result folders from the Run:ai workspace to the Mac (the Mac is the base, the PVC was 94% full; Tal, 2026-11-11).
# Per top-level entry of data/densepose_lvis/<dir>: tar over `runai workspace exec` -> extracted on the Mac -> verified (md5 of the tar stream
# on both sides + every server file on the Mac with the same size) -> DELETE=1: that entry is deleted on the server, only after it verified.
# Resumable: what was deleted is no longer listed; an entry that failed 3 times is left on the server and reported (FAILED).
# Usage: [DELETE=1] [PAR=3] bash scripts/pull_from_runai.sh runs_runai_crowd lifted_occ ...
set -uo pipefail
export PATH=$HOME/.runai/bin:$PATH LC_ALL=C
WS=${WS:-tberger3-disc-gpu3}; S=/workspace/disc/data/densepose_lvis; M=$(cd "$(dirname "$0")/.." && pwd)/data/densepose_lvis
ex() { runai workspace exec $WS -p avidan -- bash -c "$1" 2>/dev/null | tr -d '\r'; }
if [ "${1:-}" = --one ]; then   # one entry: copy, verify, delete
  D=$2; u=$3; k=$(echo "$D/$u" | md5 -q | cut -c1-12); tmp=$(mktemp -d)
  for try in 1 2 3; do
    ex "cd $S/$D && tar cf - '$u' | tee >(md5sum | cut -d' ' -f1 > /tmp/pull_$k.md5) | base64 -w0" | tr -d '\n' | base64 -d | tee >(md5 -q > $tmp/md5) | tar xf - -C "$M/$D" 2>/dev/null
    sleep 2
    a=$(ex "cd $S/$D && find '$u' -type f -printf '%s %p\n' | LC_ALL=C sort; echo END \$(cat /tmp/pull_$k.md5)")
    [ "$(echo "$a" | tail -1)" = "END $(cat $tmp/md5)" ] || { echo "$D/$u: try $try, stream md5 differs"; continue; }
    a=$(echo "$a" | sed '$d'); b=$(cd "$M/$D" && find "$u" -type f -exec stat -f '%z %N' {} + | sort)
    miss=$(comm -23 <(echo "$a") <(echo "$b") | grep -c .)
    [ "$miss" = 0 ] || { echo "$D/$u: try $try, $miss files missing or of another size"; continue; }
    msg="$D/$u: OK $(echo "$a" | grep -c .) files $(echo "$a" | awk '{s += $1} END {printf "%.2f GB", s / 1e9}')"
    if [ "${DELETE:-0}" = 1 ]; then ex "rm -rf $S/$D/'$u' /tmp/pull_$k.md5; [ -e $S/$D/'$u' ] && echo STILL_THERE" | grep -q STILL_THERE && msg="$msg, NOT deleted" || msg="$msg, deleted on the server"; fi
    echo "$(date +%H:%M) $msg"; rm -rf $tmp; exit 0
  done
  echo "$(date +%H:%M) $D/$u: FAILED, left on the server"; rm -rf $tmp; exit 0
fi
for D in "$@"; do
  mkdir -p "$M/$D"; U=$(ex "ls -A $S/$D 2>/dev/null"); echo "##### $D: $(echo "$U" | grep -c .) entries #####"
  [ -n "$U" ] && echo "$U" | xargs -P ${PAR:-3} -I{} bash "$0" --one "$D" {}
  [ "${DELETE:-0}" = 1 ] && ex "rmdir $S/$D 2>/dev/null; [ -e $S/$D ] && echo '$D: not empty, kept' || echo '$D: removed'"
done
echo "PULL DONE"
