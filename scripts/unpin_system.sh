#!/usr/bin/env bash
# Restore normal desktop behavior after benchmark session.
set -eu

echo "[unpin] schedutil governor on all CPUs"
sudo cpupower frequency-set -g schedutil >/dev/null || \
  sudo cpupower frequency-set -g powersave >/dev/null

echo "[unpin] re-enable Intel Turbo Boost"
echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null

echo "[unpin] re-enable ASLR"
echo 2 | sudo tee /proc/sys/kernel/randomize_va_space >/dev/null

echo "[unpin] done"
