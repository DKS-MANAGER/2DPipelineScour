# Comprehensive Simulation of 2D Pipeline Scour Morphodynamics using sedFoam

**Author:** Divyansh Kumar Singh (Postgraduate Research)  
**Date:** July 2026  
**Solver:** OpenFOAM (sedFoam_rbgh)  
**Repository:** [2DPipelineScour](https://github.com/DKS-MANAGER/2DPipelineScour)  

## 📌 1. Project Abstract & Physical Setup

This repository contains a rigorously reconstructed and validated computational fluid dynamics (CFD) setup for investigating 2D Pipeline Scour over an erodible granular bed. The setup utilizes the **sedFoam** suite, leveraging a fully resolved **Two-Phase Eulerian-Eulerian** (`sedFoam_rbgh`) formulation where both the fluid (water) and the sediment phases are computed over the entire volumetric domain.

### Baseline Geometry
- **Computational Domain:** $x \in [-0.75, 1.0]\text{ m}$, $y \in [-0.1, 0.205]\text{ m}$.
- **Initial Erodible Bed:** The sediment/water interface is prescribed at $y = -0.026\text{ m}$ (defined via `0_org/alpha.a`).
- **Pipeline Cylinder:** Diameter $D = 0.05\text{ m}$. The cylinder's center is shifted to $y = 0.01\text{ m}$ (bottom at $y = -0.015\text{ m}$).
- **Gap Size:** The combination of the interface and cylinder positioning perfectly enforces an $11.0\text{ mm}$ gap ratio ($e/D = 0.22$).

### Fluid & Sediment Properties
- **Fluid (Water, `alpha.a`):** Density $\rho_f = 1000\text{ kg/m}^3$, kinematic viscosity $\nu = 10^{-6}\text{ m}^2\text{/s}$.
- **Sediment (Quartz Sand, `alpha.b`):** Density $\rho_s = 2650\text{ kg/m}^3$, median grain diameter $d_{50} = 0.36\text{ mm}$.
- **Turbulence Closure:** Standard k-ω SST handles the turbulent interactions across the two-phase flow fields.

---

## 🚀 2. Automated Meshing & Execution Workflow (16-Core MPI)

The entire mesh generation, field initialization, and parallel execution pipeline are 100% automated via the `./Allrun` script. The workflow utilizes hardware threads to efficiently distribute the workload across 16 subdomains.

### Execution Steps in `Allrun`:
1. **Background Mesh (`blockMesh`):** Generates the fundamental Cartesian grid.
2. **2D Patch Fix (`sed`):** Temporarily renames `empty` patches to `emptyy` (acting as walls) so that `snappyHexMesh` correctly resolves the 2D plane.
3. **Parallel Meshing (`snappyHexMesh`):** The domain is decomposed (`decomposePar`) and `snappyHexMesh` aggressively refines the cylinder wake and gap region simultaneously across 16 cores. 
4. **Mesh Reconstruction (`reconstructParMesh`):** Merges the subdomains, after which the 2D hack is reverted.
5. **2D Enforcement (`extrudeMesh`):** The mesh is formally extruded by one cell layer to ensure a strict two-dimensional calculation.
6. **Initialization:** The pure initial conditions from `0_org` are copied to `0`.
7. **Parallel Solve (`sedFoam_rbgh`):** The case is decomposed again, and the solver runs on 16 hardware threads utilizing `mpirun --use-hwthread-cpus`.

To run the simulation from scratch:
```bash
./Allclean
./Allrun
```

---

## 📂 3. Repository Structure & Configuration File Index

- **`0_org/` (Initial Conditions):** Contains the pristine initial conditions. Specifically, `alpha.a` employs a `codeStream` that defines the exact $-0.026\text{ m}$ physical bed interface via a continuous `tanh` function.
- **`constant/`:**
  - `triSurface/Cylinder.stl`: The physical geometry of the pipeline, manually translated so its center rests at `y = 0.01\text{m}`.
  - `transportProperties`, `turbulenceProperties.*`: Two-phase hydrodynamic constraints and RANS closure specifications.
  - `granularRheologyProperties`: Resolves particle-particle friction and collision stresses inside the sediment bed.
- **`system/`:**
  - `snappyHexMeshDict`: Directs refinement boxes perfectly centered around the shifted cylinder to capture extreme shear stresses dynamically in the wake.
  - `decomposeParDict`: Controls the 16-core domain decomposition method (Scotch).

---

## 📊 4. Validation and Benchmarking

The morphodynamic scour depth ratio $S(t)/D$ is quantitatively assessed against established literature:
- **Experimental Data:** Mao (1986).
- **High-Fidelity CFD Benchmarks:** Comparisons to standard Eulerian-Eulerian literature (e.g., Larsen et al. 2016).

---

## 🙏 5. Acknowledgments & Citations

This project serves as a cornerstone for advanced sub-aqueous morphology computations, pushing the boundaries of two-phase fluid-structure-seabed interaction modeling. This work builds upon the foundational open-source contributions of:
- **sedFoam:** Chauchat, J., Cheng, Z., Nagel, T., Bonamy, C., & Hsu, T. J. (2017). SedFoam-2.0: a 3-D two-phase flow solver for depth-resolving sediment transport modeling. Geoscientific Model Development.

We deeply acknowledge their efforts in advancing the field of computational sediment transport.
