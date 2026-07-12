# Ch. 8 — P02 (K) ★★ SimPy (s, S) Inventory Model

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 8

---

## Objective

Implement a SimPy (s,S) inventory model and analyze cost-optimal policy parameters.

## System Description

- Demand arrives as a Poisson process with rate $\lambda_d = 3$ units/day.
- Each demand has size Exponential(mean=2 units).
- Replenishment lead time: Exponential(mean=2 days).
- Holding cost: $h = \$1$ per unit per day.
- Backorder cost: $b = \$8$ per unit per day.
- Capacity: $S \leq 60$ units.

## Tasks

1. **Implement** the `SSInventory` class (or use `simdes.models.inventory.SSInventory`).
   Run a single 1,000-day replication with $(s, S) = (10, 40)$ and report:
   - Average inventory level
   - Average backorder level
   - Average total cost per day

2. **Sweep** the reorder point $s \in \{5, 8, 10, 12, 15\}$ with $S = 40$ fixed.
   Run 20 replications per configuration.
   Plot mean total cost vs. $s$ with 95% CIs.

3. **2D sweep**: For $s \in \{5, 10, 15\}$ and $S \in \{25, 35, 45\}$, run 15 reps each.
   Present results in a table and identify the (s, S) pair with lowest mean cost.

4. **Discuss**: Why does increasing $s$ (while holding $S$ fixed) reduce backorder cost
   but increase holding cost?  Is there a unique optimal $s^*$?

## Submission

Jupyter notebook with model code, sweep plots, results table, and ≤ 300-word discussion.
