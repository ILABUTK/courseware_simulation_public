# Ch. 10 — P01 (A) ★★ Warmup Analysis

**Type**: Analytical | **Difficulty**: ★★ | **Chapter**: 10

---

A simulation analyst runs a single long replication of an M/M/1 queue
(λ=0.7, μ=1.0, ρ=0.7) for 10,000 customers starting empty.
They divide the run into batches of 100 customers and record the batch-mean
wait in queue $\bar{W}_q^{(b)}$ for batches $b=1,\ldots,100$.

The theoretical steady-state value is $W_q^* = \lambda/(\mu(\mu-\lambda)) = 7/3 \approx 2.333$ min.

The analyst observes that the first 20 batch means are systematically below $W_q^*$:

| Batch | $\bar{W}_q$ |
|:---:|:---:|
| 1 | 0.14 |
| 5 | 0.48 |
| 10 | 1.02 |
| 15 | 1.67 |
| 20 | 2.01 |
| 25 | 2.28 |
| 30 | 2.40 |

**Tasks**

1. Explain intuitively why $\bar{W}_q^{(1)} = 0.14$ is so far below $W_q^* = 2.33$
   when the system starts empty.

2. Apply Welch's moving average with window $w = 5$ to the table above
   (compute $\bar{Y}_5(b)$ for batches $b = 5 + 1, \ldots, 25$ using the data given,
   interpolating the missing batches linearly if necessary).
   At what batch does $\bar{Y}_5(b)$ first enter the band $[W_q^* \pm 10\%] = [2.10, 2.57]$?

3. The analyst computes the sample mean over:
   (a) All 10,000 customers: $\hat{W}_q = 2.08$
   (b) Customers 2001–10000 (warmup deleted): $\hat{W}_q = 2.31$
   
   Compute the absolute and percentage bias for each case.
   Which estimate is unbiased?

4. Suppose the analyst wanted to run independent replications instead of a single long run.
   With 30 replications of 1,000 customers each and warmup deletion of 200 per replication:
   (a) How many "effective" customers contribute to the estimate across all replications?
   (b) If the standard deviation across replications is $s = 0.42$, compute the 95% CI half-width.
   (c) Does the 95% CI contain $W_q^* = 2.333$?

5. What would happen to the warmup length if $\rho$ were increased from 0.7 to 0.95?
   Explain qualitatively (no calculation required).
