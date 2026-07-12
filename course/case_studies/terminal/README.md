# Case Study: Intermodal Container Terminal

This case study is developed progressively across Modules M05–M12,
as a parallel track to the clinic case study.

## System Description

Trucks arrive at a container terminal gate, are inspected and processed,
then proceed to a yard crane for container pickup or dropoff.

## Case Study Phases

| Phase | Module | Notebook | What you build |
|---|---|---|---|
| 1 | M05 | `phase1_single_gate.ipynb` | Single inspection gate M/M/1 |
| 2 | M05 | `phase2_multilane.ipynb` | Multi-lane M/M/c gate |
| 3 | M06 | `phase3_full_terminal.ipynb` | Gate + yard crane two-stage model |
| 4 | M08 | `phase4_scenarios.ipynb` | Output analysis: gate count comparison |
| 5 | M12 | `phase5_rl_agent.ipynb` | RL: agent controls active gate count |

## Files

- `conceptual_model.md` — entity–resource–event description
- `terminal_model.py` — notebook-facing wrapper re-exporting `TerminalModel`/`TerminalParams`
  from `simdes.models.terminal`, plus a `run_terminal()` replication helper
- `notebooks/` — phase notebooks; Phase 5 imports the Gymnasium wrapper
  directly from `simdes.envs.terminal_env.TerminalEnv`

## Data

Input data are in `data/terminal_arrivals.csv` and `data/terminal_service_times.csv`.
