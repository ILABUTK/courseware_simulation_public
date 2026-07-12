# Ch. 7 — P03 (K) ★★ Verify M/M/1 in SimPy

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 7

---

## Objective

Implement an M/M/1 queue in SimPy and verify your simulation output against the analytical formulas from P01.

## Setup

Use the same parameters as P01: $\lambda = 6$/hour, $\mu = 8$/hour.

## Tasks

1. **Implement** a SimPy M/M/1 simulation function with the signature:
   ```python
   def run_mm1(arrival_rate, service_rate, sim_time, seed=None) -> dict:
       ...  # returns {"mean_wait_queue": ..., "utilization": ..., "n_customers": ...}
   ```

2. **Run** a single replication with `sim_time = 50_000` (time units = minutes).
   Compare your simulated $W_q$ to the theoretical value from P01.

3. **Run 30 replications** and compute a 95% confidence interval for $W_q$.
   Does the CI contain the theoretical $W_q$?

4. **Sweep** $\lambda$ from 1 to 7.5 (keeping $\mu = 8$) in steps of 0.5.
   For each $\lambda$, run 10 replications and record mean $W_q$.
   Plot simulated $W_q$ vs. $\rho = \lambda/\mu$, overlaying the theoretical curve.
   This is the "hockey stick" figure.

5. **Discuss**: At what $\rho$ does the simulation become unreliable (high variance)?
   Why?

## Submission

Submit a Jupyter notebook with:
- The SimPy model code (in a `.py` cell or imported from `simdes`)
- The 30-replication CI result and comparison to theory
- The hockey-stick plot (publication quality, color-blind-safe)
- A written discussion (≤ 200 words)
