# Ch. 9 — P01 (A) ★★ Distribution Fitting by Hand

**Type**: Analytical | **Difficulty**: ★★ | **Chapter**: 9

---

You have collected 20 inter-arrival times (in minutes) from a university help desk:

```
2.3, 8.1, 0.4, 5.6, 12.4, 1.7, 3.9, 0.8, 6.2, 15.3,
0.2, 4.4, 9.7, 2.1, 0.6, 7.8, 3.3, 1.1, 5.0, 11.2
```

**Tasks**

1. Compute: $n$, mean $\bar{x}$, sample variance $s^2$, CV = $s/\bar{x}$, skewness.
   Based on CV alone, hypothesize whether the data is consistent with Exponential,
   Gamma (shape > 1), or heavy-tailed (CV > 1).

2. **Exponential MLE**: The MLE for the Exponential rate is $\hat{\lambda} = 1/\bar{x}$.
   Compute $\hat{\lambda}$ and the fitted mean.

3. **Gamma MLE** (method of moments as an approximation):
   Using $\hat{k} = \bar{x}^2 / s^2$ and $\hat{\theta} = s^2 / \bar{x}$,
   compute the method-of-moments estimates for shape $k$ and scale $\theta$.
   What is the fitted mean and variance?

4. **KS test by hand**: Compute the empirical CDF $F_n(x_i) = i/n$ for $i=1,\ldots,n$
   after sorting the data.
   For the Exponential fit, compute $F(x_i; \hat{\lambda}) = 1 - e^{-\hat{\lambda} x_i}$.
   Find $D_n = \max_i |F_n(x_i) - F(x_i)|$.

   The critical value for a two-sided KS test at $\alpha=0.05$ with $n=20$ is approximately 0.294.
   Do you reject the Exponential hypothesis?

5. Which distribution do you select and why?
   Write a one-paragraph input model specification for this dataset.
