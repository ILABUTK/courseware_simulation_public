# Ch. 11 — P04 (K) ★★ Ranking and Selection Implementation

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 11

---

You are selecting the best staffing level (number of servers) for a two-stage
tandem manufacturing line. The alternatives are $k = 4$ configurations:
- Config 1: (Stage 1 servers = 1, Stage 2 servers = 2)
- Config 2: (Stage 1 servers = 2, Stage 2 servers = 1)
- Config 3: (Stage 1 servers = 2, Stage 2 servers = 2)
- Config 4: (Stage 1 servers = 1, Stage 2 servers = 3)

Response: mean job sojourn time $W$ (minutes).

Parameters: arrival rate λ=3/min, Stage 1 mean service time 0.5 min, Stage 2 mean 0.4 min.

**Tasks**

1. **Pilot study**: Run $n_0 = 15$ replications (2,000 jobs each, warmup 200) for each configuration.
   Report the sample mean $\bar{W}_i$ and sample variance $S_i^2$.

2. **Naive selection**: Choose the configuration with the lowest $\bar{W}_i$.
   Compute a 95% CI for that configuration only. Does the CI overlap with the second-best?

3. **Rinott procedure**: Set $P^* = 0.90$ and indifference zone $\delta^* = 0.05$ minutes.
   (a) Compute the required second-stage sample size $N_i$ for each configuration.
   (b) Run the second stage.
   (c) Report the selected best configuration and its final $\bar{W}_i$.

4. **Comparison**: Does the Rinott selection agree with the naive selection?
   If they differ, which do you trust more and why?

5. **Budget sensitivity**: Fill in the table below (keeping $n_0 = 15$ fixed):

   | $\delta^*$ (min) | $P^*$ | Total $N_i$ needed | Selected config |
   |:---:|:---:|:---:|:---:|
   | 0.10 | 0.90 | | |
   | 0.05 | 0.90 | | |
   | 0.05 | 0.95 | | |
   | 0.02 | 0.95 | | |

   At which $(\delta^*, P^*)$ setting does the required budget first exceed 500 total replications?
