# Ch. 4 — P01 (T) ★★ Event Calendar and Simultaneous Events

**Type**: Trace | **Difficulty**: ★★ | **Chapter**: 4

---

A bank has **two tellers** (servers) operating FCFS.
The bank opens at $t=0$ with both servers idle.
Use the following trace data:

| Customer | Arrival time | Service time |
|:---:|:---:|:---:|
| 1 | 0 | 5 |
| 2 | 2 | 8 |
| 3 | 4 | 3 |
| 4 | 7 | 6 |
| 5 | 10 | 4 |
| 6 | 12 | 7 |
| 7 | 15 | 2 |
| 8 | 18 | 5 |

**Routing rule**: An arriving customer chooses the teller who will be free soonest.
Ties are broken by teller ID (Teller 1 preferred).

**Tasks**

1. Build the event calendar in chronological order.
   For each event, record:
   - Time
   - Event type (Arrival / Departure)
   - Customer number
   - Which teller is involved (for departures)

   Apply the simultaneous-event convention: Departure before Arrival at the same time.

2. For each customer, fill in:

   | Customer | Arrival | Teller | Service begins | Service ends | Wait $W_q$ | Sojourn $W$ |
   |:---:|:---:|:---:|:---:|:---:|:---:|:---:|
   | 1 | 0 | | | | | |
   | … | | | | | | |

3. Compute $\hat{W}_q$ and $\hat{W}$.

4. Compute the utilisation of each teller separately.
   Do they differ? Why or why not?

5. Compute the time-average number in the system $\hat{L}$
   using the area-under-curve method.
   Verify Little's Law.

6. Identify any simultaneous events in this trace.
   For each, show what state change would occur if the order were reversed
   (Arrival before Departure). Does it matter?
