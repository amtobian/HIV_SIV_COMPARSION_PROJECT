#!/bin/bash
set -ueo pipefail

# activate conda environment
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

# extract the conserved regions from the sequences - gag or pol 

# multiple sequence alignment of the extracted conserved regions - use MAFFT

# use IQ-TREE to build the phylogenetic tree from the aligned sequences


# deactivate conda
conda deactivate