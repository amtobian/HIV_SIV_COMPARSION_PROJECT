# Agent Instructions

## 1. General HPC Usage and Resource Restrictions

- Do not run commands on a Research Computing (RC) login/front-end node if they are expected to take more than 30 seconds on a single core. Submit longer-running work through the appropriate SLURM job instead.
- **Never run VS Code Server or AI coding agents directly on Research Computing SLURM or Kubernetes front-end/login nodes.** W&M prohibited this practice effective October 20, 2026.
- Use `dev.sciclone.wm.edu` for lightweight interactive development, VS Code, AI coding agents, file management, and SLURM job submission.
- Use an interactive SLURM compute allocation when development requires dedicated CPU, memory, or GPU resources.
- Submit computationally intensive workloads, large-scale data processing, large compilations, and GPU-intensive applications through SLURM or authorized Kubernetes workloads.
- The development server is not a compute node. It is a shared development and job-management environment.
- Keep CPU and memory usage on the development server low. Processes that exceed server resource limits may be terminated automatically. These restrictions also apply to AI coding agents.
- Never assume that a command is safe to run interactively simply because it is being executed through VS Code or an AI agent.

## 2. Development Server (dev.sciclone.wm.edu)

### Intended Uses

Use the W&M Research Computing development server for:

- VS Code Remote SSH connections.
- Lightweight code development and debugging.
- AI coding assistants and agents.
- Preparing and submitting SLURM jobs.
- Monitoring and managing SLURM jobs.
- Editing, organizing, and transferring files.
- Preparing Python environments and software configurations.
- Managing authorized Kubernetes workloads using `kubectl`.

### Storage

- Each user has a persistent local directory at `/local/$USER`.
- Use `/local/$USER` for VS Code Server installations, remote development tools, and regenerable development data.
- Configure VS Code Server to install under `/local/$USER/.vscode-server` instead of the default `~/.vscode-server`.
- The development server's local storage is persistent but is NOT backed up.
- Data may be lost if the server or local storage fails.
- Do not store the only copy of important research data, source code, or project files in `/local/$USER`.
- Store important research data and source code on appropriate Research Computing shared storage systems.
- Do not move or delete existing research data without explicit authorization.

### VS Code Remote SSH Configuration

When configuring VS Code on the development server:

1. Install the Remote - SSH extension on the local computer.
2. Connect to `dev.sciclone.wm.edu`.
3. Configure VS Code Server to use `/local/$USER`.

The following setting should be added to the local VS Code `settings.json`, replacing `$USER` with the actual Research Computing username:

```json
{
    "remote.SSH.serverInstallPath": {
        "dev": "/local/USERNAME"
    }
}
```

Do not assume that the VS Code Server installation should be placed in the shared home directory.

## 3. Software Modules and Python Environments

The development server uses the environment module system.

- Use `module avail` to inspect available software modules.
- Use `module list` to inspect currently loaded modules.
- Do not assume a module version is available without checking.
- Avoid loading conflicting module versions simultaneously.

### Conda

- Do not run `conda init`; it modifies the user's `.bashrc`.
- Before using Conda, load the `miniforge3` module.
- The documented development-server version is `miniforge3/24.9.2-0`. Check `module avail` if this version is unavailable.
- Initialize Conda only in the current shell:

```bash
module load miniforge3/24.9.2-0
eval "$(conda shell.bash hook)"
```

- Do not modify shell startup files unless explicitly requested.
- Reuse existing project environments when appropriate.
- Do not recreate or overwrite existing environments without checking their contents and dependencies first.

### Python

The development server also provides Python and uv modules.

Documented module versions:

- `python/3.12.7`
- `uv/0.13.1`

Load them as needed:

```bash
module load python/3.12.7
module load uv/0.13.1
```

Use `uv` or Conda for Python environment management when appropriate. Avoid unnecessary installation of duplicate packages or environments.

Python environments can be prepared on the development server, but computationally intensive applications must execute on appropriate compute resources.

## 4. SLURM Cluster Selection and Job Management

The development server can communicate with multiple Research Computing SLURM clusters.

**Always identify the intended cluster before submitting or managing jobs.**

Available documented SLURM modules:

| Module | Cluster |
|---|---|
| `slurm/astral` | Astral |
| `slurm/bora` | Bora, including Hima resources |
| `slurm/femto` | Femto |
| `slurm/gulf` | Gulf |
| `slurm/gust` | Gust |
| `slurm/kuro` | Kuro |

