# Ch. 4 — P02 (C) ★ Understanding the Event Loop

**Type**: Conceptual | **Difficulty**: ★ | **Chapter**: 4

---

The core discrete-event simulation algorithm (Algorithm 4.1 in the text)
repeats the following steps:

1. Remove the event with the smallest time from the event calendar.
2. Advance the simulation clock to that event's time.
3. Execute the event routine (update state, schedule new events).
4. Repeat until the stopping condition is met.

Answer the following questions about this algorithm.

1. **Event calendar data structure**: The event calendar is typically implemented
   as a min-heap (priority queue). What is the time complexity of:
   (a) Inserting a new event
   (b) Removing the next event (smallest time)
   (c) Peeking at the next event without removing it

   Why is a sorted list not used instead?

2. **Clock advancement**: The simulation clock jumps from event to event.
   Between consecutive events at times $t_i$ and $t_{i+1}$, does the system state change?
   Why is this the defining property of discrete-event simulation?

3. **Event granularity**: A student proposes modelling a queueing system by
   advancing the clock in fixed 1-minute increments and checking for arrivals
   and departures at each step. What is this approach called?
   What are its disadvantages compared to the event-driven approach?

4. **Endogenous vs. exogenous events**: Classify each of the following as
   endogenous (caused by the model's own dynamics) or exogenous (driven by external input):
   (a) A service completion event
   (b) A patient arrival event
   (c) A machine breakdown event triggered by a Poisson process
   (d) A shift change at a fixed clock time (e.g., 17:00 daily)

5. **Infinite event calendars**: Can the event calendar grow without bound?
   Describe a scenario where it could, and explain how the simulation would
   behave in that case (hint: consider a system where arrivals outpace departures).
