# M03 Reading Guide

**Module**: M03 — The DES Worldview and Manual Tracing

## Required Reading

1. Book Chapter 4: *DES Core Concepts and the Event Calendar*
2. Book Chapter 5: *Manual Event Tracing and Performance Measures*
3. Book Appendix C.4: *Little's Law* — proof, conditions, and applications

## Recommended External Reading

1. Banks et al. (2010), Chapters 2–3 — the event-scheduling worldview and three-phase execution; complements the book's treatment with a different notation
2. Fishman (2001), Chapter 2 — formal definition of the event calendar as a min-heap; useful for students who want to implement their own DES engine
3. Little (2011), "Little's Law as Viewed on Its 50th Anniversary" — *Operations Research* 59(3): 536–549; accessible account of where the law applies and where it fails

## Before Class

Be prepared to answer:
- What is the simulation clock and what does it mean for it to "advance"?
- What are the three types of events in the three-phase execution model (A, B, C)?
- Given a trace table for a single-server queue, how do you compute Wq and L?

## After Class

Complete the HW-02 manual trace (10-customer trace for a single-server queue). Verify your L, Lq, W, Wq results using Little's Law: L = λW and Lq = λWq. If your numbers do not satisfy both equations, find the error in your trace before submitting.
