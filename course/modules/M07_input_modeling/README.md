# Module M07 — Input Modeling

<img src="preview.png" alt="A slide from the M07 live lecture, with a simulation model running" width="70%">

**Book chapters**: Ch. 9 (Input Modeling)
**Lectures**: L23–L25 | **Tier**: Intermediate

## Learning Objectives
1. Perform EDA and fit candidate distributions using scipy.stats / fitter.
2. Apply KS, chi-squared, and Anderson-Darling goodness-of-fit tests.
3. Select a distribution when data are scarce (triangular, PERT).
4. Generate random variates and verify by comparing to fitted parameters.

## Contents
| Item | File |
|---|---|
| Lecture 18 live deck (interactive) | `live/L18_input_fitting/`: run `bash cli.sh lecture dev L18` |
| Lecture 18 code (VS Code, `# %%` cells) | `code/l18_input_fitting.py`, tests `code/test_l18_input_fitting.py`, deck data `code/make_l18_data.py` |
| Lecture 19 live deck (interactive) | `live/L19_goodness_of_fit/`: run `bash cli.sh lecture dev L19` |
| Lecture 19 code (VS Code, `# %%` cells) | `code/l19_goodness_of_fit.py`, tests `code/test_l19_goodness_of_fit.py`, deck data `code/make_l19_data.py` |
| Slides L23–L25 | `slides/L23_eda_fitting.tex`, `slides/L24_goodness_of_fit.tex`, `slides/L25_clinic_input_model.tex` |
| Notebooks | `notebooks/L23_eda_fitting.ipynb` … `notebooks/L25_clinic_input.ipynb` |
| Assignment | `course/assignments/hw05_input_modeling.pdf` |
| Data | `../../data/clinic_arrivals.csv`, `clinic_service_times.csv` |
