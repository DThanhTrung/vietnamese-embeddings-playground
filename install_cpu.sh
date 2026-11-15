#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TORCH_CPU_INDEX_URL="https://download.pytorch.org/whl/cpu"
TORCH_REQUIREMENT="torch>=2.6,<2.7"
TORCHVISION_REQUIREMENT="torchvision>=0.21,<0.22"

cd "$PROJECT_ROOT"

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install \
  --index-url "$TORCH_CPU_INDEX_URL" \
  "$TORCH_REQUIREMENT" \
  "$TORCHVISION_REQUIREMENT"

grep -vE '^[[:space:]]*(torch|torchvision)([[:space:]]|$)' requirements.txt \
  | "$PYTHON_BIN" -m pip install -r /dev/stdin

echo "CPU dependencies installed successfully."