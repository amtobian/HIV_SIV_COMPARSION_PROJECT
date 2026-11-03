#!/bin/bash
set -ueo pipefail

# activate conda environment
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

# extract the conserved regions from the sequences - gag or pol 
bash 06a_extract_conserved_regions.sh
# multiple sequence alignment of the extracted conserved regions - use MAFFT
mafft --auto --thread 8 results/gag.fasta > results/gag.aln.fasta
# use IQ-TREE to build the phylogenetic tree from the aligned sequences
iqtree3 -s results/gag.aln.fasta -m MFP -B 1000 --alrt 1000 -T AUTO --prefix results/gag


# deactivate conda
conda deactivate