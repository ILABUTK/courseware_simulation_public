# Ch. 6 — P02 (K) ★ Random Number Streams and Reproducibility

**Type**: Coding | **Difficulty**: ★ | **Chapter**: 6

---

Random number management is critical for reproducible and comparable simulation experiments.

**Tasks**

1. **Stream independence**: Using `np.random.default_rng(42).spawn(3)`, generate 3 child
   generators. Draw 10 exponential(mean=1) samples from each and verify (by inspection)
   that they produce different sequences despite sharing a parent seed.

2. **Reproducibility**: Show that running the same SimPy M/M/1 model with the same seed
   twice produces identical results. Then show that changing the seed by 1 produces
   different (but still valid) results.

3. **Stream synchronisation**: You are comparing two service policies: FCFS and LCFS.
   Both should use the same sequence of interarrival times (same randomness in arrivals)
   but may use different service time sequences.
   Write code that:
   - Creates one `arr_rng` shared between both policies
   - Creates two separate `svc_rng_fcfs` and `svc_rng_lcfs`
   - Simulates 200 customers under each policy
   - Reports mean sojourn time $\bar{W}$ for each

   Do you expect $\bar{W}$ to differ between FCFS and LCFS? Why or why not?
   (*Hint*: for M/M/1, Little's Law implies $\bar{W}$ is the same regardless of discipline
   as long as the server is non-preemptive.)

4. **Anti-pattern**: A student writes the following code:
   ```python
   for i in range(10):
       rng = np.random.default_rng(42)  # resets seed each iteration
       results.append(simulate(rng))
   ```
   What is wrong with this? What will `results` contain?
   Rewrite the loop correctly.
