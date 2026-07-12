# Ch. 8 — P01 (T) ★ (s, S) Inventory Manual Trace

**Type**: Trace | **Difficulty**: ★ | **Chapter**: 8

---

A warehouse uses an $(s, S) = (5, 20)$ continuous-review inventory policy.
The initial inventory level is 20 units.
Orders are received instantaneously (zero lead time).
Use the demand events below:

| Event # | Time | Demand (units) |
|---|---|---|
| 1 | 2 | 4 |
| 2 | 5 | 3 |
| 3 | 9 | 5 |
| 4 | 11 | 2 |
| 5 | 14 | 6 |
| 6 | 18 | 4 |
| 7 | 21 | 3 |
| 8 | 24 | 5 |

**Tasks**:

1. Complete the trace table. For each event, record:
   - Time
   - Demand
   - Inventory *before* demand
   - Inventory *after* demand
   - Was an order placed? (Yes/No)
   - Inventory *after* receiving order (if applicable)

2. Draw the inventory-over-time sawtooth plot (hand-sketch acceptable).

3. Compute the **time-average inventory level** over [0, 24].

4. Identify all time intervals when a **stockout** (inventory ≤ 0) would have occurred if the policy had been $(s, S) = (3, 15)$ instead.

5. What is the total number of orders placed under the $(5, 20)$ policy during [0, 24]?
