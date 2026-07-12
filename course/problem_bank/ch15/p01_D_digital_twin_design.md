# Problem 15.1 — Designing a Digital Twin for a Manufacturing Cell

**Chapter**: 15 — Case Studies and Digital Twins  
**Type**: D (Design)  
**Difficulty**: ★★★

---

## Background

A **digital twin** is a continuously updated simulation model that mirrors a physical system in near-real time.
Unlike a traditional simulation study (run once, report results), a digital twin ingests live sensor data, maintains current state, and can run ahead-of-time ("lookahead") to support operational decisions.

---

## Scenario

A precision machining cell consists of:
- 3 CNC machines (M1, M2, M3) arranged in series: all parts visit M1 → M2 → M3.
- Each machine has a probabilistic failure mode: MTTF ≈ 40 hr, MTTR ≈ 2 hr (both exponential).
- Processing times: M1 ~ LogNormal(μ=2.5, σ=0.3) min; M2 ~ Gamma(3, 1.2) min; M3 ~ Exponential(4.0) min.
- Arrival rate: 8 parts/hr (Poisson).
- Sensor data available: part completions at M1, M2, M3 (timestamped); machine state (idle/busy/down) at 1 Hz.

---

## Design Tasks

**(a) Architecture diagram**: Draw (sketch or describe) the data flow from physical sensors → state estimator → SimPy digital twin → decision dashboard. Identify: the data ingestion pipeline, the state synchronization module, the lookahead runner, and the output layer.

**(b) State synchronization**: When the physical cell sends a "M2 part-complete" event at timestamp $t_{\text{sensor}}$, how should the digital twin update?
List the SimPy objects that must be modified (queue lengths, resource states, environment clock) and describe a protocol for handling events that arrive out of order (e.g., a message delayed 500 ms).

**(c) Lookahead policy**: The twin runs 15-minute lookahead simulations on demand to answer: *"If M1 fails now, what is the expected throughput loss in the next 15 minutes?"*
Design the lookahead procedure:
- How do you snapshot the current twin state?
- How do you inject the hypothetical M1 failure?
- How many lookahead replications are needed for a 95% CI with half-width ≤ 1 part? (Use a pilot estimate: std dev of 15-min throughput ≈ 2.5 parts.)

**(d) Drift detection**: Over time, the real system may drift from the model (e.g., tools wear and increase processing time).
Propose a statistical test that the digital twin could run continuously to detect when model parameters have drifted significantly from observed data. Specify: the null hypothesis, the test statistic, the detection threshold, and what action to take upon detection.

**(e) Limitations**: State three inherent limitations of the digital twin approach that cannot be eliminated by better data or more compute. For each, describe its impact on decision quality.

---

## Deliverables

Write your answer as a structured design document with sections (a)–(e).  
Part (c) must include a numerical calculation for the required number of replications.  
Part (d) must name a specific statistical procedure (e.g., CUSUM, Kolmogorov-Smirnov, Welch's t-test) and justify the choice.
