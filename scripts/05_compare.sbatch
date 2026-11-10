#!/bin/bash
#SBATCH --job-name=HIV_COMPARE_V2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=1000
#SBATCH --output=output/COMPARE_V2_%j.out
#SBATCH --error=output/COMPARE_V2_%j.err
#SBATCH --mail-type=FAIL,BEGIN,END # when to email you
#SBATCH --mail-user=amtobian@wm.edu # who to email

bash scripts/05_compare.sh