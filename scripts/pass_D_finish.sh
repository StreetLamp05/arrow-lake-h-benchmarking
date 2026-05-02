#!/usr/bin/env bash
# Phase 2 Pass D finisher: run only is.B and mg.B full-tier, preserve existing ep/cg.
set -eu

cd "$(dirname "$0")/.."

RUNS=${RUNS:-3}
OUT_BASE=results/profiling/raw/npb_full
BIN=benchmarks/NPB-OMP-C/bin

rm -rf "$OUT_BASE/is.B" "$OUT_BASE/mg.B"
./scripts/drop_caches.sh

KERNELS="is.B mg.B"

echo "[pass_D_finish] starting at $(date)"

for kernel in $KERNELS; do
  for r in $(seq 1 $RUNS); do
    for spec in "P 0-5 6" "E 6-13 8" "LPE 14-15 2"; do
      set -- $spec; tier=$1; cpuset=$2; nthr=$3
      OUT="$OUT_BASE/${kernel}/r$r"
      echo "[pass_D_finish] $(date +%H:%M:%S) kernel=$kernel tier=$tier cpuset=$cpuset threads=$nthr run=$r"
      OMP_NUM_THREADS=$nthr ./scripts/measure_one.sh "$tier" "$cpuset" "$OUT" "$BIN/$kernel" > /dev/null
    done
  done
done

echo "[pass_D_finish] done at $(date)"

echo ""
echo "=== Full NPB full-tier summary (all 4 kernels) ==="
printf "%-6s %-3s %-3s %12s %10s %10s %10s %10s\n" \
  "bench" "tier" "run" "wall_s" "pkg_J" "core_J" "mops_s" "n_threads"
for kernel in ep.B cg.B is.B mg.B; do
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
