# Ch. 11 — P03 (A) ★★ 2² Factorial Effects

**Type**: Analytical | **Difficulty**: ★★ | **Chapter**: 11

---

A simulation experiment studies a call centre with two factors:
- **Factor A**: Number of agents (1 or 3)
- **Factor B**: Maximum queue length before balking (10 or 50)

Response: mean call wait time $W_q$ (minutes).
Each cell is the average of $r=10$ replications.

| | **B=10 (low)** | **B=50 (high)** |
|:---:|:---:|:---:|
| **A=1 (low)** | 8.4 | 12.1 |
| **A=3 (high)** | 1.6 | 2.8 |

**Tasks**

1. Compute the main effect of A (number of agents).
   Interpret: what does this tell you about the impact of adding agents?

2. Compute the main effect of B (queue length limit).
   Interpret: why does a longer queue (more balking room) increase $W_q$?

3. Compute the AB interaction.
   Draw an interaction plot.
   Are the effects additive? What does the interaction tell you about the system?

4. Fit the linear model:
   $$W_q = \mu + \alpha x_A + \beta x_B + \gamma x_A x_B$$
   where $x_A, x_B \in \{-1, +1\}$.
   Solve for $\hat{\mu}$, $\hat{\alpha}$, $\hat{\beta}$, $\hat{\gamma}$.

5. Use your model to predict $W_q$ at the centre point $(x_A, x_B) = (0, 0)$
   (i.e., 2 agents, queue limit = 30).
   What is the limitation of using a linear model to make this prediction?

6. If the call centre manager can implement only one change (either adding 2 agents
   OR increasing the queue limit from 10 to 50), which should they choose?
   Base your answer on the factorial effects.
