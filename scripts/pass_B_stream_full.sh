#!/usr/bin/env bash
# Phase 2 Pass B: STREAM full-tier parallel, N runs per tier.
# P=6t cpus 0-5, E=8t cpus 6-13, LPE=2t cpus 14-15.
set -eu

cd "$(dirname "$0")/.."

RUNS=${RUNS:-20}
OUT_BASE=results/profiling/raw/stream_full

rm -rf "$OUT_BASE"
./scripts/drop_caches.sh

echo "[pass_B] starting STREAM full-tier sweep at $(date) (N=$RUNS)"

for r in $(seq 1 $RUNS); do
  OMP_NUM_THREADS=6 ./scripts/measure_one.sh P   0-5   "$OUT_BASE/r$r" ./benchmarks/STREAM/stream_omp > /dev/null
  OMP_NUM_THREADS=8 ./scripts/measure_one.sh E   6-13  "$OUT_BASE/r$r" ./benchmarks/STREAM/stream_omp > /dev/null
  OMP_NUM_THREADS=2 ./scripts/measure_one.sh LPE 14-15 "$OUT_BASE/r$r" ./benchmarks/STREAM/stream_omp > /dev/null
done

echo "[pass_B] done at $(date)"

echo ""
echo "=== STREAM full-tier summary (Triad MB/s per tier, all runs) ==="
for t in P E LPE; do
  printf "%-3s: " "$t"
  for r in $(seq 1 $RUNS); do
    d=$OUT_BASE/r$r
    [ -f "$d/$t.stdout.txt" ] && grep Triad "$d/$t.stdout.txt" | awk '{printf "%s ", $2}'
  done
  echo ""
done

echo ""
echo "=== Stats (r1 often cache-cold; flag if wall > 3x median) ==="
for t in P E LPE; do
  awk -v tier="$t" 'BEGIN{n=0;s=0;s2=0} {n++;s+=$1;s2+=$1*$1} END{mean=s/n; sd=sqrt(s2/n - mean*mean); printf "%-3s n=%d triad_mean=%.1f stdev=%.1f cv=%.3f%%\n", tier, n, mean, sd, 100*sd/mean}' \
    <(for r in $(seq 1 $RUNS); do
        d=$OUT_BASE/r$r
        [ -f "$d/$t.stdout.txt" ] && grep Triad "$d/$t.stdout.txt" | awk '{print $2}'
      done)
done
