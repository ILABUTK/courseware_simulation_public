# Changelog

One entry per tagged release (see `docs/dist_plan.md` §7 for the versioning
scheme). Newest first.

## v0.3.0 — 2026-11-27

The Spring 2027 courseware.

- **Course design:** syllabus for 28 Tue/Thu classes; critical thinking as the main goal, with
  building a product end to end and AI competency as threads; grading 30/15/25/30; Docker
  required for students.
- **Live lectures:** 25 web decks (L01–L25) with speaker notes, 75-minute timing, practice and
  participation activities, handout and notes PDFs, and lecture code with tests. They replace
  the Beamer decks, which are being retired.
- **Course sites:** hosted lectures, a student site with scheduled releases, and an instructor
  site with class records and release controls. Skill surveys and participation from class logs.
- **Assessments:** new HW-00–HW-06, participation, team and project handouts (milestones P1–P7),
  rubrics and answer keys, in LaTeX only; files are named by NetID. The previous assignments,
  rubrics and solutions were removed.
- **Grading and repositories:** AI-assisted grading pipeline on anonymized packets
  (`docs/grading_workflow.md`); the course's own repository script replaces GitHub Classroom,
  retired in August 2026.
- **Student project template:** published as its own GitHub template repository.
- **Showcases:** clinic staffing, driver services office, warehouse, flood evacuation, and the
  emergency department (EP01) rebuilt on `simdes`.
- **simdes and simviz:** event traces (`simdes.trace`) and React components that replay them.
- **Book:** Appendix G (tools for simulation work) with a cheat sheet; ungraded warm-up
  exercises; corrected exercise statements and solutions.
- **Problem bank:** 48 chapter problems, including 12 critique-the-AI problems, each with a
  checked solution. EP02–EP27 capstone solutions are withdrawn until re-verified.
- **Distribution:** the public package releases course materials by `course/release.json`;
  `--no-tag` publishes between versions.
- **Licenses (2026-11-27):** code MIT; course materials CC BY-NC-SA 4.0; book PDF all rights
  reserved (free to read); solutions and rubrics all rights reserved. Replaces the Apache 2.0
  file shipped with earlier releases, which still applies to copies released under it.

- **simdes 0.2.1: `SSInventory` was wrong; its results from 0.2.0 and earlier
  must not be used.** It ordered on on-hand stock and cleared its pending flag
  at once (an order every 0.01 time units while stock was low), lost unmet
  demand (`avg_backorder` was always 0) and discarded ordered units that did not
  fit below S. It is now an event-driven continuous review of the inventory
  position with backorders, exact time averages, separate demand and lead-time
  random streams, a new `fill_rate` result, and tests against hand calculations
  and inventory theory. Materials that used it were rerun and updated (L17 deck,
  §8.5 and Exercise 8.5 of the book, the L21, L22 and L34 slides, notebooks,
  answer keys and the Chapter 8 Problem 2 solution).
- Fixed the public repo's empty `docs/` folder: the EP01 dashboard is now built
  before packaging. (Already synced to the public repo on 2026-07-14, under the
  v0.2.0 label.)
- `cli.sh ver minor|major` now checks that the book and course PDFs build from a
  clean state before tagging.

## v0.2.0 — 2026-07-12

- Added automated releases: pushing a `vX.Y.0` tag builds both packages, pushes
  them to the instructor and public repos, and creates a GitHub Release in each.
- Added the `cli.sh ver` command for version bumps.
- Fixed a LaTeX error in a Chapter 1 problem-bank solution.
- Fixed a broken figure path in the L11 (single server) slides.
- Added missing data-driven figures for Chapters 7–11 and 13.
- Fixed release version labels so that CI builds are stamped with the pushed tag.

## v0.1.1 — 2026-07-12

- Version tag only; same source commit as v0.1.0.

## v0.1.0 (development pre-release) — 2026-07-11

- First development release of the textbook, course materials, case studies,
  EP01 showcase and `simdes` package.
- Adopted the single-repo distribution model: one private authoring repo builds
  an instructor package and a public package (`scripts/build_dist.py`),
  replacing the former four-repo split. See `docs/dist_plan.md`.
