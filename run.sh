#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
PYTHONPATH=src python src/paper_scout/main.py "$@"
