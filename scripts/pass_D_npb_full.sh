#!/usr/bin/env bash
# Phase 2 Pass D: NPB full-tier parallel, 4 kernels × 3 tiers × N runs.
# P=6 threads cpus 0-5, E=8 threads cpus 6-13, LPE=2 threads cpus 14-15.
set -eu

cd "$(dirname "$0")/.."

RUNS=${RUNS:-3}
OUT_BASE=results/profiling/raw/npb_full
BIN=benchmarks/NPB-OMP-C/bin

rm -rf "$OUT_BASE"
./scripts/drop_caches.sh

KERNELS="ep.B cg.B is.B mg.B"

echo "[pass_D] starting NPB full-tier sweep at $(date)"

for kernel in $KERNELS; do
  for r in $(seq 1 $RUNS); do
    for spec in "P 0-5 6" "E 6-13 8" "LPE 14-15 2"; do
      set -- $spec; tier=$1; cpuset=$2; nthr=$3
      OUT="$OUT_BASE/${kernel}/r$r"
      echo "[pass_D] $(date +%H:%M:%S) kernel=$kernel tier=$tier cpuset=$cpuset threads=$nthr run=$r"
      OMP_NUM_THREADS=$nthr ./scripts/measure_one.sh "$tier" "$cpuset" "$OUT" "$BIN/$kernel" > /dev/null
    done
  done
done

echo "[pass_D] done at $(date)"

echo ""
echo "=== NPB full-tier summary ==="
printf "%-6s %-3s %-3s %12s %10s %10s %10s %10s\n" \
  "bench" "tier" "run" "wall_s" "pkg_J" "core_J" "mops_s" "n_threads"
for kernel in $KERNELS; do
  for r in $(seq 1 $RUNS); do
    for t in P E LPE; do
      d=$OUT_BASE/${kernel}/r$r
      if [ -f "$d/$t.energy.txt" ]; then
        wall=$(grep wall_seconds "$d/$t.energy.txt" | cut -d= -f2)
        pkg=$(grep rapl_pkg_joules "$d/$t.energy.txt" | cut -d= -f2)
        core=$(grep rapl_core_joules "$d/$t.energy.txt" | cut -d= -f2)
        nthr=$(grep omp_num_threads "$d/$t.energy.txt" | cut -d= -f2)
        mops=$(grep 'Mop/s total' "$d/$t.stdout.txt" | awk '{print $NF}' | head -1)
        printf "%-6s %-3s %-3s %12s %10s %10s %10s %10s\n" \
          "$kernel" "$t" "$r" "$wall" "$pkg" "$core" "${mops:-NA}" "$nthr"
      fi
    done
  done
done
