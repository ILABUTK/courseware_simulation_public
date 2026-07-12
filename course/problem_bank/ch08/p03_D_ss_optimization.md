# Ch. 8 — P03 (D) ★★★ (s, S) Policy Optimization

**Type**: Design | **Difficulty**: ★★★ | **Chapter**: 8

---

## Scenario

A regional distribution center manages inventory for a single SKU under a continuous-review $(s, S)$ policy. Relevant data:

| Parameter | Value |
|---|---|
| Daily demand | Poisson with mean $\bar{d} = 8$ units/day |
| Lead time | Uniform[2, 5] days |
| Unit holding cost | $\$0.50$/unit/day |
| Fixed ordering cost | $\$100$ per order |
| Unit shortage cost | $\$5$/unit/day of shortage |
| Review period | Continuous |
| Simulation horizon | 365 days |

The current policy is $(s, S) = (20, 60)$.

## Tasks

1. **Baseline simulation**: Using `simdes.models.inventory.SSInventory` (or your own SimPy implementation), run 30 replications of the current $(20, 60)$ policy. Report the mean daily cost decomposed into holding, ordering, and shortage components, each with a 95% CI.

2. **Parameter sensitivity**: Fix $S = 60$ and vary $s \in \{5, 10, 15, 20, 25, 30\}$. For each value of $s$, run 20 replications and plot mean daily holding cost, ordering cost, and shortage cost on the same figure (three lines). Identify the tradeoff: as $s$ increases, which cost goes up and which goes down?

3. **Grid search**: Search over the parameter space $s \in \{10, 15, 20, 25, 30\}$ and $S \in \{40, 50, 60, 70, 80\}$ with the constraint $S > s + 10$. Use 30 replications per policy. Present results as a heatmap of mean daily total cost. Mark the empirically optimal policy with a star.

4. **Common Random Numbers**: Using CRN (same seed sequence for each replication), compare the best policy from Task 3 against the current $(20, 60)$ policy using 50 paired replications. Report the mean cost difference and its 95% CI. Is the difference statistically significant?

5. **Robustness check**: Re-run your optimal policy under two demand perturbations: (a) demand rate doubled ($\bar{d} = 16$) and (b) lead time extended (Uniform[4, 8] days). Does your policy remain near-optimal, or does it perform significantly worse? Recommend how to adjust $(s, S)$ for each perturbation.

6. **Reflection**: In 150 words or fewer, explain why the grid search is not a practical approach for a real distribution center that manages thousands of SKUs. What would you do instead? (This sets up Module M12.)

## Deliverables

- A Jupyter notebook with all simulation code, plots, and CRN comparison
- The heatmap from Task 3 (publication quality)
- A one-page management summary stating the recommended $(s, S)$ policy and expected cost savings versus the current policy
