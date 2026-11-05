#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

module load miniforge3
eval "$(conda shell.bash hook)"

if conda env list | awk '$1 == "hiv-comp-env" { found = 1 } END { exit !found }'; then
    conda env update --name hiv-comp-env --file hiv-comp-env.yml --prune
else
    conda env create --file hiv-comp-env.yml
fi

mkdir -p results
