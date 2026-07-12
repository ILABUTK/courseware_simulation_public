# Simulation Without a Black Box — Course Materials (cc7066a-dirty)

Public companion materials for the discrete-event simulation course and textbook
*Simulation Without a Black Box: Discrete-Event Modeling and Analysis for the AI Era*.

## Contents

- `book/` — the full textbook PDF, free to read
- `course/modules/M01…M12/` — lecture slide PDFs, Jupyter notebooks, and readings
- `course/syllabus/` — course syllabus and schedule (PDF)
- `course/assignments/` — assignment statements (PDF)
- `course/problem_bank/` — problem bank (statements only)
- `showcase/ep01/` — a complete capstone example: SimPy model, report, and an
  interactive dashboard (running model)
- `course/case_studies/`, `course/data/` — clinic & container-terminal case studies with datasets
- `simdes/` — the Python companion package (`pip install -e simdes/`)
- `environment/` — Docker + pinned requirements

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r environment/requirements.txt
pip install -e simdes/
jupyter lab
```

## For Instructors

Solutions, editable assignment/slide sources, and grading rubrics are available
to instructors adopting the course — contact the author.

## License

See `LICENSE` and `CITATION.cff`. Please cite the course materials if you use them.
