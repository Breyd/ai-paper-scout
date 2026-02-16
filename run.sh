#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
PYTHONWARNINGS="ignore:NotOpenSSLWarning" PYTHONPATH=src python src/paper_scout/main.py "$@"
