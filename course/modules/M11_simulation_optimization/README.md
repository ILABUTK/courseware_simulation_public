# Module M11 — Simulation Optimization

**Book chapters**: Ch. 13 (Simulation Optimization)
**Lectures**: L37–L38 | **Tier**: Advanced

## Learning Objectives
1. Explain the challenge of optimizing over a noisy simulation response surface.
2. Evaluate candidate policies with replication-based simulation output analysis.
3. Fit a simple surrogate or metamodel to simulation output.
4. Interpret optimization results with appropriate caution about noise and search budget.

## Contents
| Item | File |
|---|---|
| Slides | `slides/L37_simopt.tex`, `slides/L38_kriging_surrogate.tex` |
| Notebooks | `notebooks/L37_simopt.ipynb`, `notebooks/L38_kriging_surrogate.ipynb` |
| Final project option | `assignment/final_project_simopt_option.md` |
| Reading | `reading.md` |

## Notes
- The notebooks use the current public `simdes` inventory model and stay within the repo's installed dependencies.
- The surrogate notebook uses a quadratic response surface by default and includes a Gaussian-process extension only if `scikit-learn` is available locally.
