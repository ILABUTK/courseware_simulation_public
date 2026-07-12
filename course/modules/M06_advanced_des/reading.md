# M06 Reading Guide

**Module**: M06 — Advanced DES Modeling

## Required Reading

1. Book Chapter 8: *Advanced DES Modeling*
2. SimPy documentation, "Events" — `Event`, `AnyOf`, `AllOf`, and the timeout-race pattern used for reneging
3. SimPy documentation, "Process Interaction" — `Process.interrupt()` for preemptive breakdowns

## Recommended External Reading

1. Kelton et al. (2015), *Simulation with Arena*, Chapter 9 — routing logic and advanced entity flow; the concepts translate directly to SimPy even if the notation differs
2. Zipkin (2000), *Foundations of Inventory Management*, Chapter 5 — (s, S) policy derivation and optimality conditions; read before L22 to understand what the grid search is actually searching for
3. Lewis and Shedler (1979), "Simulation of nonhomogeneous Poisson processes by thinning" — *Naval Research Logistics Quarterly* 26(3): 403–413; the original thinning algorithm paper (short and readable)

## Before Class

Be prepared to answer:
- What is the difference between preemptive and non-preemptive breakdown handling, and which leads to higher Wq?
- In the Lewis-Shedler thinning algorithm, why must λ* ≥ λ(t) for all t?
- For the (s, S) inventory policy: when is an order placed, and how large is it?

## After Class

Complete HW-04. If you chose the (s, S) model: plot your 30-replication cost distribution as a histogram and overlay the 95% CI. If you chose a queue extension: verify that your effective arrival rate (accounting for rework or routing) matches what you observe in the simulation throughput.
