# Ch. 11 — P01 (K) ★★ Common Random Numbers

**Type**: Coding | **Difficulty**: ★★ | **Chapter**: 11

---

You are comparing two inventory policies for a retail store:
- **Policy A** (baseline): reorder point $s=10$, order-up-to $S=50$
- **Policy B** (new): reorder point $s=15$, order-up-to $S=60$

Response: mean total cost per day (holding + ordering + shortage).

Use the `simdes` package `SSInventory` model (or implement your own).

**Tasks**

1. **Independent streams**: Run 30 replications for each policy using independent seeds.
   Compute the mean cost, standard deviation, and 95% CI for each.
   Is the difference statistically significant?

2. **CRN implementation**: Run 30 paired replications.
   Both policies use the same demand stream (same seed for demand generation).
   Compute $D_i = \text{cost}_A(i) - \text{cost}_B(i)$ for each replication $i$.
   Report $\bar{D}$, $s_D$, and the 95% CI for $E[D]$.

3. **Variance reduction**: Compare $s_D^2$ (CRN) to $s_A^2 + s_B^2$ (independent).
   Report the variance reduction ratio.
   Explain in 2 sentences why sharing the demand stream induces positive correlation.

4. **When does CRN help?**: Suppose you instead compared:
   - Policy A: $s=10$, $S=50$
   - Policy C: $s=10$, $S=50$, but with a different supplier (2× longer lead time)
   
   Would CRN still help? Which stream(s) should be shared?
   Describe the synchronisation challenge when the two systems have structurally different event sequences.

5. **Effect size**: Based on the CRN paired-difference CI, is the cost difference
   between A and B practically significant (i.e., worth the operational change)?
   Define "practical significance" for this problem.
