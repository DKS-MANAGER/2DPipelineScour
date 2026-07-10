# 2DPipelineScour: Eulerian-Eulerian Two-Phase SedFoam Reference Case



This repository contains the reference case setup for **2D Pipeline Scour** around a cylinder on an erodible bed, simulated using the two-fluid Eulerian-Eulerian **SedFoam** solver (compiled as `sedFoam_rbgh`) in OpenFOAM.

This case serves as the physical baseline and validation standard for the moving-mesh, finite-area morphodynamics transition solver (`sedExnerFoam`).

---
## Prerequisites
* OpenFOAM v[Version] / SedFoam (`sedFoam_rbgh`)
* Python 3.x (numpy, pandas)

## Physical Setup
* **Domain**: x: [-0.75, 1.0] m, y: [-0.1, 0.205] m.
* **Bed**: Horizontal interface at y = -0.025 m. Porosity 0.40, hindrance exponent 2.65.
* **Cylinder**: D = 0.05 m, fixed. Gap e = 0.010 m (e/D = 0.2). Center at x = 0.0 m, y = 0.010 m.
* **Fluid**: Density 1000 kg/m3, kinematic viscosity 1e-6 m2/s.
* **Sediment**: Quartz sand. Density 2650 kg/m3, d50 = 0.36 mm.
* **Physics**: Wilcox twophasekOmega, kinetic granular stress, mesh diffusion.

## Execution
``` bash
./Allclean
./Allrun
```

## 📌 Project Overview & Physical Setup

The goal of this simulation is to resolve the detailed fluid-sediment mechanics and scour development underneath a pipeline cylinder using a complete two-phase Eulerian description.

### Baseline Geometry
* **Simulation Domain**: $x \in [-0.75, 1.0]\text{ m}$, $y \in [-0.1, 0.205]\text{ m}$.
* **Initial Erodible Bed**: Horizontal interface located at $y = -0.025\text{ m}$.
* **Pipeline Cylinder**: Diameter $D = 0.05\text{ m}$, fixed rigid position. Gap $e = 0.010\text{ m}$, gap-to-diameter ratio $e/D = 0.2$. Cylinder center located at $x = 0.0\text{ m}$, $y = 0.010\text{ m}$ (applied via `translateVector (0 0.010 0)` transform in `snappyHexMeshDict`; STL geometry is centered at origin).
* **Mesh Resolution**: Fine mesh around the cylinder and along the seabed to capture granular shear, vortex shedding, and scour velocity gradients.

### Fluid & Sediment Properties
* **Fluid (Water / Phase B)**: Density $\rho_f = 1000\text{ kg/m}^3$, kinematic viscosity $\nu_f = 10^{-6}\text{ m}^2\text{/s}$.
* **Sediment (Quartz Sand / Phase A)**: Density $\rho_s = 2650\text{ kg/m}^3$ (specific gravity $s = 2.65$), median grain diameter $d_{50} = 0.36\text{ mm}$ ($3.6 \times 10^{-4}\text{ m}$).
* **Erodible Bed Properties**: Porosity $\lambda_s = 0.40$, hindrance exponent $h_{exp} = 2.65$ (Richardson-Zaki drag correction).

---

## 🔄 Two-Phase Eulerian Physics & Settings

Unlike single-phase moving-bed solvers, SedFoam resolves the Navier-Stokes equations for both the fluid phase and the sediment phase (volume fraction `alpha.a`/`alpha.b`) throughout the entire 3D mesh volume.

* **Turbulence Model**: Wilcox (2006) twophasekOmega with density stratification corrections, resolving turbulence fields `k.b` and `omega.b` for the fluid phase.
* **Granular Stress**: Solved using kinetic theory and granular rheology models (frictional stress models, particle pressure, and interphase drag).
* **Grid Deformation**: Grid motion is enabled via mesh diffusion using OpenFOAM's mesh motion solvers to track the changing boundary interfaces.

---

## 🚀 Simulation Workflow & Execution

The simulation is configured to run in parallel using MPI decomposition.

1. **Clean the Case**:
   ```bash
   ./Allclean
   ```
2. **Generate the Mesh & Run the Solver**:
   Run the automated `Allrun` script:
   ```bash
   ./Allrun
   ```
   The script performs the following operations:
   * **Mesh Generation**: Cleans the polyMesh, runs `blockMesh`, edits boundary patches for snappy compatibility, runs `snappyHexMesh` to snap the grid around the cylinder, and applies `extrudeMesh` to create the 2D domain.
   * **Boundary/Field Initialization**: Copies the initial templates from `0_org/` to the active `0/` folder.
   * **Domain Decomposition**: Decomposes the case into 16 partitions using `decomposePar`.
   * **Parallel Execution**: Launches the parallel MPI task on 16 cores:
     ```bash
     mpirun -np 16 sedFoam_rbgh -parallel > log 2>&1 &
     ```

---

## 🔧 Geometry & Gap Configuration

The cylinder STL (`constant/triSurface/Cylinder.stl`) is defined with its center at the origin $(0, 0)$ with $R = 0.025\text{ m}$.  
The physical position in the mesh is controlled entirely via the `transform` block in `system/snappyHexMeshDict`:

```
Cylinder.stl
{
    type triSurfaceMesh;
    name cylinder;
    transform
    {
        translateVector (0 0.010 0);
    }
}
```

To change the gap $e$, only update the `translateVector` y-component:

$$y_{\text{translate}} = y_{\text{bed}} + R + e = -0.025 + 0.025 + e = e$$

So `translateVector y = e` directly. Also update the `surface1` near-cylinder refinement box `min`/`max` y-bounds to follow the new cylinder position.

---

## 📊 Extraction & Validation Scripts

This directory includes custom Python scripts to post-process the OpenFOAM data and validate the results against literature:

*   **`extract_scour_and_validate.py`**:
    *   Reads the `alpha.a`/`alpha.b` sediment volume fractions and cell coordinates near the cylinder centerline ($x = 0.0\text{ m}$).
    *   Identifies the bed elevation $y_{bed}$ where the volume fraction reaches $\alpha_{thr} = 0.30$.
    *   Saves the scour history to `scour_St_D.csv`.
    *   Generates an interactive validation report `scour_validation.html` displaying the scour depth ratio $S(t)/D$ over dimensionless time $T^* = t \cdot U/D$, comparing it directly against experimental data from **Mao (1986)** and CFD simulations by **Larsen et al. (2016)**.
*   **`extract_openfoam_scour.py`**:
    *   Pulls physical, material, boundary forcing, solver, and grid parameter definitions from the case directory.
    *   Generates a comprehensive structured Excel spreadsheet (`scour_validation_data.xlsx` or fallback CSVs) containing all physical and numerical parameters used in the case.

---

