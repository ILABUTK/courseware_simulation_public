# Case Studies

Two parallel, progressively built running examples that thread through
Modules M05–M12: [`clinic/`](clinic/README.md) (healthcare queueing) and
[`terminal/`](terminal/README.md) (container-terminal queueing). Instead of a
new toy example every module, students return to the *same* system and add
complexity as the course adds tools — an M/M/1 approximation in M05 becomes a
multi-stage SimPy model in M06, gets a full output-analysis treatment in M08,
and is finally handed to an RL agent in M12.

## Why two parallel case studies

- **Clinic** (registration → triage nurse → exam room) is the primary
  worked example used in the book's chapter prose and figures.
- **Terminal** (inspection gate → yard crane) is a structurally analogous
  system in a different domain, so instructors can assign it as a parallel
  exercise, a midterm/final variant, or a way to check whether a student
  generalized the concepts rather than memorized the clinic case.

Both follow the identical 5-phase structure (see each subfolder's README for
its phase table): Phase 1 single-server approximation → Phase 2 multi-server
or two-stage → Phase 3 full multi-stage model → Phase 4 output analysis and
scenario comparison → Phase 5 reinforcement learning.

## What's in each case-study folder

| File | Purpose |
|---|---|
| `README.md` | Phase table (which module/notebook builds what) |
| `conceptual_model.md` | Entities, resources, events, state variables (Ch. 3 methodology) |
| `{clinic,terminal}_model.py` | Thin notebook-facing wrapper: re-exports the canonical model from `simdes` and adds a `run_{clinic,terminal}(params, n_reps)` replication helper |
| `notebooks/` | The 5 phase notebooks |

**The canonical model and RL-environment code lives in the `simdes` package**,
not here: `simdes.models.clinic.ClinicModel` / `simdes.models.terminal.TerminalModel`,
and `simdes.envs.clinic_env.ClinicEnv` / `simdes.envs.terminal_env.TerminalEnv`
(see `docs/CODEMAPS/package.md`). The `{clinic,terminal}_model.py` files here
just wrap that package API into the shape the case-study notebooks expect —
they are convenience layers, not the simulation logic itself.

## Data

Input datasets (arrival times, service times) are in `course/data/` —
see `course/data/README.md`.

## Distribution

Ships in both the instructor and public packages (no solutions live here);
see `docs/dist_plan.md`.
