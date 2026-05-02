#!/usr/bin/env bash
# For each (workload, tier), run the workload pinned to one CPU of the tier
# and sample MSR 0x17D2 on the same CPU at ~20 Hz for SAMPLE_SECONDS, then
# kill the workload. One log per combination at results/td/raw/<workload>_<tier>.log.
# Log line: <timestamp>\t<cpu>\t<raw_hex>\t<valid>\t<class_id>
# Workloads: idle, ep.B, cg.B, stream
set -eu

cd "$(dirname "$0")/.."

MSR=0x17D2
SAMPLE_SECONDS=${SAMPLE_SECONDS:-10}
SAMPLE_INTERVAL=${SAMPLE_INTERVAL:-0.05}   # 20 Hz
OUT_BASE=results/td/raw

sudo modprobe msr 2>/dev/null || true
mkdir -p "$OUT_BASE"

declare -A ANCHOR_CPU=( [P]=0 [E]=6 [LPE]=14 )
declare -A THREADS=(   [P]=1 [E]=1 [LPE]=1 )

launch_workload() {
  # $1=workload $2=cpu $3=threads
  local w=$1 cpu=$2 nth=$3
  case "$w" in
    idle)
      : ;;  # nothing
    ep.B|cg.B|mg.B|is.B)
      # Looped until killed so MSR sampling sees steady-state.
      bash -c "while true; do \
        OMP_NUM_THREADS=$nth taskset -c $cpu ./benchmarks/NPB-OMP-C/bin/$w; \
      done" > /dev/null 2>&1 &
      echo $! ;;
    stream)
      bash -c "while true; do \
        OMP_NUM_THREADS=$nth taskset -c $cpu ./benchmarks/STREAM/stream_omp; \
      done" > /dev/null 2>&1 &
      echo $! ;;
    *)
      echo "unknown workload: $w" >&2
      exit 1 ;;
  esac
}

sample_msr() {
  # $1=cpu $2=log_path $3=seconds
  local cpu=$1 log=$2 secs=$3
  local end
  end=$(awk -v s=$secs 'BEGIN{printf "%.3f", systime() + s}')
  : > "$log"
  while :; do
    local now raw raw_hex valid class_id
    now=$(date +%s.%N)
    raw=$(sudo rdmsr -p "$cpu" -u "$MSR" 2>/dev/null || echo "-1")
    if [ "$raw" != "-1" ]; then
      raw_hex=$(printf "0x%016x" "$raw")
      valid=$(( raw & 0x1 ))
      class_id=$(( (raw >> 8) & 0xFF ))
      printf "%s\t%s\t%s\t%s\t%s\n" "$now" "$cpu" "$raw_hex" "$valid" "$class_id" >> "$log"
    fi
    awk -v n=$now -v e=$end 'BEGIN{exit !(n<e)}' || break
    sleep "$SAMPLE_INTERVAL"
  done
}

echo "[td_sample] starting at $(date), ${SAMPLE_SECONDS}s per combination, ${SAMPLE_INTERVAL}s interval"

for workload in idle ep.B cg.B stream; do
  for tier in P E LPE; do
    cpu=${ANCHOR_CPU[$tier]}
    nth=${THREADS[$tier]}
    log="$OUT_BASE/${workload}_${tier}.log"
    echo "[td_sample] $(date +%H:%M:%S) workload=$workload tier=$tier cpu=$cpu threads=$nth"

    pid=""
    if [ "$workload" != "idle" ]; then
      pid=$(launch_workload "$workload" "$cpu" "$nth")
      # Give the workload a moment to enter steady state before sampling.
      sleep 1
    else
      sleep 1
    fi

    sample_msr "$cpu" "$log" "$SAMPLE_SECONDS"

    if [ -n "$pid" ]; then
      # Kill the looper and any spawned benchmark child.
      kill -9 "$pid" 2>/dev/null || true
      pkill -9 -P "$pid" 2>/dev/null || true
      # Also sweep any stragglers matching the workload binary name.
      case "$workload" in
        stream) pkill -9 -f stream_omp 2>/dev/null || true ;;
        *)      pkill -9 -f "${workload}" 2>/dev/null || true ;;
      esac
      wait "$pid" 2>/dev/null || true
    fi
    sleep 1  # settle between combinations
  done
done

echo "[td_sample] done at $(date)"
echo ""
echo "Logs written to $OUT_BASE/"
ls -la "$OUT_BASE"
