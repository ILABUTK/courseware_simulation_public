# Ch. 2 — P02 (C) ★★ Jensen's Inequality and Variability

**Type**: Conceptual + Analytical | **Difficulty**: ★★ | **Chapter**: 2

---

A delivery service operates a single van making deliveries.
The dispatcher estimates the "typical" delivery time as 20 minutes
and plans routes assuming exactly 20 minutes per stop.

In reality, delivery times follow an Exponential distribution with mean 20 minutes.

**Tasks**

1. The M/D/1 formula for mean wait in queue is
   $W_q^{D} = \frac{\rho}{2(\mu - \lambda)}$
   and the M/M/1 formula is
   $W_q^{M} = \frac{\lambda}{\mu(\mu - \lambda)}$.

   Show algebraically that $W_q^{M} = 2 \times W_q^{D}$ for the same $(\lambda, \mu)$.
   Interpret: what does this say about the cost of variability?

2. The dispatcher assumes "deterministic 20-minute deliveries" and sets the schedule at
   $\lambda = 2$ deliveries/hour (van utilisation $\rho = 40/60 \approx 0.667$).
   Compute $W_q$ under:
   - The dispatcher's deterministic model (M/D/1)
   - The true exponential model (M/M/1)
   - What the dispatcher incorrectly believes (Wq = 0, since ρ < 1)

   Report all three values and the percentage error of each wrong model relative to M/M/1.

3. Suppose the service time distribution is Lognormal with the same mean (20 min)
   but standard deviation 30 min (higher variability).
   Using the Pollaczek-Khinchine formula:
   $W_q = \frac{\lambda(\text{Var}[S] + (1/\mu)^2)}{2(1 - \rho)}$
   compute $W_q$ for this Lognormal scenario and compare it to M/M/1 and M/D/1.

4. Sketch (or compute and plot) the function $f(\sigma_S) = W_q(\sigma_S)$
   for $\sigma_S \in [0, 40]$ min, holding $\lambda=2/\text{hr}$ and $\mu=3/\text{hr}$ fixed.
   At what $\sigma_S$ does $W_q$ double relative to the M/D/1 value?

5. Write 2–3 sentences explaining to the dispatcher why their planning assumption
   "average time in = correct model" leads to systematically wrong predictions.
   Reference Jensen's inequality.
