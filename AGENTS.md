# Agent instructions

- Do not run commands on a login node if they are expected to take more than 30 seconds on a single core. Submit longer-running work through the appropriate SLURM job instead.
- Do not run `conda init`; it modifies the user's `.bashrc`.
- Before using Conda, load the `miniforge3` module, then initialize Conda only in the current shell with:
  ```bash
  eval "$(conda shell.bash hook)"
  ```
- Update the relevant README automatically when a change affects documented setup, usage, workflows, outputs, or requirements. Keep documentation accurate and limit updates to what the change makes necessary.
- Add an entry to `prompt_action_log.md` for every user request and whenever you make changes in this assignment. Keep entries brief and include the date, request, model name/version, and actions taken. If the model name or version is not available, say so rather than guessing.
