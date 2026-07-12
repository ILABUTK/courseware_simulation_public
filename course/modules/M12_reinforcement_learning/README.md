# Module M12 — Reinforcement Learning for Simulation Environments

**Book chapters**: Ch. 14 (RL), Appendix D (prerequisite)
**Lectures**: L39–L42 | **Tier**: Advanced

## Learning Objectives
1. Formulate a SimPy model as a Markov Decision Process.
2. Wrap a SimPy simulation as a Gymnasium-compatible environment.
3. Implement tabular Q-learning on a small discrete state/action space.
4. Train a deep RL agent on a teaching environment when optional RL dependencies are installed.
5. Evaluate an RL policy against rule-based baselines and explain current modeling limits.

## Contents
| Item | File |
|---|---|
| Slides | `slides/L39_mdp_framing.tex`, `slides/L40_tabular_q_learning.tex`, `slides/L41_simpy_gym_wrapper.tex`, `slides/L42_deep_rl_training.tex` |
| Notebooks | `notebooks/L39_mdp_framing.ipynb`, `notebooks/L40_tabular_q_learning.ipynb`, `notebooks/L41_simpy_gym_wrapper.ipynb`, `notebooks/L42_deep_rl_training.ipynb` |
| Final project | `assignment/final_project_rl_option.md` |
| Reading | `reading.md` |

## Prerequisites
- Appendix D (Markov Chains and MDPs) — read before L39
- Module M08 (output analysis) — needed to evaluate RL policy performance

## Notes
- `L41` and `L42` are honest starter materials: they inspect the current `simdes` wrapper API and use a small teaching environment for runnable examples.
- A full ClinicEnv-based training notebook should follow after the package-level RL wrappers are completed beyond their current scaffold state.
