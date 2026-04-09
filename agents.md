# Agent Roles for Phase Field Fatigue App Development

To ensure a high-quality, professional desktop application, the development process is divided into specialized roles.

## 1. Frontend Agent (wxPython Specialist)
**Role**: Design and implement the GUI.
**Tasks**:
- Create a responsive `MainFrame` with split-view layout.
- Build custom input widgets with validation (e.g., float-only inputs for material constants).
- Integrate `Matplotlib` canvases into `wxPython` panels for real-time and post-simulation plotting.
- Implement simulation progress monitors and status indicators.

## 2. Backend Agent (Numerical Engine Specialist)
**Role**: Manage the FEniCSx and PhaseFieldX integration.
**Tasks**:
- Wrap the `PhaseFieldX` solver logic into a reusable `SimulationEngine` class.
- Orchestrate `Gmsh` mesh generation based on user parameters.
- Handle multi-processing and MPI execution to keep the UI responsive during resource-heavy simulations.
- Implement Paris' Law integration for cycle prediction.

## 3. Post-Processing & Data Agent
**Role**: Result analysis and visualization.
**Tasks**:
- Implement skeletonization-based crack measurement using `scikit-image`.
- Calculate specimen compliance and derivatives from simulation output.
- Manage data export to standard formats (`.xdmf`, `.vtu`) for Paraview.
- Develop data persistence logic for saving/loading simulation configurations.

## 4. DevOps & Environment Agent
**Role**: Project management and distribution.
**Tasks**:
- Maintain the `uv` environment and `pyproject.toml` dependencies.
- Configure logging and error handling across GUI and backend.
- Handle packaging for desktop distribution (e.g., using `PyInstaller` or `Nuitka`).
