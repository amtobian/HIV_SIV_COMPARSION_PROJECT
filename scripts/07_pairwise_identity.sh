#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

module load miniforge3
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

python "$SCRIPT_DIR/07_plot_pairwise_identity.py"

conda deactivate
