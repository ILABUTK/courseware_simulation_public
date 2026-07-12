# Data Files

Synthetic empirical datasets generated from known distributions for use in
input modeling (Module M07 / Ch. 9) and model calibration.

## Files

| File | Description | True distribution | Parameters |
|---|---|---|---|
| `clinic_arrivals.csv` | Inter-arrival times (minutes) for clinic patients | Exponential | λ = 5/hour ≈ 0.0833/min |
| `clinic_service_times.csv` | Triage service times (minutes) | Lognormal | μ_log=2.1, σ_log=0.4 |
| `terminal_arrivals.csv` | Inter-arrival times (minutes) for terminal trucks | Exponential | λ = 10/hour ≈ 0.167/min |
| `terminal_service_times.csv` | Gate processing times (minutes) | Gamma | shape=2.0, scale=2.5 |

## Generating the Data

Run the generator script (Phase 4 of development):
```bash
python data/generate_data.py --seed 42
```

The true distributions and parameters are intentionally *not* disclosed
to students — they must fit distributions themselves in the input modeling
module.

## Usage in Notebooks

```python
import pandas as pd
arrivals = pd.read_csv("../../data/clinic_arrivals.csv")["interarrival_time"]
```
