# Ch. 7 — P02 (A) ★★ M/M/c and the Erlang-C Formula

**Type**: Analytical | **Difficulty**: ★★ | **Chapter**: 7

---

A hospital emergency department triage station receives patients at a rate of $\lambda = 12$ patients/hour following a Poisson process. Each triage nurse can assess a patient in an exponentially distributed time with mean $1/\mu = 10$ minutes ($\mu = 6$/hour).

**Tasks**:

1. **M/M/1 baseline**: Suppose $c = 1$ nurse is on duty. Is the system stable? Compute $\rho$, $W_q$ (minutes), and $L_q$.

2. **M/M/c with $c = 2$**: Compute the offered load $a = \lambda/\mu$ and traffic intensity $\rho = \lambda/(c\mu)$. Using the Erlang-C formula:
   $$C(c, a) = \frac{\frac{a^c}{c!} \cdot \frac{1}{1-\rho}}{\sum_{n=0}^{c-1} \frac{a^n}{n!} + \frac{a^c}{c!} \cdot \frac{1}{1-\rho}}$$
   compute $C(2, 2)$ — the probability that an arriving patient must wait. Then compute $W_q$ and $L_q$.

3. **M/M/c with $c = 3$**: Repeat Task 2 for $c = 3$ nurses.

4. **Comparison table**: Summarize $\rho$, $C(c, a)$, $W_q$ (min), and $L_q$ for $c \in \{1, 2, 3\}$ in a single table.

5. **Throughput check**: Using Little's Law ($L = \lambda W$), verify your $L$ values for $c = 2$ and $c = 3$.

6. **Staffing decision**: The department's service standard is $W_q \leq 3$ minutes. What is the minimum number of nurses needed to meet this standard? Justify using your computed values.

*Express $W_q$ in minutes and all other quantities to three significant figures.*
