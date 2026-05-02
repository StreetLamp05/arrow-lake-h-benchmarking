#!/usr/bin/env bash
# Phase 1 topology dump. Safe to re-run.
set -eu

cd "$(dirname "$0")/.."
mkdir -p topology

# Static
lscpu --extended=CPU,CORE,SOCKET,NODE,MAXMHZ,MINMHZ > topology/lscpu.txt
lscpu -J > topology/lscpu.json
lstopo --output-format svg topology/lstopo.svg 2>/dev/null
lstopo --of console --no-io > topology/lstopo.txt
cat /proc/cpuinfo > topology/cpuinfo.txt

# Max freq per CPU (authoritative tier key)
: > topology/cpu_max_freq.txt
for c in /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq; do
  cpu=$(basename "$(dirname "$(dirname "$c")")")
  echo "$cpu $(cat "$c")" >> topology/cpu_max_freq.txt
done
sort -V -o topology/cpu_max_freq.txt topology/cpu_max_freq.txt

# EAS capacity
: > topology/cpu_capacity.txt
for c in /sys/devices/system/cpu/cpu*/cpu_capacity; do
  cpu=$(basename "$(dirname "$c")")
  echo "$cpu $(cat "$c")" >> topology/cpu_capacity.txt
done
sort -V -o topology/cpu_capacity.txt topology/cpu_capacity.txt

# Cache topology per CPU
: > topology/cache_topology.txt
for i in $(seq 0 15); do
  echo "=== cpu$i ===" >> topology/cache_topology.txt
  for idx in /sys/devices/system/cpu/cpu$i/cache/index*; do
    lvl=$(cat "$idx/level")
    typ=$(cat "$idx/type")
    size=$(cat "$idx/size")
    shared=$(cat "$idx/shared_cpu_list")
    echo "  L${lvl} ${typ} size=${size} shared_with=${shared}" >> topology/cache_topology.txt
  done
done

echo "topology dump written to topology/"
