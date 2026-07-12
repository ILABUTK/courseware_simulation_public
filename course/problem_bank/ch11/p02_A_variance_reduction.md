# Ch. 11 — P02 (A) ★★ Antithetic Variates

**Type**: Analytical + Coding | **Difficulty**: ★★ | **Chapter**: 11

---

The antithetic variates method pairs each run with a "mirror" run using
$1 - U$ in place of $U$ for each uniform deviate.
For a monotone increasing estimator $g(U)$, this induces negative correlation
between paired runs and reduces variance:
$$\text{Var}\!\left(\frac{g(U) + g(1-U)}{2}\right) = \frac{\text{Var}[g(U)] + \text{Cov}[g(U), g(1-U)]}{2}$$

**Tasks**

1. **Analytical example**: Let $U \sim \text{Uniform}(0,1)$ and $g(U) = U^2$.
   Compute:
   (a) $E[g(U)] = E[U^2]$
   (b) $\text{Var}[g(U)]$
   (c) $\text{Cov}[g(U), g(1-U)]$
   (d) $\text{Var}[(g(U) + g(1-U))/2]$
   
   What is the variance reduction ratio compared to using $n$ independent runs?

2. **Exponential service times**: For an M/M/1 queue, service times use the inverse CDF:
   $S = -\frac{1}{\mu}\ln(U)$.
   Show that $S' = -\frac{1}{\mu}\ln(1-U)$ is also Exponential($\mu$).
   Does this guarantee negative correlation between $W_q(S)$ and $W_q(S')$?
   Under what conditions on the queueing model is the answer yes?

3. **Coding**: Implement an M/M/1 simulation (λ=0.7, μ=1.0, 1000 customers) that:
   (a) Runs $n=20$ independent replications
   (b) Runs $n=10$ antithetic pairs (20 runs total, paired)
   
   Report the standard error of $\hat{W}_q$ under each approach.
   Compute the variance reduction ratio.

4. **Limitation**: Antithetic variates require $g$ to be monotone in the input uniforms
   to guarantee a variance reduction. Describe a queueing scenario where this
   monotonicity breaks down (hint: consider priority queues or finite buffers).
