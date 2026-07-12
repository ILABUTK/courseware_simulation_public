# Container Terminal Case Study — Conceptual Model

## System Description

A container terminal receives trucks that arrive to pick up or drop off shipping containers.
Each truck passes through two sequential stages: (1) an inspection/processing gate, and (2)
a yard crane operation to load or unload the container. The terminal operates a fixed shift
(default: 8 hours). The study focuses on truck throughput time and waiting at each stage.

## Entities

| Entity | Attributes | Entry point | Exit point |
|---|---|---|---|
| Truck | arrival_time, wait_gate, wait_crane | Arrival event | Departure after crane service |

Trucks are the sole entity type. Each truck carries one container transaction (pickup or
delivery). The distinction between pickup and delivery is not modeled — service times are
assumed identical for both.

## Resources

| Resource | Capacity | Service distribution | Discipline |
|---|---|---|---|
| Inspection gate | `n_gates` (configurable, default 2) | Exp(mean = `gate_mean` min) | FCFS |
| Yard crane | `n_cranes` (configurable, default 1) | Exp(mean = `crane_mean` min) | FCFS |

Gates and cranes are independent resource pools. A truck must complete gate processing
before entering the crane queue; there is no direct gate-to-crane assignment.

## Events

1. **Truck arrives**: scheduled by a Poisson process at rate `arrival_rate` trucks/hour.
   Inter-arrival times are Exp(60/arrival_rate) minutes.
2. **Gate service begins**: when a truck reaches the front of the gate queue and a gate
   becomes free.
3. **Gate service ends / crane queue entry**: after Exp(`gate_mean`) service time.
   The truck immediately joins the crane queue.
4. **Crane service begins**: when the truck reaches the front of the crane queue and a
   crane becomes free.
5. **Crane service ends / truck departs**: after Exp(`crane_mean`) service time.
   The truck exits the system; total time in system is recorded.

## State Variables

- `gate_queue_length`: number of trucks waiting for a gate
- `crane_queue_length`: number of trucks waiting for a crane
- `gates_busy`: number of gates currently in service
- `cranes_busy`: number of cranes currently in service

## Performance Measures

| Measure | Symbol | Definition |
|---|---|---|
| Mean total time in system | W | From arrival to crane-service completion |
| Mean wait at gate | Wq_gate | Time from arrival until gate service begins |
| Mean wait at crane | Wq_crane | Time from gate exit until crane service begins |
| Throughput | TH | Number of trucks processed per shift |
| Gate utilization | ρ_gate | Fraction of time each gate is busy |
| Crane utilization | ρ_crane | Fraction of time each crane is busy |

## Assumptions

| # | Assumption | Consequence if violated |
|---|---|---|
| 1 | Truck arrivals are Poisson (rate constant over the shift) | If arrivals are bursty or time-varying, gate queues will spike; NHPP thinning required |
| 2 | Gate service times are exponentially distributed | Longer-tailed distributions (e.g., lognormal) would increase tail wait times |
| 3 | Crane service times are exponentially distributed | Same as above; particularly sensitive given crane is typically the bottleneck |
| 4 | All gates are identical and interchangeable | Dedicated gate lanes (e.g., hazmat) would require separate resources |
| 5 | All cranes are identical and interchangeable | In practice, crane reach varies; a more detailed model would use crane-specific queues |
| 6 | No truck abandonment or balking | Trucks must complete their transaction; realistic for contractual delivery |
| 7 | The terminal is empty at time 0 | A warm-up period may be needed for steady-state analysis |
| 8 | Zero travel time between gate and crane | Negligible relative to service times at typical terminal scale |

## Model Parameters (Defaults)

| Parameter | Symbol | Default | Notes |
|---|---|---|---|
| Number of gates | n_gates | 2 | Design variable |
| Number of cranes | n_cranes | 1 | Design variable |
| Arrival rate | arrival_rate | 10 trucks/hr | Calibrated to busy-hour data |
| Gate mean service time | gate_mean | 4 min | Administrative processing |
| Crane mean service time | crane_mean | 12 min | Container lift + placement |
| Simulation duration | sim_time | 8 hr | One operating shift |

## Scope Boundary

**In scope**: truck arrival, gate processing, crane operation, truck departure.

**Out of scope**: vessel operations (container unloading from ship), truck routing inside
the yard, equipment breakdowns, shift changes, and priority among trucks (e.g., hazardous
materials or time-sensitive cargo).
