# Ch. 9 — P02 (K) ★ Automated Distribution Fitting with SciPy

**Type**: Coding | **Difficulty**: ★ | **Chapter**: 9

---

Load the terminal service time dataset from `data/terminal_service_times.csv`.

**Tasks**

1. Compute the five-number summary (min, Q1, median, Q3, max),
   mean, standard deviation, and CV.

2. Fit four candidate distributions using `scipy.stats` MLE (all with `floc=0`):
   - `gamma`
   - `weibull_min`
   - `lognorm`
   - `expon`

   For each fit, report the estimated parameters, the fitted mean, and the AIC.

3. For the two best-AIC distributions, run a two-sided KS test.
   Report: test statistic, p-value, decision at $\alpha=0.05$.

4. Produce a figure with two subplots:
   - Left: histogram with fitted PDFs overlaid
   - Right: ECDF with fitted CDFs overlaid
   Use a legend that includes the AIC for each distribution.

5. Produce a Q-Q plot for the best-fit distribution.
   Annotate with the 45° reference line.
   Comment on whether the upper tail is well-fitted.

6. Write an input model specification (4–6 sentences) for use in a SimPy model.
   Include the SimPy code line that would sample from the fitted distribution.
