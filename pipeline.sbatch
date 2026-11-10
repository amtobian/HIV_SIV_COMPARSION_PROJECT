#!/bin/bash
#SBATCH --job-name=FULL_PIPELINE
#SBATCH --nodes=1 # how many physical machines in the cluster
#SBATCH --ntasks=1 # how many separate 'tasks' (stick to 1)
#SBATCH --cpus-per-task=1
#SBATCH --time=2-00:00
#SBATCH --mail-type=FAIL,BEGIN,END # when to email you
#SBATCH --mail-user=amtobian@wm.edu # who to email
#SBATCH -o FULL_PIPELINE_%j.out #STDOUT to file (%j is jobID)
#SBATCH -e FULL_PIPELINE_%j.err #STDERR to file (%j is jobID)

# Run script to setup file directory 
bash scripts/00_setup_file_directory.sh 

# Run script to download data and clean up folders
bash scripts/01_download_data.sbatch 
bash scripts/03_clean_up_data_folder.sh

# Create Conda Environment 
bash scripts/04_create_conda_env.sh

# Initial Comparisons 
bash scripts/05_compare.sh

# Pairwise Comparisons 
bash scripts/07_pairwise_identity.sh 


# Complete 
echo "Pipeline Complete!" 