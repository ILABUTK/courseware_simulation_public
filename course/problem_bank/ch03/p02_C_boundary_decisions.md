# Ch. 3 — P02 (C) ★ Model Boundary Decisions

**Type**: Conceptual | **Difficulty**: ★ | **Chapter**: 3

---

For each scenario below, a simulation analyst has made a boundary decision.
Evaluate whether the boundary is appropriate given the study question.
If the boundary is wrong, explain what is missing and what error it introduces.

1. **Study question**: "What is the mean patient wait in the ER?"
   **Boundary**: Patients arrive, wait for a bed, see a physician, and leave.
   Lab tests are treated as an instantaneous delay of fixed duration.
   **Omitted**: Lab processing time variability.
   
   Is this boundary appropriate? Under what conditions would omitting variability matter most?

2. **Study question**: "Does adding a second baggage carousel reduce passenger pickup wait?"
   **Boundary**: Passengers arrive at the carousel area after their flight lands,
   wait for their bag, and leave.
   **Omitted**: The flight landing process and the bag loading process.
   
   Evaluate this boundary. Is the omitted process relevant?

3. **Study question**: "How does a change in reorder policy affect inventory costs?"
   **Boundary**: Demand arrives, is filled from on-hand inventory, and backorders accumulate
   if stock-out occurs. Orders arrive after a lead time drawn from a distribution.
   **Omitted**: The supplier's production process.
   
   Is the supplier's process inside or outside the natural boundary for this question?

4. **Study question**: "How long does a patient spend in the hospital?"
   **Boundary**: Patient is admitted, assigned a bed, receives daily care,
   and is discharged when clinically ready.
   **Omitted**: Post-discharge home care and readmission within 30 days.
   
   Classify: is readmission a boundary decision or a simplifying assumption?
   What would you need to know to decide whether to include it?
