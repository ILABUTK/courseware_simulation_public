# M05 Reading Guide

**Module**: M05 — Queue Models in SimPy

## Required Reading

1. Book Chapter 7: *Queue Models — From Analytics to Simulation*
2. Book Appendix C.1–C.3: *Queueing Theory Essentials* — M/M/1, M/M/c (Erlang-C), M/G/1 (Pollaczek-Khinchine formula)
3. SimPy documentation, "Resources" — `Resource`, `PriorityResource`; the core SimPy tools used in every notebook this module

## Recommended External Reading

1. Gross et al. (2008), *Fundamentals of Queueing Theory*, Chapters 2–3 — M/M/1 derivation and M/M/c tables; use to check your Erlang-C computations
2. Hillier and Lieberman (2021), *Introduction to Operations Research*, Chapter 17 — alternative derivation of M/M/c; useful if the book's notation feels unfamiliar
3. Law (2015), Chapter 4, Section 4.3 — queueing simulations as validation benchmarks; explains why M/M/1 is the canonical "sanity check" for a new simulator

## Before Class

Be prepared to answer:
- What is the condition for a stable M/M/c queue, and what happens when ρ ≥ 1?
- Why does the Pollaczek-Khinchine formula depend on the variance of service time, not just its mean?
- How do you use `simpy.PriorityResource` to model priority classes?

## After Class

Complete HW-03. For the multi-server extension, verify your SimPy `Wq` against the Erlang-C formula from Appendix C.2. If they differ by more than 5%, check your seed handling and replication count before blaming the formula.
