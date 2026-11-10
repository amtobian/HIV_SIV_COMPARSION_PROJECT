#!/bin/bash
set -ueo pipefail

# create necessary directories that will be needed for the project 
mkdir -p results
mkdir -p output

# make the folders for the data in scr10
mkdir -p ${HOME}/scr10/data_project/{HIV,SIV}
