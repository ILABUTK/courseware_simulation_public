# Case Study: Primary Care Clinic

This case study is developed progressively across Modules M05–M12.

## System Description

A primary care clinic operates 8 hours per day (480 minutes).
Patients arrive, register at the front desk, see a triage nurse, then wait for an available exam room.

## Case Study Phases

| Phase | Module | Notebook | What you build |
|---|---|---|---|
| 1 | M05 | `phase1_single_nurse.ipynb` | M/M/1 approximation: single nurse, no registration |
| 2 | M05 | `phase2_two_stage.ipynb` | Two-stage: registration + nurse |
| 3 | M06 | `phase3_full_clinic.ipynb` | Full three-stage model (registration, triage, exam) |
| 4 | M08 | `phase4_scenarios.ipynb` | Output analysis: 30 reps, CIs, scenario comparison |
| 5 | M12 | `phase5_rl_agent.ipynb` | RL: PPO agent controls nurse count |

## Files

- `conceptual_model.md` — entity–resource–event description
- `clinic_model.py` — notebook-facing wrapper re-exporting `ClinicModel`/`ClinicParams`
  from `simdes.models.clinic`, plus a `run_clinic()` replication helper
- `notebooks/` — phase notebooks; Phase 5 imports the Gymnasium wrapper
  directly from `simdes.envs.clinic_env.ClinicEnv`

## Data

Input data are in `data/clinic_arrivals.csv` and `data/clinic_service_times.csv`.
