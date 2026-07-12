# Problem Bank

This folder contains problem *statements only* — no solutions live here. Full
solutions exist (in the private `Courseware_Simulation` authoring repo, under
`solutions/`) and ship to instructors only as part of the instructor package
(see `docs/dist_plan.md`); the public package strips all solutions via a
leak check. See "Relationship to the Book" below for exactly where each
layer's solutions live.

## Relationship to the Book

The textbook has two distinct exercise layers:

**Layer 1 — In-book exercises** (embedded in `book/chapters/chXX_*.tex`, `\section{Exercises}`)
These are numbered Exercise 1.1, 1.2, etc., typeset directly in the chapter text.
Students encounter them while reading. Solutions are in `solutions/exercises/chXX/`.

**Layer 2 — Problem bank** (this folder)
These standalone Markdown files are *not* embedded in the book prose.
Each chapter's LaTeX source includes only a brief footnote pointing here.
They are flexible building blocks for the instructor to assign selectively.
Solutions are in `solutions/problem_bank/chXX/`.

## How to Use the Problem Bank

The type and difficulty metadata makes it easy to curate balanced sets:

| Use case | Guidance |
|---|---|
| **Weekly problem sets** | Pick 2–3 problems matching the week's chapter — a balanced set might be 1 C + 1 A/T + 1 K |
| **Exams** | C and A problems suit written exams; K problems suit take-home assessments |
| **Recitation / discussion** | T (Trace) problems are ideal for in-class hand-simulation exercises |
| **Differentiated difficulty** | ★ for participation credit; ★★★ for bonus or honors work |
| **Extra credit / enrichment** | D (Design) problems have no single answer — good complements to hw01–hw07 |

These problems are **single focused exercises** (1–6 parts, solvable in 30–90 min).
The multi-part weekly homework assignments in `assignments/` are a separate, larger-scale artifact.

**Layer 3 — Extra capstone problems** (`course/problem_bank/extra_capstones/extra_problems.tex`)
25 open-ended, multi-week capstone studies drawn from real operational settings
(healthcare, manufacturing, logistics, transportation, computing, and more).
Each problem specifies a system, representative data, KPIs, and 5–7 structured
deliverables suitable for a full simulation project.  Solutions are in
`solutions/extra_capstones/` (instructor package only).

## Problem Naming Convention

`course/problem_bank/chXX/pYY_TYPE_short_title.md`

- `XX`: two-digit chapter number
- `YY`: two-digit problem number within the chapter
- `TYPE`: one of:
  - `C` — Conceptual
  - `A` — Analytical (closed-form derivation)
  - `T` — Trace (hand-simulate)
  - `K` — Coding (Python/SimPy)
  - `D` — Design (open-ended)

Difficulty is stated in the file header: ★ / ★★ / ★★★.

## Problem Index

| File | Type | Difficulty | Topic |
|---|---|---|---|
| ch01/p01_C_classify_systems.md | C | ★ | System classification |
| ch01/p02_D_design_study.md | D | ★★ | Simulation study design |
| ch02/p01_C_when_to_simulate.md | C | ★ | When to simulate |
| ch02/p02_C_jensens_inequality.md | C | ★★ | Jensen's inequality |
| ch03/p01_D_conceptual_model.md | D | ★★ | Conceptual model design |
| ch03/p02_C_boundary_decisions.md | C | ★ | System boundary decisions |
| ch04/p01_T_event_calendar.md | T | ★ | Event calendar trace |
| ch04/p02_C_event_loop_algorithm.md | C | ★ | Event loop algorithm |
| ch05/p01_T_trace_single_server.md | T | ★ | Single-server queue trace |
| ch05/p02_A_littles_law.md | A | ★ | Little's Law application |
| ch06/p01_K_simpy_mmc.md | K | ★★ | SimPy M/M/c implementation |
| ch06/p02_K_rng_streams.md | K | ★★ | RNG streams |
| ch07/p01_A_mm1_formulas.md | A | ★ | M/M/1 closed-form |
| ch07/p02_A_mmc_erlang_c.md | A | ★★ | M/M/c Erlang-C |
| ch07/p03_K_mm1_simpy_verify.md | K | ★★ | Verify M/M/1 in SimPy |
| ch07/p04_K_mg1_variance_effect.md | K | ★★ | M/G/1 variance effect |
| ch07/p05_D_clinic_design.md | D | ★★★ | Clinic staffing design |
| ch08/p01_T_inventory_trace.md | T | ★ | (s,S) manual trace |
| ch08/p02_K_ss_inventory.md | K | ★★ | SimPy (s,S) model |
| ch08/p03_D_ss_optimization.md | D | ★★★ | Optimize (s,S) policy |
| ch09/p01_A_distribution_fitting.md | A | ★★ | Distribution fitting |
| ch09/p02_K_scipy_fitting.md | K | ★★ | scipy.stats fitting |
| ch10/p01_A_warmup_analysis.md | A | ★★ | Warmup period analysis |
| ch10/p02_A_sample_size.md | A | ★★ | Sample size calculation |
| ch11/p01_K_crn_comparison.md | K | ★★ | Common random numbers |
| ch11/p02_A_variance_reduction.md | A | ★★ | Variance reduction |
| ch11/p03_A_factorial_effects.md | A | ★★ | 2² factorial effects |
| ch11/p04_K_ranking_selection.md | K | ★★ | Ranking and selection |
| ch12/p01_C_verification_checklist.md | C | ★ | V&V checklist |
| ch12/p02_K_debug_flawed_model.md | K | ★★ | Debugging a flawed model |
| ch13/p01_A_simopt_gradient.md | A | ★★ | SimOpt gradient methods |
| ch13/p02_K_simopt_nelder_mead.md | K | ★★★ | Nelder-Mead optimisation |
| ch14/p01_A_mdp_formulation.md | A | ★★ | MDP formulation |
| ch14/p02_K_q_learning_simdes.md | K | ★★★ | Q-learning with SimPy |
| ch15/p01_D_digital_twin_design.md | D | ★★★ | Digital twin design |
| ch15/p02_C_case_study_critique.md | C | ★★ | Case study critique |
