# Phase Field Fatigue Analysis Desktop App

A professional desktop application for simulating and analyzing fatigue crack propagation using the Phase-Field Fracture (PFF) approach.

## Overview

This application bridges the gap between complex numerical simulations and intuitive engineering analysis. It integrates `PhaseFieldX` and `FEniCSx` into a `wxPython` GUI, allowing researchers and engineers to:
- Configure material and fatigue properties.
- Automate mesh generation via Gmsh.
- Run high-fidelity Phase-Field simulations.
- Automatically predict fatigue life using compliance-based Paris' Law integration.

## Features

- **Intuitive GUI**: Built with `wxPython` for a native desktop experience.
- **Advanced Solvers**: Leverages `FEniCSx` for high-performance Finite Element Analysis.
- **Automated Crack Measurement**: Uses image skeletonization techniques to accurately track crack growth.
- **Interactive Visualization**: Real-time plotting of $a$ vs. $N$, $P$ vs. $u$, and compliance curves via `Matplotlib`.
- **MPI Support**: Optimized for parallel execution on multi-core systems.

## Tech Stack

- **Core**: Python 3.12+
- **GUI**: `wxPython`
- **Numerical engine**: `dolfinx` (FEniCSx), `PhaseFieldX`
- **Utilities**: `gmsh`, `scikit-image`, `numpy`, `matplotlib`
- **Environment**: Managed via `uv`

## Installation (Cross-Platform)

### macOS (Local Development)
The recommended way for macOS is via **Conda (conda-forge)** to handle the complex C++ dependencies:
```bash
conda create -n phasefield-fatigue-env python=3.12
conda activate phasefield-fatigue-env
conda install -c conda-forge fenics-dolfinx phasefieldx wxpython
```

### Ubuntu / Linux (Hybrid Hybrid setup)
On Ubuntu, use the official FEniCS PPA for system binaries and `uv` for the Python layer:
```bash
sudo add-apt-repository ppa:fenics-packages/fenics
sudo apt update
sudo apt install fenicsx
uv venv --system-site-packages
uv pip install .
```

### Windows
Native installation via `pip/uv` is not yet possible. Please use **WSL2** (follow Ubuntu instructions) or the **Conda-forge** method.

## CI/CD Workflow
A GitHub Actions pipeline is provided in `.github/workflows/ci.yml`. It uses:
- **Ubuntu**: Hybrid `apt` + `uv` runner.
- **Windows**: Conda-forge runner.

## Development

See [agents.md](agents.md) for detailed development roles and workflows.
