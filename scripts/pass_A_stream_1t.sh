#!/usr/bin/env bash

set -eu

cd "$(dirname "$0")/.."

RUNS=${RUNS:-20}
OUT_BASE=results/profiling/raw/stream_1t

rm -rf "$OUT_BASE"
./scripts/drop_caches.sh

echo "[pass_A] starting STREAM 1-thread sweep at $(date) (N=$RUNS)"

for r in $(seq 1 $RUNS); do
  for spec in "P 0" "E 6" "LPE 14"; do
    set -- $spec; tier=$1; cpu=$2
    OMP_NUM_THREADS=1 ./scripts/measure_one.sh "$tier" "$cpu" "$OUT_BASE/r$r" ./benchmarks/STREAM/stream_omp > /dev/null
  done
done

echo "[pass_A] done at $(date)"

echo ""
echo "=== STREAM 1-thread summary (Triad MB/s per tier, all runs) ==="
for t in P E LPE; do
  printf "%-3s: " "$t"
  for r in $(seq 1 $RUNS); do
    d=$OUT_BASE/r$r
    [ -f "$d/$t.stdout.txt" ] && grep Triad "$d/$t.stdout.txt" | awk '{printf "%s ", $2}'
  done
  echo ""
done

echo ""
echo "=== Stats ==="
for t in P E LPE; do
  awk -v tier="$t" 'BEGIN{n=0;s=0;s2=0} {n++;s+=$1;s2+=$1*$1} END{mean=s/n; sd=sqrt(s2/n - mean*mean); printf "%-3s n=%d mean=%.1f stdev=%.1f cv=%.3f%%\n", tier, n, mean, sd, 100*sd/mean}' \
    <(for r in $(seq 1 $RUNS); do
        d=$OUT_BASE/r$r
        [ -f "$d/$t.stdout.txt" ] && grep Triad "$d/$t.stdout.txt" | awk '{print $2}'
      done)
done
