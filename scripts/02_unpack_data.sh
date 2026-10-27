#!/bin/bash
set -ueo pipefail

# move into the right directory

cd ~/scr10/data_project/HIV

# Unzip each dataset into its own directory

for virus in HIV HIV1 HIV2 HIV3 Siminian-HIV
do
    echo "Unzipping ${virus}.zip..."

    mkdir -p "$virus"
    unzip -o "${virus}.zip" -d "$virus"

    echo "Finished ${virus}"
done


# move into SIV directory 

cd ~/scr10/data_project/SIV

mkdir SIV
unzip SIV.zip -d SIV


echo "All datasets have been unzipped."
