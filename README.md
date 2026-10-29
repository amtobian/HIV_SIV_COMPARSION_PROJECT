# HIV/SIV conservation comparison

This project collects HIV and simian immunodeficiency virus (SIV) genome sequences to investigate how they are conserved. Downloaded data is stored in Scratch 10 on an HPC. This project was completed for the class Supercomputing for Science class at William & Mary. Most of this project was competed on the bora node that has 2x Intel Xeon E5-2640 processors, 20 cores per node, 20 nodes, 64 GB of memory, on the 10 GbE/FDR IB network, and was deployed in 2017. 

## Current workflow

The scripts expect the data directories `~/scr10/data_project/HIV` and `~/scr10/data_project/SIV`. Create them before running the download script:

```bash
mkdir -p ~/scr10/data_project/HIV ~/scr10/data_project/SIV
```

### 1. Download genome data

Submit the batch script:

```bash
sbatch scripts/01_download_data.sbatch
```

It uses NCBI `datasets` to download complete genomes for the configured taxon IDs (11676, 57667, 12721, 35274, 11709, and SIV). The HIV downloads are saved as `HIV1.zip`, `Siminian-HIV.zip`, `HIV.zip`, `HIV3.zip`, and `HIV2.zip`; the SIV download is saved as `SIV.zip`. The ZIP files are saved in their corresponding HIV or SIV Scratch 10 directories. The script's Slurm output and error files are written to the directory from which the job was submitted.

### 2. Unpack the datasets

After the download job finishes successfully, run:

```bash
bash scripts/02_unpack_data.sh
```

This extracts each archive into its own subdirectory under the matching HIV or SIV directory.

### 3. Optionally remove the ZIP archives

After verifying that the extracted data is present and usable, run:

```bash
bash scripts/03_clean_up_data_folder.sh
```

This permanently removes the downloaded ZIP archives; the extracted directories are retained.

### 4. Create the Conda environment

Run:

```bash
bash scripts/04_create_conda_env.sh
```

The script loads Miniforge and creates the `hiv-comp-env` environment. It currently does not install project packages or run analysis code. To activate the environment in a later shell, initialize Conda and activate it:

```bash
module load miniforge3
eval "$(conda shell.bash hook)"
conda activate hiv-comp-env
```
