# Problem 13.2 — Nelder-Mead on a Stochastic Response Surface

**Chapter**: 13 — Simulation Optimization  
**Type**: K (Coding)  
**Difficulty**: ★★★

---

## Background

Nelder-Mead (simplex search) is a derivative-free optimizer suitable when $g(x)$ is expensive to evaluate and gradients are unavailable or unreliable.
`scipy.optimize.minimize(..., method='Nelder-Mead')` wraps this algorithm.
When applied to a stochastic objective, each evaluation should use *multiple replications* to reduce noise.

---

## Setup

The following function represents the true (unknown) daily cost of an $(s, S)$ inventory policy as a function of the reorder point $s$ and order-up-to level $S$:

```python
import numpy as np
import simpy

def inventory_cost(params, n_reps=20, seed_base=0):
    """
    Simulate (s, S) inventory system and return mean daily cost.
    params = [s, S]  (will be rounded to nearest integer)
    """
    s_val = max(1, round(params[0]))
    S_val = max(s_val + 1, round(params[1]))
    costs = []
    for rep in range(n_reps):
        rng = np.random.default_rng(seed_base + rep)
        env = simpy.Environment()
        inventory = [S_val]
        daily_cost = []

        def run_inventory():
            while env.now < 365:
                # Daily demand ~ Poisson(10)
                demand = rng.poisson(10)
                inventory[0] = max(0, inventory[0] - demand)
                # Holding + shortage cost
                hold = 2.0 * max(0, inventory[0])
                short = 20.0 * max(0, demand - inventory[0])
                daily_cost.append(hold + short)
                # Order if below reorder point
                if inventory[0] <= s_val:
                    lead = rng.integers(1, 4)  # 1-3 day lead time
                    yield env.timeout(lead)
                    inventory[0] += S_val - inventory[0]
                else:
                    yield env.timeout(1)

        env.process(run_inventory())
        env.run()
        costs.append(np.mean(daily_cost))
    return np.mean(costs)
```

---

## Tasks

**(a)** Evaluate `inventory_cost([20, 80])` and `inventory_cost([40, 100])` with `n_reps=30`.
Report the mean and standard deviation across replications for each configuration.

**(b)** Apply `scipy.optimize.minimize` with `method='Nelder-Mead'` to minimize `inventory_cost` starting from $x_0 = [30, 90]$.
Use `n_reps=10` per evaluation during the search, then re-evaluate the reported optimum with `n_reps=50` for a more precise estimate.

```python
from scipy.optimize import minimize

result = minimize(
    lambda x: inventory_cost(x, n_reps=10, seed_base=42),
    x0=[30, 90],
    method='Nelder-Mead',
    options={'xatol': 1.0, 'fatol': 0.5, 'maxiter': 200}
)
print(result)
```

**(c)** Plot the optimizer's trajectory in $(s, S)$ space by logging each function evaluation.
Use `callback` or wrap the objective to append `(params, cost)` to a list. Scatter-plot the evaluations colored by call order.

**(d)** Nelder-Mead is sensitive to initialization. Run the optimizer from three different starting points:
- $x_0 = [10, 50]$, $[30, 90]$, $[60, 120]$

Do all three converge to the same $(s^*, S^*)$? Discuss what this reveals about the response surface.

**(e)** **Bias from noisy evaluations**: when `n_reps=10`, the objective is noisy.
Nelder-Mead may accept a move to a worse point if the noisy estimate looks better.
Propose one mitigation strategy (without switching algorithms) and implement it.

---

## Constraints

$1 \le s < S \le 200$, both integers.
Round non-integer suggestions from the optimizer before passing to the simulator.
