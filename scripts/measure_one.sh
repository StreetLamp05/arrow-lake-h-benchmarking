#!/usr/bin/env bash
# Run one benchmark pinned to one CPU set, record perf stat output and RAPL
# package+core energy bracketed across the run.
#
# Usage: scripts/measure_one.sh <tier:P|E|LPE> <cpu_id_or_set> <outdir> <command...>

set -eu


ulimit -s unlimited

TIER=$1
CPU=$2
OUT=$3
shift 3

mkdir -p "$OUT"

case "$TIER" in
  P)   PMU=cpu_core ;;
  E)   PMU=cpu_atom ;;
  LPE) PMU=cpu_lowpower ;;
  *) echo "Unknown tier: $TIER (expected P|E|LPE)" >&2; exit 1 ;;
esac


EVENTS="${PMU}/instructions/,${PMU}/cycles/,${PMU}/cache-references/,${PMU}/cache-misses/,task-clock"


RAPL_PKG=/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj
RAPL_CORE=/sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj

read_rapl() {
  local f=$1
  if [ -r "$f" ]; then cat "$f"; else echo 0; fi
}

echo "[measure] tier=$TIER cpu=$CPU pmu=$PMU out=$OUT"
echo "[measure] cmd: $*"



PKG_BEFORE=$(read_rapl "$RAPL_PKG")
CORE_BEFORE=$(read_rapl "$RAPL_CORE")
T_START=$(date +%s.%N)


: ${OMP_NUM_THREADS:=1}
: ${OMP_PROC_BIND:=close}
: ${OMP_PLACES:=cores}
: ${OMP_STACKSIZE:=512M}
export OMP_NUM_THREADS OMP_PROC_BIND OMP_PLACES OMP_STACKSIZE

taskset -c "$CPU" \
  perf stat -o "$OUT/${TIER}.perf.txt" -e "$EVENTS" \
  "$@" > "$OUT/${TIER}.stdout.txt" 2> "$OUT/${TIER}.stderr.txt"

T_END=$(date +%s.%N)
PKG_AFTER=$(read_rapl "$RAPL_PKG")
CORE_AFTER=$(read_rapl "$RAPL_CORE")


PKG_J=$(awk "BEGIN{printf \"%.3f\", ($PKG_AFTER - $PKG_BEFORE) / 1e6}")
CORE_J=$(awk "BEGIN{printf \"%.3f\", ($CORE_AFTER - $CORE_BEFORE) / 1e6}")
WALL=$(awk "BEGIN{printf \"%.3f\", $T_END - $T_START}")

{
  echo "tier=$TIER"
  echo "cpu=$CPU"
  echo "pmu=$PMU"
  echo "omp_num_threads=$OMP_NUM_THREADS"
  echo "wall_seconds=$WALL"
  echo "rapl_pkg_joules=$PKG_J"
  echo "rapl_core_joules=$CORE_J"
} > "$OUT/${TIER}.energy.txt"

echo "[measure] === perf summary ==="
cat "$OUT/${TIER}.perf.txt"
echo ""
echo "[measure] === energy ==="
cat "$OUT/${TIER}.energy.txt"
echo ""
echo "[measure] === last 20 lines of program stdout ==="
tail -20 "$OUT/${TIER}.stdout.txt"
