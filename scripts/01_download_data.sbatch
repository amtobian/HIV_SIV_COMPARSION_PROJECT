#!/bin/bash
#SBATCH --job-name=DOWNLOAD_DATA
#SBATCH --nodes=1 # how many physical machines in the cluster
#SBATCH --ntasks=1 # how many separate 'tasks' (stick to 1)
#SBATCH --cpus-per-task=1
#SBATCH --time=180
#SBATCH --mail-type=FAIL,BEGIN,END # when to email you
#SBATCH --mail-user=amtobian@wm.edu # who to email
#SBATCH -o DOWNLOAD_DATA_%j.out #STDOUT to file (%j is jobID)
#SBATCH -e DOWNLOAD_DATA_%j.err #STDERR to file (%j is jobID)

echo "download data for project"

cd ~/scr10/data_project/HIV

datasets download virus genome taxon 11676 --complete-only --filename HIV1.zip

datasets download virus genome taxon 57667 --complete-only --filename Siminian-HIV.zip

datasets download virus genome taxon 12721 --complete-only --filename HIV.zip

datasets download virus genome taxon 35274 --complete-only --filename HIV3.zip

datasets download virus genome taxon 11709 --complete-only --filename HIV2.zip


cd ~/scr10/data_project/SIV

datasets download virus genome taxon SIV --complete-only --filename SIV.zip

echo "download data finished"
