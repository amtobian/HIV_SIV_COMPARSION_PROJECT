#!/bin/bash
set -ueo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# activate conda environment
module load miniforge3
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

# Extract annotated env, pol, and gag CDS features from GenBank .gbff files.
# The Python script writes one FASTA per region and reports regions with no matches.

python "$SCRIPT_DIR/06a_extract_conserved_regions.py"

# deactivate conda
conda deactivate