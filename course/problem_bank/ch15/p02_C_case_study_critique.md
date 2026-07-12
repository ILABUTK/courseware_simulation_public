# Problem 15.2 — Critical Analysis of a Published Simulation Case Study

**Chapter**: 15 — Case Studies and Digital Twins  
**Type**: C (Conceptual)  
**Difficulty**: ★★

---

## Background

Reading simulation case studies critically is a core professional skill.
A published study may have excellent methodology but poor communication, or vice versa.
The Sargent V&V framework gives a structured lens for critique.

---

## Case Study Summary (Fictional)

The following is a summary of a fictional simulation study.
Read it carefully, then answer the questions below.

---

> **"Optimizing Ambulance Deployment in a Mid-Sized City"**
>
> *Study objective*: Determine the number and location of ambulances to minimise mean response time to 911 calls.
>
> *Model*: A discrete-event simulation model of the city's EMS system was built in a commercial package.
> Call arrivals were modelled as a homogeneous Poisson process at rate 12 calls/hr.
> Travel times were drawn from a uniform distribution [3, 15] minutes based on "analyst experience."
> Ambulance service times (on-scene + transport + turnaround) were fixed at 45 minutes.
>
> *Validation*: The model was "run until results stabilised" (no warmup analysis reported).
> Output was compared to the vendor's benchmark database for "similar cities" — not to actual city data.
>
> *Results*: With 6 ambulances, mean response time was 8.2 minutes (no confidence interval reported).
> With 8 ambulances, mean response time was 5.7 minutes.
> The study recommends 8 ambulances for a \$1.2M annual cost increase.
>
> *Limitations section*: None.

---

## Questions

**(a) Conceptual validity issues**: Identify at least two assumptions in the conceptual model that are likely to be violated in a real EMS system. For each, explain the likely direction of bias (does it make performance look better or worse than reality?).

**(b) Verification gaps**: What verification evidence is missing from the report? List at least three checks that should have been performed and described. For each, state what a failure would have indicated.

**(c) Operational validity**: The validation used a vendor benchmark database rather than local historical data.
- Why is this a weaker form of validation than historical comparison?
- Under what circumstances (if any) would benchmark comparison be acceptable as the primary validation evidence?

**(d) Output analysis critique**: The report gives point estimates (8.2 min, 5.7 min) without confidence intervals.
- Construct a hypothetical scenario where the decision to add 2 ambulances would reverse if proper CIs were included.
- What information (standard deviations, number of replications) would you need to test whether the difference is statistically significant?

**(e) Limitations section**: Write a 3–5 bullet limitations section that should have appeared in this report. Follow the format from the course: state the limitation, its likely magnitude of impact, and the condition under which it matters most.

**(f) Recommendation**: Given the methodological gaps, would you use this study to justify the \$1.2M ambulance purchase? State your position clearly and explain what additional analysis you would require before making a recommendation to the city council.

---

## Notes

There is no single correct answer to parts (e) and (f) — your grade depends on the quality of reasoning, not the specific conclusion. Reference specific V&V concepts and output analysis methods from the course.
