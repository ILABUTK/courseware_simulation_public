# Ch. 12 — P02 (K) ★★ Debugging a Flawed Simulation

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 12

---

## Objective

Practice model verification by diagnosing and correcting deliberate bugs in a SimPy simulation. This problem uses a test-driven verification approach: write the tests first, then find the bugs.

## The Flawed Model

Below is a SimPy M/M/1 simulation that contains **three deliberate bugs**. Your task is to find and fix all three without being told what they are.

```python
import simpy
import numpy as np

def flawed_mm1(arrival_rate, service_rate, sim_time=50_000, seed=0):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    server = simpy.Resource(env, capacity=1)
    waits = []

    def customer():
        arrival = env.now
        with server.request() as req:
            yield req
            # Bug may be hiding here or nearby
            svc = rng.exponential(service_rate)   # Bug 1
            yield env.timeout(svc)
        waits.append(env.now - arrival)           # Bug 2: this records W, not Wq

    def arrivals():
        while True:
            iat = rng.exponential(arrival_rate)   # Bug 3
            yield env.timeout(iat)
            env.process(customer())

    env.process(arrivals())
    env.run(until=sim_time)
    return {'Wq': np.mean(waits), 'utilization': server.count / sim_time,
            'n_served': len(waits)}
```

## Tasks

1. **Write verification tests first**: Before looking for bugs, write five `pytest` unit tests that a *correct* M/M/1 simulation must pass. At minimum, include:
   - Stability check: when $\rho < 1$, throughput ≈ $\lambda$
   - Little's Law: $L \approx \lambda W$
   - Extreme case: when $\lambda \to 0$, $W_q \to 0$
   - Formula match: simulated $W_q$ within 5% of $1/(\mu - \lambda) - 1/\mu$
   - Utilization check: $\rho_{\text{sim}} \approx \lambda/\mu$

2. **Run the tests**: Apply your tests to `flawed_mm1` with $\lambda = 3$, $\mu = 4$. Which tests fail? What do the failures suggest about the nature of each bug?

3. **Find and fix all three bugs**: Identify each bug (line number, what it computes incorrectly, what it should compute). Write the corrected function `fixed_mm1`.

4. **Verify the fix**: Re-run all five tests on `fixed_mm1`. All must pass. Include the `pytest` output showing all tests green.

5. **Regression guard**: Add one additional test for each bug you found — a test that would have caught that bug if written before the bug was introduced. Explain why this test targets that specific failure mode.

## Submission

Submit a Python file or notebook with:
- The five original verification tests (with docstrings explaining what each tests and why)
- The analysis of which tests failed and what each failure implies
- The corrected `fixed_mm1` function with comments on each fix
- All six regression tests passing
