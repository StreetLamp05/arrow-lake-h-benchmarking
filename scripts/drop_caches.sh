#!/usr/bin/env bash
set -eu
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
echo "[drop_caches] done"
