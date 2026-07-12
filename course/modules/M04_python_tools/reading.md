# M04 Reading Guide

**Module**: M04 — Python Tools for Simulation

## Required Reading

1. Book Chapter 6: *Python Tools for Simulation*
2. SimPy documentation — "SimPy in 10 Minutes" and "Core Concepts" (processes, resources, environments)

## Recommended External Reading

1. SimPy documentation, "Resource" — covers `Resource`, `PriorityResource`, `PreemptiveResource`, and `Container`; required background for M05 and M06
2. NumPy documentation, "Random sampling (numpy.random)" — `default_rng` and the Generator API; this is the style used throughout all notebooks
3. McKinney (2022), *Python for Data Analysis*, Chapter 4 — NumPy fundamentals; read if you need a refresher on array operations and broadcasting

## Before Class

Be prepared to answer:
- What is a SimPy `Process` and how does `yield env.timeout()` relate to the simulation clock?
- Why do we pass a random seed to the model constructor rather than setting a global seed?
- What does `rng = np.random.default_rng(seed)` give you that `np.random.seed()` does not?

## After Class

Run the `L10_simpy_intro.ipynb` notebook and modify the inter-arrival and service time distributions from exponential to something else (triangular, lognormal, or uniform). Observe how the output changes. This prepares you for M05's comparison of analytical results to simulation.
