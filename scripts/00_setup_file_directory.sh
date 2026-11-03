#!/bin/bash
set -ueo pipefail

# create necessary directories that will be needed for the project 
mkdir -p results
mkdir -p output

# make the folders for the data in scr10
cd ~/scr10
mkdir -p data_project
cd ~/scr10/data_project
mkdir -p HIV SIV

# move back to HIV project 
cd ~/HIV_SIV_COMPARSION_PROJECT