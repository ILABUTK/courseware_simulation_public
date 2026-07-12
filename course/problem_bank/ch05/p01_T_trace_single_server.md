# Ch. 5 — P01 (T) ★ Trace a Single-Server Queue

**Type**: Trace | **Difficulty**: ★ | **Chapter**: 5

---

A single-server barbershop operates from 9:00 AM to 1:00 PM (240 minutes).
Use the inter-arrival times and service times given below.
The shop is empty at time 0.

| Customer | Inter-arrival time (min) | Service time (min) |
|---|---|---|
| 1 | 0 (arrives at t=0) | 12 |
| 2 | 8 | 15 |
| 3 | 5 | 10 |
| 4 | 12 | 8 |
| 5 | 3 | 20 |
| 6 | 15 | 7 |
| 7 | 6 | 14 |
| 8 | 10 | 11 |

**Tasks**:

1. Complete the event trace table below for all customers who *begin service* before t = 240.

   | Customer | Arrival time | Service begins | Service ends | Wait in queue | Time in system |
   |---|---|---|---|---|---|
   | 1 | 0 | | | | |
   | … | | | | | |

2. Compute the sample mean wait in queue $\bar{W}_q$ and mean time in system $\bar{W}$.

3. Estimate the time-average number in the system $\bar{L}$ using the area-under-curve method.

4. Verify Little's Law: check whether $\bar{L} \approx \hat{\lambda} \cdot \bar{W}$, where $\hat{\lambda}$ is the observed arrival rate.

5. What is the server utilization over this 240-minute period?
