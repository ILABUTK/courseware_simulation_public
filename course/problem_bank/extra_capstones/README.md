# Extra Capstone Problems

25 open-ended capstone simulation studies for *Simulation Without a Black Box*.

## Contents

| File | Description |
|---|---|
| `extra_problems.tex` | Main LaTeX source — all 25 problems |
| `data/ep25_districts.csv` | District map for EP25 (fire station siting) |

## Building

```bash
cd course/problem_bank/extra_capstones
lualatex --shell-escape extra_problems.tex
lualatex --shell-escape extra_problems.tex   # second pass for TOC
```

Requires LuaLaTeX and the same font stack as the main book
(`TeX Gyre Termes`, `TeX Gyre Heros`, `Inconsolata`).

## Problem Index

| EP | Title | Domain | Difficulty |
|---|---|---|---|
| 01 | Emergency Department Patient Flow | Healthcare | ★★★ |
| 02 | Outpatient Clinic No-Shows and Overbooking | Healthcare | ★★ |
| 03 | ICU Surge Capacity Planning | Healthcare | ★★★ |
| 04 | Regional Mass Vaccination Campaign | Healthcare | ★★ |
| 05 | Job Shop with Machine Breakdowns | Manufacturing | ★★★ |
| 06 | Semiconductor Wafer Fabrication Re-entrant Flow | Manufacturing | ★★★ |
| 07 | Perishable Food Processing Line | Manufacturing | ★★ |
| 08 | Pharmaceutical Batch Manufacturing with Changeovers | Manufacturing | ★★★ |
| 09 | Coffee Shop Drive-Through and Walk-In | Retail / Service | ★★ |
| 10 | Supermarket Checkout Lane Design | Retail / Service | ★★ |
| 11 | E-Commerce Order Fulfillment Center | Retail / Service | ★★★ |
| 12 | Bank Branch with Teller and Digital Alternatives | Retail / Service | ★★ |
| 13 | Multi-Echelon Inventory Network | Logistics | ★★★ |
| 14 | Container Port Terminal Operations | Logistics | ★★★ |
| 15 | Last-Mile Parcel Delivery | Logistics | ★★ |
| 16 | Cold-Chain Pharmaceutical Distribution | Logistics | ★★★ |
| 17 | Highway Toll Plaza Congestion | Transportation | ★★ |
| 18 | Airport Gate Turnaround Operations | Transportation | ★★★ |
| 19 | Urban Signalized Intersection Control | Transportation | ★★ |
| 20 | Cloud Auto-Scaling for a Web API | Computing | ★★★ |
| 21 | Call Center with Skill-Based Routing | Computing | ★★ |
| 22 | Agile Sprint Capacity Planning | Projects | ★★ |
| 23 | Construction Project with Weather and Resource Conflicts | Projects | ★★★ |
| 24 | Capital Investment Portfolio Risk | Finance | ★★★ |
| 25 | Fire Station Location and Response Time | Public Safety | ★★★ |

## Solutions

Full instructor solutions (LLM prompts, Python code, output-analysis notebooks,
and model reports) live in `solutions/extra_capstones/` and are distributed only in the
instructor package (see `docs/dist_plan.md`).
