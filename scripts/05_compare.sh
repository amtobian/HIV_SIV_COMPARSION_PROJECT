#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/results"

module load miniforge3
module load mafft/gcc-11.4.1/7.525
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

if ! command -v mafft >/dev/null 2>&1; then
    echo "ERROR: MAFFT is unavailable after loading its module." >&2
    exit 1
fi

threads="${SLURM_CPUS_PER_TASK:-1}"
mkdir -p "$RESULTS_DIR"

if ! command -v datasets >/dev/null 2>&1; then
    echo "ERROR: NCBI datasets CLI is unavailable." >&2
    exit 1
fi

python "$SCRIPT_DIR/06a_extract_conserved_regions.py"

for region in env pol gag; do
    input="$RESULTS_DIR/${region}.fasta"
    alignment="$RESULTS_DIR/${region}.aln.fasta"

    if [[ ! -s "$input" ]]; then
        echo "ERROR: Expected extracted sequences in $input." >&2
        exit 1
    fi

    echo "Aligning $region sequences with $threads thread(s)..."
    mafft --auto --thread "$threads" --inputorder "$input" > "$alignment"
    if [[ ! -s "$alignment" ]]; then
        echo "ERROR: MAFFT produced an empty alignment for $region." >&2
        exit 1
    fi
done

python "$SCRIPT_DIR/06b_summarize_comparison.py"

echo "Comparison complete. Alignments and identity summaries are in $RESULTS_DIR."

conda deactivate