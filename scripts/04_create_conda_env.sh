#!/bin/bash
set -ueo pipefail

# load module with conda in it?
module load miniforge3

# initalize conda
eval "$(conda shell.bash hook)"

#create conda environment
conda create --name hiv-comp-env

# activate conda
conda activate hiv-comp-env

# make results directory
mkdir -p results

# do stuff  -- what modules do i need to activate
# something for the comparison of sequences
# load python  -- python/gcc-11.4.1/3.11.9
module load python/gcc-11.4.1/3.11.9
# mafft for alignment of sequences
module load mafft/gcc-11.4.1/7.525
# iqtree for building phylogenetic trees
module load iqtree/3.0.1 


# i will need to export the yml file for the environment at some point
conda env export > hiv-comp-env.yml

# deactivate conda
conda deactivate