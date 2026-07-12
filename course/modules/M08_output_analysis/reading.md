# M08 Reading Guide

**Module**: M08 — Output Analysis

## Required Reading

1. Book Chapter 10: *Output Analysis*
2. Book Appendix B: *Statistical Essentials for Simulation Output* — t-distribution, confidence intervals, sequential sampling, the central limit theorem as applied to batch means

## Recommended External Reading

1. Welch (1983), "The Statistical Analysis of Simulation Results" — in Lavenberg (ed.), *Computer Performance Modeling Handbook*; the original presentation of the Welch method for warm-up deletion; short and still the best explanation
2. Law (2015), Chapter 9 — "Output Analysis for a Single System"; comprehensive treatment with examples; read Sections 9.1–9.5 before L26
3. Nelson (2016), Chapter 3 — sequential sampling and the Rinott procedure; good preparation for the replication planning exercises in L26

## Before Class

Be prepared to answer:
- What is initialization bias and why does it make the first few hundred observations unreliable?
- Why can you not use standard t-confidence intervals directly on output from a single long run without batching?
- What is the "rule of thumb" for the number of replications needed to achieve a CI half-width of δ?

## After Class

Complete HW-06. Plot your Welch moving-average curve (as shown in L25) and defend your chosen warm-up period. If two team members chose different warm-up lengths, discuss why and which produces better CI coverage.
