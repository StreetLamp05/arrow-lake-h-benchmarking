#!/usr/bin/env bash
# Per-boot: make RAPL energy_uj files world-readable, pre-cache sudo.
set -eu

echo "[prep] chmod RAPL energy_uj files"
for f in \
  /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj \
  /sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj \
  /sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:1/energy_uj
do
  sudo chmod a+r "$f" 2>/dev/null || true
  ls -l "$f"
done

echo "[prep] sudo refresh"
sudo -v

echo "[prep] done"
