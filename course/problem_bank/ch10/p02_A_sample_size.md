# Ch. 10 — P02 (A) ★★ Sample Size and Confidence Interval Width

**Type**: Analytical | **Difficulty**: ★★ | **Chapter**: 10

---

A pilot study of $n_0 = 10$ replications of a SimPy simulation yields:
$$\bar{X} = 14.7 \text{ min}, \quad s = 3.2 \text{ min}$$

**Tasks**

1. Compute the 95% confidence interval for the true mean.
   Use the $t$-distribution with $n_0 - 1 = 9$ degrees of freedom.
   Report the half-width $h$.

2. **Sequential planning**: The analyst wants a half-width of $h^* = 0.5$ minutes.
   Using the formula:
   $$n^* = \left\lceil \left(\frac{t_{9,\,0.025} \cdot s}{h^*}\right)^2 \right\rceil$$
   compute $n^*$.
   
   The analyst is surprised by how large $n^*$ is. Explain why small $h^*$ requires
   disproportionately more replications (reference the $h \propto 1/\sqrt{n}$ relationship).

3. **Run the second stage**: Suppose after running $n^*$ replications, the analyst obtains:
   $\bar{X} = 15.1$ min, $s = 3.0$ min.
   Compute the new 95% CI. Does the achieved half-width meet the target?
   What if the true mean is 15.5 min — is the true value covered?

4. **Cost tradeoff**: Each replication costs 2 minutes of compute time.
   Complete the table below and recommend the most cost-effective sample size
   that keeps $h \leq 1.0$ min:

   | $n$ | $h$ (min) | Total cost (min) |
   |:---:|:---:|:---:|
   | 10 | | |
   | 20 | | |
   | 30 | | |
   | 50 | | |
   | 100 | | |

   Use $s = 3.2$ throughout (conservative estimate from pilot).

5. A colleague argues: "Instead of 50 replications of 500 customers,
   run 1 replication of 25,000 customers — it's the same sample size."
   Identify the two key reasons this is not equivalent.
