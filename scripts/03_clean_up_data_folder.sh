#!/bin/bash
set -ueo pipefail

# move into the right place 
cd ~/scr10/data_project/HIV

# force remove the zipped folders that are not needed anymore 
rm -rf HIV.zip
rm -rf HIV1.zip
rm -rf HIV2.zip
rm -rf HIV3.zip
rm -rf Siminian-HIV.zip

# move into SIV folder
cd ~/scr10/data_project/SIV

rm -rf SIV.zip
