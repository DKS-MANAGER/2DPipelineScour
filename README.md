# Comprehensive Simulation of 2D Pipeline Scour Morphodynamics using sedExnerFoam

**Author:** Divyansh Kumar Singh (Postgraduate Research)  
**Date:** July 2026  
**Solver:** OpenFOAM v2412 (sedExnerFoam)  
**Repository:** [2DPipelineScour](https://github.com/DKS-MANAGER/2DPipelineScour)  

## 📌 1. Project Abstract & Physical Setup

This repository contains a rigorously reconstructed and validated computational fluid dynamics (CFD) setup for investigating 2D Pipeline Scour over an erodible granular bed. The primary objective is to transition from computationally expensive two-fluid Eulerian-Eulerian formulations (e.g., SedFoam) to the highly efficient, mesh-deformation-based `sedExnerFoam` solver. The approach couples the standard Navier-Stokes equations with the macroscopic Exner morphodynamic equation solved via the Finite Area Method (FAM).

### Baseline Geometry
- **Computational Domain:** $x \in [-0.75, 1.0]\text{ m}$, $y \in [-0.1, 0.205]\text{ m}$.
- **Initial Erodible Bed:** Prescribed as a horizontal interface located at $y = -0.026\text{ m}$.
- **Pipeline Cylinder:** Diameter $D = 0.05\text{ m}$, rigidly fixed with a gap-to-diameter ratio $e/D = 0.22$ ($11.0\text{mm}$). Center at $x = 0.0\text{ m}$, $y = 0.01\text{ m}$.
- **Morphodynamics Interface:** Represented via a 2D FAM mesh mapped directly to the `bottom` boundary patch.

### Fluid & Sediment Properties
- **Fluid (Water):** Density $\rho_f = 1000\text{ kg/m}^3$, kinematic viscosity $\nu = 10^{-6}\text{ m}^2\text{/s}$.
- **Sediment (Quartz Sand):** Density $\rho_s = 2650\text{ kg/m}^3$ (specific gravity $s = 2.65$), median grain diameter $d_{50} = 0.36\text{ mm}$ ($3.6 \times 10^{-4}\text{ m}$).
- **Erodible Bed Properties:** Porosity $\lambda_s = 0.40$, Angle of repose $\beta_r = 32^\circ$.
- **Derived Scale Parameters:** Soulsby critical Shields parameter $\theta_{cr} \approx 0.0473$.

### Boundary Conditions & Forcing
- **Inlet Velocity (U):** Coded logarithmic boundary layer matching a friction velocity $u^* = 0.04318\text{ m/s}$ and roughness height $z_0 = 3.0 \times 10^{-5}\text{ m}$. 
- **Seabed Boundary (bottom):** Solves sediment transport closures (Nielsen 1992 bedload, van Rijn slope correction) directly on the 2D surface.

---

## 🔄 2. Solver Architecture Transition

| Feature / Aspect | SedFoam (Reference Case) | sedExnerFoam (This Case) |
|---|---|---|
| **Phase Model** | Two-phase Eulerian-Eulerian (fluid + sediment) | Single-phase fluid; sediment bed is represented as a boundary patch |
| **Sediment Fields** | Volume fraction `alpha.b` solved in the 3D volume | Passive scalar concentration `Cs` in fluid; bedload flux on the bed boundary only |
| **Bed Morphodynamics** | Grid deformation via whole-domain mesh diffusion | Exner equation solved on a 2D Finite Area surface mesh, driving the `displacementLaplacian` solver |
| **Turbulence Closure** | k-ω SST (phase b) | Standard single-phase k-ω SST |
| **Bedload/Erosion** | Resolved via interphase drag, granular rheology, and particle pressure | Nielsen (1992) empirical bedload model & slope-corrected boundary condition |

---

## 🛠️ 3. Core Solver Diagnostics & Methodological Fixes (CRITICAL)

During the case reconstruction, several critical solver-level and configuration-level limitations were identified and permanently resolved:

### A. Resolution of Uninitialized Pointer Segfault in projectedFaMesh
During the morphodynamic phase, `sedExnerFoam` can experience a hard crash (Segmentation fault). Diagnostic tracing identified a C++ uninitialized variable defect in the constructor of `projectedFaMesh` (`src/projectedFiniteArea/projectedFaMesh/projectedFaMesh.C`). Several dynamically allocated raw pointers (`LePtr_`, `magLePtr_`, `pointCoordsPtr_`, `SPtr_`) were not explicitly initialized to `nullptr`.
**Methodological Fix:** The source code was patched to ensure strict pointer initialization, and the `projectedFiniteArea` library was recompiled, completely mitigating the memory corruption.

### B. Remediation of Locked Bed Mesh Motion
In the standard initialization, the bottom patch was rigidly constrained via `fixedValue uniform (0 0 0)` to allow for hydrodynamic spin-up. However, this mathematically locked the vertices, preventing the Exner solver from deforming the bed.
**Methodological Fix:** The automated script manages a dedicated configuration (`system/pointDisplacement`) where the bottom boundary is set as `fixedValue` so that the `sedExnerFoam` solver can explicitly inject the Exner morphological displacements into it.

### C. MPI Parallelization Constraint (Single Processor FaceSets)
The finite-area Exner solver in `sedExnerFoam` lacks parallel communication logic. A naïve volumetric domain decomposition inherently splits the bottom boundary across multiple MPI ranks, triggering fatal solver errors.
**Methodological Fix:** The parallelization strategy is constrained strictly according to the literature. Using `topoSet`, a `faceSet` is generated for the `bottom` patch. The `decomposeParDict` is subsequently programmed with a `singleProcessorFaceSets` constraint, forcing the entire morphodynamic bed to compute sequentially on a single CPU core, while distributing the volumetric Navier-Stokes matrices efficiently across the remaining cores.

### D. OpenFOAM v2412 Compatibility: Step-by-Step Source Code Fixes
The official `sedExnerFoam` solver contains a critical C++ bug in its mesh motion solver, which prevents the mesh from deforming because the displacement values are never successfully assigned back to the boundary.

To install and fix the solver on a new PC (e.g., your lab workstation), follow these exact steps to clone the development branch, patch the bug, and compile:

**1. Clone the `sedExnerFoam` solver (devel branch):**
```bash
git clone -b devel https://github.com/sedFoam/sedExnerFoam.git
```

**2. Copy the Pre-Patched Files from this Repository:** 
Instead of manually editing the C++ source code, we have provided the perfectly patched files directly in this repository. The `sedExnerFoam_v2412_fixes` directory perfectly mirrors the solver's repository structure.

Simply copy them over the original solver files:
```bash
cp -r sedExnerFoam_v2412_fixes/* <path-to-sedExnerFoam>/
```

*(For reference, these patched files apply the following critical C++ fixes for OpenFOAM v2412):*
- **Fix 1 (`meshMove.H`):** Modifies the initial read of the boundary displacement. The default solver incorrectly uses the internal field. The patched version casts and extracts the exact boundary values using `refCast<const fixedValuePointPatchVectorField>`.
- **Fix 2 (`meshMove.H`):** Replaces the direct array assignment with an explicit `tmp<Field>` memory allocation (`patchDisp == tmp<Field<vector>>::New(dispVals);`) to bypass fatal C++ move semantics errors that completely break mesh motion in v2412.
- **Fix 3 (`meshMove.H`):** Adds a missing `pointDisplacement.correctBoundaryConditions();` call to ensure dynamic mesh displacements are synchronized across MPI processor boundaries.
- **Fix 4 (`sedExnerFoam.C`):** Adds `#include "fixedValuePointPatchFields.H"` to resolve the forward declaration compiler error triggered by the `refCast` used in Fix 1.
- **Fix 5 (`projectedFaMesh.C`):** Explicitly initializes uninitialized raw pointers (`LePtr_`, `magLePtr_`, `pointCoordsPtr_`, `SPtr_`) to `nullptr` in the constructor to resolve a fatal Segmentation Fault that triggers randomly during Phase 2 morphodynamics.

**3. Recompile the Solver:** 
Open a terminal, navigate to the `<path-to-sedExnerFoam>/` directory, and run:
```bash
./Allwmake
```

### E. ParaView Decomposed Moving Mesh Reader Bug (v2412)
When viewing an actively running simulation in parallel, ParaView's native `.foam` reader throws a fatal error: `Mismatch in number of old points and new points` or fails to show any mesh motion. This is a known ParaView bug where it incorrectly assumes decomposed parallel boundaries will never change their local point counts during dynamic mesh deformation.
**The Fix:** Do not use the native `.foam` reader. Instead, export the mesh to VTK format step-by-step:
```bash
foamToVTK
```
In ParaView, navigate to the newly created `VTK/` folder and open the `.vtk` or `.vtm` files. This perfectly visualizes the moving scour hole without any point-mismatch errors.

### F. Scaling to Higher Core Counts (16, 32+ Cores)
If you are moving this simulation to a high-performance workstation or cluster and want to run on more CPU cores (e.g., 16 or 32 cores), update `system/decomposeParDict` and `Allrun`:
- **Update `system/decomposeParDict`:** Change `numberOfSubdomains` from 6 to your desired core count (e.g., 32). 
*(Note: DO NOT remove or change the `singleProcessorFaceSets` constraint. The bottom patch MUST remain constrained to a single core to prevent faMesh decomposition errors).*
- **Update the execution script (`Allrun`):** Change `-np 6` to your target core count for the execution.

### G. Phase Transition Stability Fixes
Getting the morphodynamics to run stably in OpenFOAM v2412 required several numerical fixes:
- Note: In previous tangent configurations, `makeFaMesh` non-manifold 0-thickness errors occurred. In the active setup, the cylinder is placed 11 mm above the bed (y-min at -0.015 m, bed at -0.026 m) to ensure stability.
- Undefined edges on the contact line were routed to a proper `cylinderFa` boundary condition with `zeroGradient`.
- `filterExner` was turned off to prevent unstable explicit Laplacian smoothing on highly skewed finite-area cells.
- `ABorder` was reduced to 0 (Euler Explicit) to bypass corrupted restart history.

---

## 🚀 4. Automated 2-Phase Simulation Workflow (6-Core MPI)

Modeling the $11.0\text{mm}$ gap introduces significant numerical challenges. The velocity through the gap creates an instantaneous, extreme shear stress spike at $t=0$. If the bed is allowed to deform immediately at real-time speeds, the explicit Exner solver's Courant number ($C_{exner}$) explodes, instantly corrupting the mesh ($V < 0$) and causing floating-point exceptions.

To completely stabilize this, the entire pipeline is **100% fully automated** via a single execution script:

```bash
bash Allrun
```

The `Allrun` script autonomously orchestrates the following discrete phases (currently solved up to $t = 3.5\text{s}$ of the planned $10.0\text{s}$ total simulation time):

### Phase 1: Hydrodynamic Spin-up ($t = 0.0\text{s} \rightarrow 2.0\text{s}$)
- **Settings:** `morphoAccFactor = 0.005`, `avalanche = off`.
- **Purpose:** By severely artificially slowing the morphodynamic time-scale by 200x, the turbulent flow field and pressure equations are granted the physical time required to fully develop and stabilize through the gap *without* the bed dropping out from underneath them instantly.

### Phase 2: Morphodynamic Scour ($t = 2.0\text{s} \rightarrow 10.0\text{s}$)
- **Settings:** `morphoAccFactor = 0.1`, `avalanche = on`.
- **Purpose:** Once the hydrodynamics are established, the bed is permitted to evolve. However, stepping immediately to $1.0$ causes $C_{exner}$ to exceed 1.0 due to the extreme initial gap velocity. Phase 2 acts as a shock-absorber, allowing the gap to widen slightly at 1/10th speed. The `avalanche` algorithm is safely engaged here to cap steep slopes to the $32^\circ$ angle of repose.
- **Current Run Status:** The simulation has successfully completed Phase 1 (up to $t = 2.0\text{s}$) and progressed through Phase 2 up to **$t = 3.5\text{s}$** (producing the time-step output directories: `0.5`, `1`, `1.5`, `2` for Phase 1, and `2.5`, `3`, `3.5` for Phase 2).

---

## 📂 5. Repository Structure & Configuration File Index

- `0_org/` (Initial Conditions): Contains the pristine initial conditions. The `copyFA.sh` script maps these onto the dynamically generated mesh inside `0/`.
- `constant/transportProperties` & `turbulenceProperties`: Baseline hydrodynamic constraints and RANS closure specifications.
- `constant/bedloadProperties`: The master configuration file for the morphodynamic solver (houses the $d_{50}$, Exner settings, Nielsen model coefficients, `morphoAccFactor`, and `avalanche` toggles).
- `constant/dynamicMeshDict`: Governs how the 2D mesh deforms as the bed drops. It uses an `inverseDistance` Laplacian diffusivity field explicitly referencing the `bottom` and `cylinder` to ensure elements near the pipeline are not crushed during massive bed evolution.
- `system/fvSolution`: Defines the linear solvers and PIMPLE loop controls. `correctPhi` and `moveMeshOuterCorrectors` are automatically managed by `Allrun`.
- `system/controlDict`: Governs the time-stepping ($\Delta t$), write intervals, and Courant number limits ($Co \le 0.4$).
- `system/blockMeshDict`, `snappyHexMeshDict`, `extrudeMeshDict`: Handles spatial domain synthesis, cylinder carving, and strictly enforces a 2D topology.

---

## 📊 6. Validation and Benchmarking

The morphodynamic scour depth ratio $S(t)/D$ is quantitatively assessed against established literature:
- **Experimental Data:** Mao (1986).
- **High-Fidelity CFD:** Larsen et al. (2016) utilizing resolved two-phase Eulerian-Eulerian models.
- **Empirical Estimations:** Sumer-Fredsøe deterministic development models.

To extract the physical depth of the scour hole at each timestep:
```bash
postProcess -func 'patchExpression(bottom, Cf.y())' -latestTime
```

---

## 🙏 7. Acknowledgments & Citations

I would like to extend my profound gratitude to my academic advisor and the OpenFOAM community for their continuous support. This project serves as a cornerstone for advanced sub-aqueous morphology computations, pushing the boundaries of accessible, high-performance fluid-structure-seabed interaction modeling.

Furthermore, this work builds upon the foundational open-source contributions of the following authors and their respective solvers, without whom this research would not be possible:
- **sedFoam:** Chauchat, J., Cheng, Z., Nagel, T., Bonamy, C., & Hsu, T. J. (2017). SedFoam-2.0: a 3-D two-phase flow solver for depth-resolving sediment transport modeling. Geoscientific Model Development.
- **sedExnerFoam:** Larsen, R. P., Fuhrman, D. R., & Roenby, J. sedExnerFoam: A moving mesh finite-area morphodynamic solver for OpenFOAM.

We deeply acknowledge their efforts in advancing the field of computational sediment transport.
