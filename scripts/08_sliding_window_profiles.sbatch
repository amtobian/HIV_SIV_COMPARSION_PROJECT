#!/bin/bash
#SBATCH --job-name=HIV_WINDOW_PROFILES
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=30
#SBATCH --output=output/SLIDING_WINDOW_PROFILES_%j.out
#SBATCH --error=output/SLIDING_WINDOW_PROFILES_%j.err
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --mail-user=amtobian@wm.edu

PROJECT_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
WORKFLOW_SCRIPT="$PROJECT_ROOT/scripts/08_sliding_window_profiles.sh"

if [[ ! -f "$WORKFLOW_SCRIPT" ]]; then
    echo "ERROR: Could not find $WORKFLOW_SCRIPT." >&2
    echo "Submit this job from the project root directory." >&2
    exit 1
fi

cd "$PROJECT_ROOT"
bash "$WORKFLOW_SCRIPT"
