#!/bin/bash
set -ueo pipefail

# activate conda environment
module load miniforge3
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env

# extract the conserved regions from the sequences - gag or pol
# will get results/gag.fasta and results/pol.fasta out of this script
# need annotated genome files - GenBank .gbff files
#1) search the unpacked HIV and SIV datasets for .gbff files
#2) read each record's annotated CDS features to extract the conserved regions labeled gag or pol
#3) extract the feature's nucleotide sequence, preserving its strand and location and write one fasta per gene
#4) report genomes with no mathcing feature and check for duplicate of unual annotation 

# run python file 
python 06a_extract_conserved_regions.py

# deactivate conda
conda deactivate