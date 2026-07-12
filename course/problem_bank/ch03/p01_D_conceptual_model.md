# Ch. 3 — P01 (D) ★★ Conceptual Model for a Coffee Kiosk

**Type**: Design | **Difficulty**: ★★ | **Chapter**: 3

---

A university coffee kiosk operates 7:00–10:00 AM on weekdays.
Walk-up customers order at one of two registers, wait for a barista to prepare their drink,
collect it at the pickup counter, and leave.
There are 2 cash registers and 3 baristas.
A customer whose order requires more than one barista action (e.g., two espressos)
holds one barista until the order is complete.

The simulation study question is:
*"How many baristas are needed to keep mean wait-for-drink time below 3 minutes
at 95th percentile during the 8:00–9:00 peak hour?"*

**Tasks**

1. **Boundary choice**: Identify what is inside and outside the model boundary.
   Justify your choice given the study question.

2. **Entity table**: List all entity types with their attributes.
   Include at least 3 attributes per entity.

3. **Resource table**: List all resources with: name, capacity, service time
   distribution (state plausible parameters), and discipline.

4. **Event list**: List all distinct events with:
   - The state change each causes
   - Which resources are seized or released

5. **State variables**: List the minimal set of state variables needed to
   resume the simulation from any snapshot.

6. **Performance measures**: Define at least 4 performance measures
   that address the study question, with mathematical notation.

7. **Assumptions**: Write at least 6 explicit, quantified assumptions.
   For each, state what modelling error its violation would introduce.

8. **Pre-simulation bound**: The peak-hour arrival rate is 45 customers/hour.
   With 3 baristas each serving at rate $\mu = 20$ orders/hour,
   compute the utilisation $\rho$. Is the system stable at peak load?
   At what minimum number of baristas does stability hold?
