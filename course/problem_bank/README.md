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
These standalone LaTeX problems (`.tex` → `.pdf`, built with `make problems`) are *not* embedded in the book prose.
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
| **Extra credit / enrichment** | D (Design) problems have no single answer — good complements to HW-01–HW-06 and the team project |

These problems are **single focused exercises** (1–6 parts, solvable in 30–90 min).
The multi-part weekly homework assignments in `assignments/` are a separate, larger-scale artifact.

**Layer 3 — Extra capstone problems** (`course/problem_bank/extra_capstones/extra_problems.tex`)
27 open-ended, multi-week capstone studies drawn from real operational settings
(healthcare, manufacturing, logistics, transportation, computing, and more).
Each problem specifies a system, representative data, KPIs, and 5–7 structured
deliverables suitable for a full simulation project. (Their exemplar solutions are being
re-verified and are not distributed at present.)

## Problem Naming Convention

`course/problem_bank/chXX/pYY_TYPE_short_title.tex` (and its built `.pdf`)

- `XX`: two-digit chapter number
- `YY`: two-digit problem number within the chapter
- `TYPE`: one of:
  - `C` — Conceptual
  - `A` — Analytical (closed-form derivation)
  - `T` — Trace (hand-simulate)
  - `K` — Coding (Python/SimPy)
  - `D` — Design (open-ended)

Difficulty is stated in the title block: ★ / ★★ / ★★★. The title block also shows the course module (M01–M12) that covers the chapter.

## Problem Index

48 problems. Files named `pYY_TYPE_ai_*` are *critique-the-AI* problems.

| File | Type | Difficulty | Topic |
|---|---|---|---|
| ch01/p01_C_classify_systems.tex | C | ★ | Classify Systems |
| ch01/p02_D_design_study.tex | D | ★★ | Design a Simulation Study |
| ch02/p01_C_when_to_simulate.tex | C | ★ | When to Simulate |
| ch02/p02_C_jensens_inequality.tex | C | ★★ | Jensen's Inequality and Variability |
| ch02/p03_C_ai_clinic_averages.tex | C | ★ | Critique the AI: A Spreadsheet Says No Waiting |
| ch03/p01_D_conceptual_model.tex | D | ★★ | Conceptual Model for a Coffee Kiosk |
| ch03/p02_C_boundary_decisions.tex | C | ★ | Model Boundary Decisions |
| ch03/p03_C_ai_conceptual_model.tex | C | ★★ | Critique the AI: A Conceptual Model That Cannot Run |
| ch04/p01_T_event_calendar.tex | T | ★★ | Event Calendar and Simultaneous Events |
| ch04/p02_C_event_loop_algorithm.tex | C | ★ | Understanding the Event Loop |
| ch05/p01_T_trace_single_server.tex | T | ★ | Trace a Single-Server Queue |
| ch05/p02_A_littles_law.tex | A | ★ | Little's Law Applications |
| ch05/p03_C_ai_hand_trace.tex | C | ★★ | Critique the AI: A Trace Where No One Waits |
| ch06/p01_K_simpy_mmc.tex | K | ★★ | Implement M/M/c in SimPy |
| ch06/p02_K_rng_streams.tex | K | ★ | Random Number Streams and Reproducibility |
| ch06/p03_K_ai_simpy_release.tex | K | ★★ | Critique the AI: A Pharmacy With No Waiting |
| ch07/p01_A_mm1_formulas.tex | A | ★ | M/M/1 Formulas |
| ch07/p02_A_mmc_erlang_c.tex | A | ★★ | M/M/c and the Erlang-C Formula |
| ch07/p03_K_mm1_simpy_verify.tex | K | ★★ | Verify M/M/1 in SimPy |
| ch07/p04_K_mg1_variance_effect.tex | K | ★★ | M/G/1 and the Effect of Service-Time Variance |
| ch07/p05_D_clinic_design.tex | D | ★★★ | Clinic Staffing Design |
| ch07/p06_K_ai_wait_vs_system.tex | K | ★★ | Critique the AI: Wait or Time in System? |
| ch08/p01_T_inventory_trace.tex | T | ★ | (s,S) Inventory Manual Trace |
| ch08/p02_K_ss_inventory.tex | K | ★★ | SimPy (s,S) Inventory Model |
| ch08/p03_D_ss_optimization.tex | D | ★★★ | (s,S) Policy Optimization |
| ch08/p04_K_ai_inventory_position.tex | K | ★★ | Critique the AI: An (s,S) Policy That Over-Orders |
| ch09/p01_A_distribution_fitting.tex | A | ★★ | Distribution Fitting by Hand |
| ch09/p02_K_scipy_fitting.tex | K | ★ | Automated Distribution Fitting with SciPy |
| ch09/p03_K_ai_normal_fit.tex | K | ★★ | Critique the AI: A Normal Fit for Service Times |
| ch10/p01_A_warmup_analysis.tex | A | ★★ | Warmup Analysis |
| ch10/p02_A_sample_size.tex | A | ★★ | Sample Size and Confidence Interval Width |
| ch10/p03_K_ai_single_run_ci.tex | K | ★★ | Critique the AI: A Confidence Interval From One Run |
| ch11/p01_K_crn_comparison.tex | K | ★★ | Common Random Numbers |
| ch11/p02_A_variance_reduction.tex | A | ★★ | Antithetic Variates |
| ch11/p03_A_factorial_effects.tex | A | ★★ | 2^2 Factorial Effects |
| ch11/p04_K_ranking_selection.tex | K | ★★ | Ranking and Selection Implementation |
| ch11/p05_K_ai_compare_no_crn.tex | K | ★★ | Critique the AI: Declaring a Winner From Two Runs |
| ch12/p01_C_verification_checklist.tex | C | ★ | Verification and Validation Concepts |
| ch12/p02_K_debug_flawed_model.tex | K | ★★ | Debugging a Flawed Simulation |
| ch12/p03_C_ai_validation_claim.tex | C | ★★ | Critique the AI: “The Model Is Validated” |
| ch13/p01_A_simopt_gradient.tex | A | ★★ | Stochastic Gradient and Noise in SimOpt |
| ch13/p02_K_simopt_nelder_mead.tex | K | ★★★ | Nelder-Mead on a Stochastic Response Surface |
| ch13/p03_K_ai_optimization_bias.tex | K | ★★★ | Critique the AI: The Best of Ten Noisy Runs |
| ch14/p01_A_mdp_formulation.tex | A | ★★ | MDP Formulation for a Queuing System |
| ch14/p02_K_q_learning_simdes.tex | K | ★★★ | Q-Learning on a SimPy Gymnasium Environment |
| ch14/p03_K_ai_rl_seed_leak.tex | K | ★★★ | Critique the AI: A Q-Learner That Beats Everything |
| ch15/p01_D_digital_twin_design.tex | D | ★★★ | Designing a Digital Twin for a Manufacturing Cell |
| ch15/p02_C_case_study_critique.tex | C | ★★ | Critical Analysis of a Published Case Study |
