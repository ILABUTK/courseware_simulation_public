# Ch. 7 — P05 (D) ★★★ Clinic Staffing Design

**Type**: Design | **Difficulty**: ★★★ | **Chapter**: 7

---

## Scenario

A community health clinic sees walk-in patients during a 10-hour operating day (8 AM–6 PM). Patient arrivals follow a Poisson process at rate $\lambda = 18$/hour during peak hours (10 AM–2 PM) and $\lambda = 9$/hour during off-peak hours (8–10 AM, 2–6 PM). The clinic currently routes all patients through a single triage nurse, then to one of several exam rooms.

Triage service time is exponentially distributed with mean 5 minutes. Exam service time is lognormally distributed with mean 20 minutes and coefficient of variation $c_s = 0.8$.

The clinic's performance targets are:
- Mean triage wait $\leq$ 3 minutes at all hours
- Mean exam wait $\leq$ 10 minutes at all hours
- Nurse utilization $\leq$ 85% (to allow unscheduled breaks)

## Tasks

1. **Analytical feasibility**: Use the M/M/c Erlang-C formula to determine the minimum number of triage nurses needed during peak hours to satisfy both the wait target and the utilization cap. State all assumptions required to apply the formula.

2. **Simulation model design**: Write a conceptual model document (one page) for a SimPy simulation of this clinic. Include:
   - Entity types and their attributes
   - Resource list with capacity parameters (as design variables)
   - Event types
   - Performance measures to track
   - Key assumptions and their justification

3. **Implement and verify**: Implement the SimPy model (time unit = hours). Run 30 replications of a single operating day. Verify that your simulated mean triage wait matches the M/M/c formula (from Task 1) for the peak-hour staffing level. If they differ by more than 10%, identify the source of the discrepancy.

4. **Design alternatives**: Define and evaluate three staffing configurations that differ in the number of triage nurses and exam rooms. For each configuration, run 30 replications and report mean triage wait, mean exam wait, nurse utilization, and total daily cost (assume $\$60$/hr per nurse and $\$40$/hr per exam room).

5. **Recommendation**: Identify the configuration that meets all performance targets at minimum cost. Write a ≤ 200-word recommendation suitable for a clinic manager (no simulation jargon).

## Constraints

- You may use `simdes.models.queues` for the M/M/c formula and the SimPy model scaffold.
- The lognormal service time must be implemented directly (not approximated as exponential).
- Do not use steady-state formulas for the exam stage; simulation is required.
