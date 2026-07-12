# Problem 13.1 — Stochastic Gradient and Noise in SimOpt

**Chapter**: 13 — Simulation Optimization  
**Type**: A (Analytical)  
**Difficulty**: ★★

---

## Background

Simulation optimization (SimOpt) seeks to solve:

$$x^* = \arg\min_{x \in \mathcal{X}} \; g(x) = \mathbb{E}[G(x, \omega)]$$

where $G(x, \omega)$ is a single-replication output for scenario $x$ with random seed $\omega$.
Because the expectation is approximated by a sample mean, gradient estimates are noisy.

---

## Problem

A manufacturing system has a single tunable parameter: the reorder quantity $q \in [20, 200]$ units.
After 30 replications at $q = 80$ and $q = 100$, you observe:

| $q$ | $\bar{G}(q)$ (cost/day) | $s(q)$ (std dev) |
|-----|------------------------|------------------|
| 80  | 142.8                  | 18.4             |
| 100 | 137.3                  | 19.1             |

**(a)** Estimate the finite-difference gradient:
$$\hat{\nabla} g \approx \frac{\bar{G}(100) - \bar{G}(80)}{100 - 80}$$

**(b)** Construct a 95% confidence interval for the *difference in means* $g(100) - g(80)$ using a two-sample $t$-test with 29 degrees of freedom (each).  
At significance level $\alpha = 0.05$, is the gradient estimate statistically distinguishable from zero?

**(c)** The finite-difference step $h = 20$ introduces **approximation bias** (because $g$ is nonlinear) and **noise** (because samples are finite).  
Describe the trade-off: what happens to bias and noise as $h \to 0$? As $h \to \infty$?

**(d)** Suppose you are allowed a total budget of $B = 300$ replications to evaluate the gradient at $q = 80$ and $q = 100$.  
If $\text{Var}[G(80)] \approx \text{Var}[G(100)] \approx \sigma^2$, show that the optimal budget allocation is equal ($n_1 = n_2 = 150$).  
What changes if $\sigma^2(80) \neq \sigma^2(100)$? Give the optimal allocation formula.

---

## Data Summary

$$t_{0.025, 58} \approx 2.002 \qquad z_{0.025} = 1.960$$
