#!/bin/bash
set -ueo pipefail

# activate conda environment
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

# How much of the virus is conserved between different strains/subtypes/lineages?


# deactivate conda
conda deactivate