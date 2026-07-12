# Ch. 6 — P01 (K) ★★ Implement M/M/c in SimPy

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 6

---

Implement an M/M/c queue in SimPy and verify it against the Erlang-C formula.

**System parameters**:
- Arrival rate: $\lambda = 12$ customers/hour
- Service rate per server: $\mu = 5$ customers/hour
- Number of servers: $c = 3$
- Run for 5,000 customers per replication; delete warmup of 500

**Tasks**

1. **Implement**: Write a SimPy model `MMcQueue` that accepts $\lambda$, $\mu$, $c$,
   `n_customers`, and `seed` as parameters.
   Use `simpy.Resource(env, capacity=c)`.
   Collect per-customer wait in queue $W_q$ and sojourn $W$.

2. **Run 30 replications** using `np.random.default_rng(seed).spawn(30)`.
   Compute $\hat{W}_q$ (mean across replications) and a 95% CI.

3. **Erlang-C theory**: Compute the theoretical $W_q$ using:
   $$C(c, \rho) = \frac{\frac{(c\rho)^c}{c!(1-\rho)} \cdot \frac{1}{c}}{\sum_{k=0}^{c-1} \frac{(c\rho)^k}{k!} + \frac{(c\rho)^c}{c!(1-\rho)}}$$
   $$W_q = \frac{C(c, \rho)}{\mu c - \lambda}$$
   where $\rho = \lambda/(c\mu)$.

   Implement `erlang_c_wq(lam, mu, c)` in Python and compute the theoretical value.

4. **Comparison**: Does the 95% CI from step 2 contain the theoretical value?
   Report the relative error $|\hat{W}_q - W_q^*| / W_q^*$.

5. **Sweep over c**: For $c \in \{2, 3, 4, 5\}$ and the same $\lambda$, $\mu$,
   compute both the simulated $\hat{W}_q$ (10 reps each) and the theoretical $W_q^*$.
   Plot both on the same axis (theory as a line, simulation as points with error bars).
   At what $c$ does $W_q$ first fall below 1 minute?