### Selecting a Cluster

For example, to use Bora:

```bash
module load slurm/bora
```

To switch from Astral to Bora:

```bash
module unload slurm/astral
module load slurm/bora
```

### Job Management

Once the appropriate SLURM module is loaded, use:

```bash
sinfo
squeue -u $USER
sbatch job.sh
```

Other available commands include:

- `sacct` — inspect job accounting and completed jobs.
- `scancel` — cancel jobs.
- `sinfo` — inspect cluster partitions and available resources.
- `squeue` — inspect queued and running jobs.
- `sbatch` — submit batch jobs.

Important:

- SLURM commands operate on the cluster selected by the currently loaded SLURM module.
- Always verify the selected cluster before submitting, monitoring, or canceling jobs.
- Never assume that a job was submitted to the intended cluster without checking.
- Jobs execute on SLURM compute nodes, not on the development server.
- Prefer `sbatch` for longer-running computational work rather than occupying interactive resources unnecessarily.
- Follow project-specific resource requirements and existing SLURM script conventions.

## 5. Interactive SLURM Development

When development requires dedicated CPU, memory, or GPU resources, use an interactive SLURM allocation.

W&M supports connecting VS Code directly to an allocated SLURM compute node through SSH configurations.

Important considerations:

- Interactive allocations are subject to SLURM queue availability.
- Allocations have CPU, memory, GPU, and time limits.
- AI coding agents running inside an allocation are subject to the same resource limits.
- Reconnecting through VS Code may request a new allocation.
- VS Code may establish multiple SSH connections during startup, potentially creating multiple allocations.
- Important files must reside on appropriate shared storage rather than temporary compute-node storage.

Do not configure or initiate interactive VS Code allocations unless they are necessary for the requested work.

When an interactive allocation is necessary, verify the appropriate cluster, resource requirements, and time limit first.

## 6. Kubernetes

Kubernetes access is enabled by default on the development server.

No additional environment module is required.

Example commands:

```bash
kubectl get pods -n YOUR_NAMESPACE
kubectl get jobs -n YOUR_NAMESPACE
kubectl describe pod POD_NAME -n YOUR_NAMESPACE
```

Important:

- Kubernetes access is subject to existing user permissions.
- Workloads execute on Kubernetes worker nodes, not on the development server.
- Do not create, modify, or delete Kubernetes workloads unless explicitly required by the task.
- Do not assume that the user has permission to access every namespace or resource.

## 7. Project Development and File Management

- Inspect the existing project structure before modifying files.
- Preserve existing directory structures, naming conventions, and established workflows.
- Do not overwrite existing data, results, scripts, or configurations without understanding their purpose.
- Do not move important project files to temporary or unbacked storage.
- Keep computational outputs in the appropriate project directories.
- Avoid generating unnecessary intermediate files or duplicate datasets.
- Use existing software installations and environments whenever possible.
- Verify that commands are being executed on the appropriate system before running them.

## 8. Documentation Requirements

- Update the relevant README automatically when a change affects documented setup, usage, workflows, outputs, or requirements.
- Keep documentation accurate and limit updates to what the change makes necessary.
- Document new dependencies, environment requirements, SLURM configuration changes, and execution instructions.
- Do not document commands or workflows that have not been verified.
- Distinguish between commands intended for the development server, login nodes, and compute nodes.

## 9. Prompt and Action Logging

- Add an entry to `prompt_action_log.md` for every user request and whenever changes are made in this assignment.
- Keep entries brief.
- Each entry must include:
  - Date.
  - User request.
  - Model name/version.
  - Actions taken.
- If the model name or version is not available, explicitly state that it is unavailable rather than guessing.
- Do not fabricate actions or claim that files were modified when they were not.
- Preserve existing log entries; append new entries rather than replacing historical records.

## 10. Official W&M Research Computing Documentation

Use the following official documentation as the primary reference for Research Computing development-server procedures:

- Development server, VS Code, and AI agents: https://www.wm.edu/offices/it/services/researchcomputing/atwm/dev-server/
- SLURM job submission and management: Refer to the official W&M Research Computing documentation linked from the development-server page.
- Python environment management: https://docs.astral.sh/uv/
- Python environments using uv and pip: https://docs.astral.sh/uv/pip/environments/

When instructions in this file conflict with updated official W&M Research Computing policies, prioritize current university policies and inform the user of the conflict.

Do not assume that documented module versions, cluster availability, or system configurations will remain unchanged. Verify them when necessary.