#!/usr/bin/env bash
# Dumps kernel scheduling domain topology. Needs debugfs mounted (uses sudo).
set -eu

cd "$(dirname "$0")/.."
mkdir -p topology

sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true

SCHED=/sys/kernel/debug/sched
if [ ! -d "$SCHED/domains" ]; then
  echo "WARN: $SCHED/domains not present; kernel may not expose it."
  ls /sys/kernel/debug/ 2>&1 | head || true
  exit 0
fi

: > topology/sched_domains.txt
for d in "$SCHED"/domains/cpu*; do
  cpu=$(basename "$d")
  echo "=== $cpu ===" >> topology/sched_domains.txt
  for dom in "$d"/domain*; do
    name=$(sudo cat "$dom/name" 2>/dev/null || echo "?")
    flags=$(sudo cat "$dom/flags" 2>/dev/null || echo "?")
    groups=$(sudo cat "$dom/groups_flags" 2>/dev/null || echo "?")
    echo "  $(basename "$dom"): name=$name" >> topology/sched_domains.txt
    echo "    flags=$flags" >> topology/sched_domains.txt
    echo "    groups_flags=$groups" >> topology/sched_domains.txt
  done
done

echo "sched domain dump -> topology/sched_domains.txt"
