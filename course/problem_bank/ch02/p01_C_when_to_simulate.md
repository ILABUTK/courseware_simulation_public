# Ch. 2 — P01 (C) ★ When to Simulate

**Type**: Conceptual | **Difficulty**: ★ | **Chapter**: 2

---

For each system below, decide whether discrete-event simulation, an analytical model,
Monte Carlo (static) simulation, ODE/system-dynamics, or no model is most appropriate.
Classify each along the three axes: {Discrete, Continuous} × {Stochastic, Deterministic} × {Static, Dynamic}.

Justify each answer in 1–2 sentences.

1. A factory produces exactly 200 identical widgets per 8-hour shift.
   The manager wants to know the total output per week.

2. A hospital emergency department with 6 exam rooms, 3 triage nurses,
   and time-varying patient arrivals (high at noon, low at 3 AM).
   The administrator asks: "What is the 90th-percentile wait time?"

3. A financial analyst wants to estimate the probability that a stock portfolio
   loses more than 15% of its value in any given year, based on historical return data.

4. A water distribution network obeys Hazen-Williams flow equations.
   An engineer wants to find the pressure at each node.

5. An epidemiologist models flu spread through a city of 500,000 people
   using an SIR compartmental model (dS/dt = −βSI, etc.).

6. A call centre with 10 agents, Poisson arrivals at rate λ=20/hr,
   and exponential service times with mean 4 min.
   The manager asks: "What is the average queue length?"

7. A parking garage with 200 spaces and Poisson arrivals/departures.
   Drivers leave immediately if no space is available.
   What fraction of drivers are turned away?

8. A single machine processes jobs with exactly 15-minute setup time
   and exactly 30-minute processing time, one job at a time.
   What is the throughput per hour?
