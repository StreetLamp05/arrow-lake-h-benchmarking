#!/usr/bin/env bash
# Phase 2 Pass C finisher: run only is.B and mg.B, 3 tiers, 3 runs each.
# Assumes ep.B and cg.B data already exists in results/profiling/raw/npb_1t/.

set -eu

cd "$(dirname "$0")/.."

RUNS=${RUNS:-3}
OUT_BASE=results/profiling/raw/npb_1t
BIN=benchmarks/NPB-OMP-C/bin


rm -rf "$OUT_BASE/is.B" "$OUT_BASE/mg.B"

./scripts/drop_caches.sh

KERNELS="is.B mg.B"

echo "[pass_C_finish] starting at $(date)"

for kernel in $KERNELS; do
  for r in $(seq 1 $RUNS); do
    for spec in "P 0" "E 6" "LPE 14"; do
      set -- $spec; tier=$1; cpu=$2
      OUT="$OUT_BASE/${kernel}/r$r"
      echo "[pass_C_finish] $(date +%H:%M:%S) kernel=$kernel tier=$tier cpu=$cpu run=$r"
      OMP_NUM_THREADS=1 ./scripts/measure_one.sh "$tier" "$cpu" "$OUT" "$BIN/$kernel" > /dev/null
    done
  done
done

echo "[pass_C_finish] done at $(date)"

echo ""
echo "=== Full NPB 1-thread summary (all 4 kernels) ==="
printf "%-6s %-3s %-3s %12s %10s %10s %10s\n" \
  "bench" "tier" "run" "wall_s" "pkg_J" "core_J" "mops_s"
for kernel in ep.B cg.B is.B mg.B; do
  for r in $(seq 1 $RUNS); do
    for t in P E LPE; do
      d=$OUT_BASE/${kernel}/r$r
      if [ -f "$d/$t.energy.txt" ]; then
        wall=$(grep wall_seconds "$d/$t.energy.txt" | cut -d= -f2)
        pkg=$(grep rapl_pkg_joules "$d/$t.energy.txt" | cut -d= -f2)
        core=$(grep rapl_core_joules "$d/$t.energy.txt" | cut -d= -f2)
        mops=$(grep 'Mop/s total' "$d/$t.stdout.txt" | awk '{print $NF}' | head -1)
        printf "%-6s %-3s %-3s %12s %10s %10s %10s\n" \
          "$kernel" "$t" "$r" "$wall" "$pkg" "$core" "${mops:-NA}"
      fi
    done
  done
done
