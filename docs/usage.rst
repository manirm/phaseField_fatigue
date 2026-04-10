User Guide
==========

Geometries and Meshing
----------------------
The suite supports three standard specimen types:

1. **Compact Tension (CT)**: Standard ASTM E399 geometry.
2. **Single Edge Notch Bending (SENB)**: Three-point bending setup.
3. **Center-Cracked Tension (CCT)**: Internal crack under remote tension.

Use the **Preview Mesh** button to visualize the refinement before running.

Simulation Modes
----------------
* **Quick Mode**: Uses Analytical Paris' Law for rapid fatigue life estimation.
* **Full Mode**: Uses the Variational Staggered Solver for research-grade crack propagation.

Environmental Fatigue (Hydrogen)
------------------------------
Enable Hydrogen Multi-physics in the Settings tab.
* **Diffusion Coefficient (D)**: Controls the speed of hydrogen transport.
* **Sensitivity (chi)**: Controls the severity of decohesion.

Batch Processing
----------------
The **Batch Manager** allows you to define parametric studies. 
To perform a Grid Search:
1. Enable the desired parameters in the Batch tab.
2. Input a comma-separated list of values (e.g., ``2.0, 3.0, 4.0`` for Gc).
3. Click **Generate & Run Batch**.
4. View the final trend in the **Sensitivity Analysis** chart.
