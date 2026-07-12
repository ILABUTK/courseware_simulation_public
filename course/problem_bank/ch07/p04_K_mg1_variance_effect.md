# Ch. 7 — P04 (K) ★★ M/G/1 and the Effect of Service-Time Variance

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 7

---

## Objective

Demonstrate empirically that the mean waiting time in an M/G/1 queue depends on the *variance* of service time — not just its mean — and verify the Pollaczek-Khinchine (P-K) formula against SimPy simulation.

## Background

The P-K mean waiting-time formula for an M/G/1 queue is:

$$W_q = \frac{\lambda \, \mathbb{E}[S^2]}{2(1-\rho)}$$

where $\rho = \lambda / \mu$, $\mathbb{E}[S]= 1/\mu$, and $\mathbb{E}[S^2] = \text{Var}(S) + (1/\mu)^2$.

## Setup

Fix $\lambda = 3$/hour and $\mu = 4$/hour ($\rho = 0.75$). Consider four service-time distributions, each with the same mean $1/\mu = 0.25$ hr but different variance:

| Distribution | Parameters | $\text{Var}(S)$ | $c_s^2 = \mu^2 \text{Var}(S)$ |
|---|---|---|---|
| Deterministic (D) | constant = 0.25 hr | 0 | 0 |
| Erlang-2 (E₂) | shape=2, rate=8/hr | $1/(2 \cdot 16)$ | 0.5 |
| Exponential (M) | rate=4/hr | $1/16$ | 1.0 |
| Hyperexponential | see below | — | 2.0 |

For the hyperexponential: with probability 0.5 draw from Exp(rate=2/hr); with probability 0.5 draw from Exp(rate=6/hr). Verify that this gives mean 0.25 hr and $c_s^2 = 2$.

## Tasks

1. **Compute** the theoretical $W_q$ for each distribution using the P-K formula.

2. **Implement** a general M/G/1 SimPy simulation:
   ```python
   def mg1_sim(arrival_rate, service_time_fn, sim_time=500_000, seed=0) -> dict:
       ...  # service_time_fn(rng) -> float
   ```

3. **Run** 20 replications for each distribution and compute 95% CIs for $W_q$.

4. **Plot** simulated $W_q$ (with error bars) and theoretical P-K $W_q$ on a single bar chart, grouped by distribution. Use a color-blind-safe palette.

5. **Sensitivity sweep**: Fix the exponential distribution ($c_s^2 = 1$) and vary $\rho$ from 0.1 to 0.95 in steps of 0.05. For each $\rho$, compute theoretical P-K $W_q$ and simulate (10 reps each). Plot both curves on the same axes. At what $\rho$ does simulation variance become so large that the CI no longer contains the theoretical value?

## Submission

Submit a Jupyter notebook with all code, the comparison plot, the sensitivity-sweep plot, and a written interpretation (≤ 150 words) of why variance matters more at high utilization.
