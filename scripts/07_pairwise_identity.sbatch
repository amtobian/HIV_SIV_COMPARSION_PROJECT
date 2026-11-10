#!/bin/bash
#SBATCH --job-name=HIV_PAIRWISE_ID
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=50
#SBATCH --output=output/PAIRWISE_IDENTITY_%j.out
#SBATCH --error=output/PAIRWISE_IDENTITY_%j.err
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --mail-user=amtobian@wm.edu

PROJECT_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
WORKFLOW_SCRIPT="$PROJECT_ROOT/scripts/07_pairwise_identity.sh"

if [[ ! -f "$WORKFLOW_SCRIPT" ]]; then
    echo "ERROR: Could not find $WORKFLOW_SCRIPT." >&2
    echo "Submit this job from the project root directory." >&2
    exit 1
fi

cd "$PROJECT_ROOT"
bash "$WORKFLOW_SCRIPT"
