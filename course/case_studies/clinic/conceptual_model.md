# Clinic Case Study — Conceptual Model

## System Description

A primary care clinic sees walk-in and scheduled patients.
For this study we model only walk-in patients during an 8-hour operating day.

## Entities

| Entity | Attributes | Entry point | Exit point |
|---|---|---|---|
| Patient | arrival_time, acuity_level | Arrival event | Departure after exam |

## Resources

| Resource | Capacity | Discipline |
|---|---|---|
| Registration clerk | 1 (Phase 1–2) | FCFS |
| Triage nurse | 1–4 (configurable) | FCFS |
| Exam room / physician | 2–6 (configurable) | FCFS |

## Events

1. **Patient arrives**: scheduled by Poisson process with rate λ (per minute).
2. **Registration begins**: when patient reaches front of registration queue.
3. **Registration ends / triage queue entry**: after service time ~ Exp(reg_mean).
4. **Triage begins**: when nurse becomes available.
5. **Triage ends / exam queue entry**: after service time ~ Exp(triage_mean).
6. **Exam begins**: when exam room becomes available.
7. **Exam ends / patient departs**: after service time ~ Exp(exam_mean).

## State Variables

- `reg_queue_length`: number of patients waiting for registration
- `triage_queue_length`: number of patients waiting for triage
- `exam_queue_length`: number of patients waiting for exam room
- `nurse_busy[i]`: boolean, whether nurse i is occupied

## Performance Measures

- Mean total time in system (W)
- Mean wait at each stage (W_reg, W_triage, W_exam)
- Utilization of each resource type
- Number of patients seen per day (throughput)

## Assumptions

1. Patient arrivals are Poisson with constant rate (no time-of-day variation).
2. All service times are exponentially distributed (memoryless).
3. No patient abandonment (all patients wait indefinitely).
4. Registration clerks are always available (never on break).
5. Exam rooms are interchangeable (any patient can use any room).
6. The clinic is empty at time 0.
