Installation Guide
==================

The Phase-Field Fatigue Suite requires a robust scientific Python environment with high-performance finite element solvers.

Quick Start (Recommended)
-------------------------
The most reliable way to set up the environment is using **Conda/Mamba**, as it handles complex dependencies like PETSc and MPI across multiple platforms.

.. code-block:: bash

   conda create -n fenicsx -c conda-forge fenics-dolfinx gmsh mpich pyvista wxpython
   conda activate fenicsx

Operating System Specifics
--------------------------

Windows (WSL2 Mandatory)
^^^^^^^^^^^^^^^^^^^^^^^^
FEniCSx does not support native Windows execution for high-performance physics.
1. Install **WSL2** (Ubuntu 22.04+) from the Microsoft Store.
2. Open the WSL terminal and follow the **Quick Start** (Conda) instructions above.
3. To view graphics (Gmsh/Plots), ensure you have an X-server like **WSLg** (Windows 11) or **VcXsrv** (Windows 10).

macOS (Intel & M-Series Silicon)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Install **Conda** (Miniforge recommended for M1/M2/M3 chips).
2. Follow the **Quick Start** instructions.
3. **Important**: If you have `mpich` or `openmpi` installed via Homebrew, run ``brew unlink mpich`` before starting to avoid conflicts.

Linux (Ubuntu/Debian)
^^^^^^^^^^^^^^^^^^^^^
You can use the native PPA for the best performance:

.. code-block:: bash

   sudo add-apt-repository ppa:fenics-packages/fenics
   sudo apt update
   sudo apt install fenicsx gmsh

Core Dependencies
-----------------
* **FEniCSx (DOLFINx)**: The finite element solver for the phase-field equations.
* **Gmsh**: Used for parametric specimen mesh generation.
* **wxPython**: Characterized by the native desktop GUI.
* **Matplotlib**: Real-time plotting and sensitivity mapping.
* **scikit-image**: Skeletonization core for crack tracking.

Troubleshooting
---------------
* **MPI Conflicts**: If you see "multiple MPI installations detected", ensure your system PATH isn't mixing Conda and System/Homebrew MPI versions.
* **Persistence**: Use ``uv`` to manage Python packages if you prefer a faster alternative to pip:
  ``uv pip install -e .``
