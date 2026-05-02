#!/usr/bin/env bash
# Reproducibility for benchmark runs.
# Run once at the start of a benchmark session; unpin_system.sh reverses.
set -eu

cd "$(dirname "$0")/.."
mkdir -p logs

echo "[pin] performance governor on all CPUs"
sudo cpupower frequency-set -g performance >/dev/null

echo "[pin] disable Intel Turbo Boost"
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null

echo "[pin] disable ASLR"
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space >/dev/null

echo "[pin] drop caches"
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null

STAMP=$(date +%Y%m%d_%H%M%S)
echo "[pin] recording baseline to logs/baseline_${STAMP}.txt"
{
  echo "=== uname ===";            uname -a
  echo "=== kernel cmdline ===";   cat /proc/cmdline
  echo "=== turbo ===";            cat /sys/devices/system/cpu/intel_pstate/no_turbo
  echo "=== governor (cpu0) ===";  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
  echo "=== aslr ===";             cat /proc/sys/kernel/randomize_va_space
  echo "=== meminfo ===";          grep -E 'MemTotal|MemFree|MemAvailable' /proc/meminfo
  echo "=== thermal ===";          sensors 2>/dev/null || echo "(sensors not installed)"
} > "logs/baseline_${STAMP}.txt"

echo "[pin] done. Baseline: logs/baseline_${STAMP}.txt"
