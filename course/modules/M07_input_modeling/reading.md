# M07 Reading Guide

**Module**: M07 — Input Modeling

## Required Reading

1. Book Chapter 9: *Input Modeling*
2. Book Appendix A: *Probability Distributions for Simulation* — shape, support, and parameterization of exponential, Erlang, Weibull, lognormal, gamma, and uniform families

## Recommended External Reading

1. Law (2015), Chapter 6 — "Selecting Input Probability Distributions"; the most thorough treatment of input modeling in the simulation literature; covers MLE, chi-squared GOF, and the dangers of misspecification
2. Asmussen and Glynn (2007), *Stochastic Simulation*, Chapter 1 — theoretical basis for why input distributions matter for output variance
3. `fitter` Python package documentation — automated distribution ranking by AIC/BIC; used in the L22 notebook

## Before Class

Be prepared to answer:
- What does MLE give you, and why is it preferred over method-of-moments for heavy-tailed distributions?
- What is the difference between the chi-squared goodness-of-fit test and the Kolmogorov-Smirnov test? When would you use each?
- What should you do when no standard distribution fits your data?

## After Class

Complete HW-05. Before submitting, verify that your fitted distribution is statistically plausible (GOF p-value > 0.05) and physically sensible (support, shape, and mean match the real-system context). A distribution that passes the KS test but has negative support for service times is not acceptable.
