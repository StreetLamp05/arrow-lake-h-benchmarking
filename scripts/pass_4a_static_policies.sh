#!/usr/bin/env bash
# Phase 4a: mixed concurrent workload (6 cg.B + 4 ep.B + 2 stress-ng --io 1)
# run under four affinity policies. Wall time and package+core RAPL energy
# collected per run.
#
# Policies (pinning via taskset -c at launch):
#   cfs        unpinned
#   all_P      all 12 workers on CPUs 0-5
#   pe_split   cg.B on 0-5, ep.B on 6-13, I/O on 6-13
#   three_way  cg.B on 0-5, ep.B on 6-13, I/O on 14-15
set -eu

cd "$(dirname "$0")/.."

RUNS=${RUNS:-5}
OUT_BASE=results/scheduler/raw
NPB=benchmarks/NPB-OMP-C/bin

mkdir -p "$OUT_BASE"

RAPL_PKG=/sys/class/powercap/intel-rapl:0/energy_uj
RAPL_CORE=/sys/class/powercap/intel-rapl:0:0/energy_uj

read_rapl() {
  if [ -r "$1" ]; then cat "$1"; else echo 0; fi
}

sweep_workers() {
  pkill -9 -f 'benchmarks/NPB-OMP-C/bin/cg\.B' 2>/dev/null || true
  pkill -9 -f 'benchmarks/NPB-OMP-C/bin/ep\.B' 2>/dev/null || true
  pkill -9 -f 'stress-ng' 2>/dev/null || true
  sleep 0.5
}

cleanup_on_exit() {
  echo ""
  echo "[pass_4a] sweeping any stray workers before exit"
  sweep_workers
}
trap cleanup_on_exit EXIT INT TERM

MOST_RECENT_PID=""

launch_cg() {
  local idx=$1 pin=$2 outdir=$3
  local out="$outdir/cg_${idx}.out"
  local err="$outdir/cg_${idx}.err"
  if [ -n "$pin" ]; then
    OMP_NUM_THREADS=1 taskset -c "$pin" "$NPB/cg.B" > "$out" 2> "$err" &
  else
    OMP_NUM_THREADS=1 "$NPB/cg.B" > "$out" 2> "$err" &
  fi
  MOST_RECENT_PID=$!
}

launch_ep() {
  local idx=$1 pin=$2 outdir=$3
  local out="$outdir/ep_${idx}.out"
  local err="$outdir/ep_${idx}.err"
  if [ -n "$pin" ]; then
    OMP_NUM_THREADS=1 taskset -c "$pin" "$NPB/ep.B" > "$out" 2> "$err" &
  else
    OMP_NUM_THREADS=1 "$NPB/ep.B" > "$out" 2> "$err" &
  fi
  MOST_RECENT_PID=$!
}

launch_stress() {
  local idx=$1 pin=$2 outdir=$3
  local out="$outdir/stress_${idx}.out"
  local err="$outdir/stress_${idx}.err"
  if [ -n "$pin" ]; then
    taskset -c "$pin" stress-ng --io 1 --timeout 600s --metrics-brief \
      > "$out" 2> "$err" &
  else
    stress-ng --io 1 --timeout 600s --metrics-brief \
      > "$out" 2> "$err" &
  fi
  MOST_RECENT_PID=$!
}

