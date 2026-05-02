#!/usr/bin/env bash
# Read IA32_THREAD_FEEDBACK_CHAR (MSR 0x17D2) on every CPU; decode valid bit
# and class_id.
set -eu

cd "$(dirname "$0")/.."

MSR=0x17D2

sudo modprobe msr 2>/dev/null || true

if ! command -v rdmsr >/dev/null; then
  echo "ERROR: rdmsr not found. Install msr-tools: sudo dnf install -y msr-tools"
  exit 1
fi

echo "=== IA32_THREAD_FEEDBACK_CHAR (MSR $MSR) readback ==="
printf "%-4s %-5s %-18s %-6s %-9s\n" "cpu" "tier" "raw_hex" "valid" "class_id"

for cpu in $(seq 0 15); do
  if   [ "$cpu" -le 5 ];  then tier="P"
  elif [ "$cpu" -le 13 ]; then tier="E"
  else                         tier="LPE"
  fi

  raw=$(sudo rdmsr -p "$cpu" -u "$MSR" 2>/dev/null || echo "ERR")
  if [ "$raw" = "ERR" ]; then
    printf "%-4s %-5s %-18s %-6s %-9s\n" "$cpu" "$tier" "(unreadable)" "-" "-"
    continue
  fi

  raw_hex=$(printf "0x%016x" "$raw")
  valid=$(( raw & 0x1 ))
  class_id=$(( (raw >> 8) & 0xFF ))
  printf "%-4s %-5s %-18s %-6s %-9s\n" "$cpu" "$tier" "$raw_hex" "$valid" "$class_id"
done