run_policy() {
  local policy=$1 outdir=$2 run=$3
  mkdir -p "$outdir"

  local cg_pin ep_pin io_pin
  case "$policy" in
    cfs)       cg_pin="" ;      ep_pin="" ;      io_pin="" ;;
    all_P)     cg_pin="0-5" ;   ep_pin="0-5" ;   io_pin="0-5" ;;
    pe_split)  cg_pin="0-5" ;   ep_pin="6-13" ;  io_pin="6-13" ;;
    three_way) cg_pin="0-5" ;   ep_pin="6-13" ;  io_pin="14-15" ;;
    *) echo "unknown policy: $policy" >&2; exit 1 ;;
  esac

  sweep_workers
  ./scripts/drop_caches.sh > /dev/null

  local npb_pids=() stress_pids=()

  local t_start pkg_before core_before
  t_start=$(date +%s.%N)
  pkg_before=$(read_rapl "$RAPL_PKG")
  core_before=$(read_rapl "$RAPL_CORE")

  for i in 1 2 3 4 5 6; do
    launch_cg "$i" "$cg_pin" "$outdir"
    npb_pids+=("$MOST_RECENT_PID")
  done
  for i in 1 2 3 4; do
    launch_ep "$i" "$ep_pin" "$outdir"
    npb_pids+=("$MOST_RECENT_PID")
  done
  for i in 1 2; do
    launch_stress "$i" "$io_pin" "$outdir"
    stress_pids+=("$MOST_RECENT_PID")
  done

  for p in "${npb_pids[@]}"; do
    wait "$p" 2>/dev/null || true
  done

  local t_end pkg_after core_after
  t_end=$(date +%s.%N)
  pkg_after=$(read_rapl "$RAPL_PKG")
  core_after=$(read_rapl "$RAPL_CORE")

  for p in "${stress_pids[@]}"; do
    kill -TERM "$p" 2>/dev/null || true
  done
  pkill -TERM -f 'stress-ng' 2>/dev/null || true
  sleep 0.3
  for p in "${stress_pids[@]}"; do
    kill -9 "$p" 2>/dev/null || true
  done
  pkill -9 -f 'stress-ng' 2>/dev/null || true

  local wall pkg_j core_j
  wall=$(awk "BEGIN{printf \"%.3f\", $t_end - $t_start}")
  pkg_j=$(awk "BEGIN{printf \"%.3f\", ($pkg_after - $pkg_before) / 1e6}")
  core_j=$(awk "BEGIN{printf \"%.3f\", ($core_after - $core_before) / 1e6}")

  {
    echo "policy=$policy"
    echo "run=$run"
    echo "wall_seconds=$wall"
    echo "rapl_pkg_joules=$pkg_j"
    echo "rapl_core_joules=$core_j"
    echo "cg_pin=$cg_pin"
    echo "ep_pin=$ep_pin"
    echo "io_pin=$io_pin"
  } > "$outdir/metrics.txt"

  printf "  %-9s r%-2s wall=%8ss pkg=%9sJ core=%9sJ\n" \
    "$policy" "$run" "$wall" "$pkg_j" "$core_j"

  sweep_workers
}

if pgrep -f 'benchmarks/NPB-OMP-C/bin/(cg|ep)\.B|stress-ng' > /dev/null; then
  echo "[pass_4a] WARNING: NPB/stress processes already running. Sweeping first."
  sweep_workers
  if pgrep -f 'benchmarks/NPB-OMP-C/bin/(cg|ep)\.B|stress-ng' > /dev/null; then
    echo "[pass_4a] ERROR: could not clear stale processes. Investigate with:"
    echo "          pgrep -af 'benchmarks/NPB-OMP-C/bin/(cg|ep)\.B|stress-ng'"
    exit 1
  fi
fi

echo "[pass_4a] starting at $(date). runs=$RUNS per policy"
POLICIES="cfs all_P pe_split three_way"
for policy in $POLICIES; do
  echo "[pass_4a] policy=$policy"
  for r in $(seq 1 $RUNS); do
    outdir="$OUT_BASE/${policy}/r${r}"
    run_policy "$policy" "$outdir" "$r"
  done
done
echo "[pass_4a] done at $(date)"

echo ""
echo "=== Phase 4a summary ==="
printf "%-10s %-4s %10s %10s %10s\n" "policy" "run" "wall_s" "pkg_J" "core_J"
for policy in $POLICIES; do
  for r in $(seq 1 $RUNS); do
    f="$OUT_BASE/${policy}/r${r}/metrics.txt"
    if [ -f "$f" ]; then
      wall=$(grep wall_seconds "$f" | cut -d= -f2)
      pkg=$(grep rapl_pkg_joules "$f" | cut -d= -f2)
      core=$(grep rapl_core_joules "$f" | cut -d= -f2)
      printf "%-10s %-4s %10s %10s %10s\n" "$policy" "$r" "$wall" "$pkg" "$core"
    fi
  done
done

echo ""
echo "=== Policy means ==="
for policy in $POLICIES; do
  awk -v p="$policy" '
    BEGIN{nw=0}
    /wall_seconds=/{split($0,a,"="); nw++; sw+=a[2]}
    /rapl_pkg_joules=/{split($0,a,"="); sp+=a[2]}
    /rapl_core_joules=/{split($0,a,"="); sc+=a[2]}
    END{
      if (nw>0) printf "  %-10s wall_mean=%.2fs  pkg_mean=%.1fJ  core_mean=%.1fJ (n=%d)\n",
        p, sw/nw, sp/nw, sc/nw, nw
    }' "$OUT_BASE/${policy}"/r*/metrics.txt
done
