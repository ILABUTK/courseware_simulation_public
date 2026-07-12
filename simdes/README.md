# simdes

Python companion package for *Simulation Without a Black Box: Discrete-Event Modeling and Analysis for the AI Era*.

## Install

From the repository root, the recommended path is:

```bash
bash cli.sh setup
```

If you are working directly inside `simdes/`, the equivalent manual install is:

```bash
pip install -e .          # editable install from this directory
pip install simdes        # from PyPI (once published)
```

From the repository root, the editable install command is:

```bash
python3 -m pip install -e ./simdes
```

## Quick Start

```python
from simdes.models.queues import MM1Queue
from simdes.analysis.ci import confidence_interval

model = MM1Queue(arrival_rate=0.8, service_rate=1.0, sim_time=10_000, seed=42)
reps = model.run_replications(n=30)
print(confidence_interval(reps["mean_wait"]))
```

## Package Layout

```
simdes/
├── core/           # BaseModel, SimPy env helpers
├── models/         # MM1Queue, MMCQueue, SSInventory, ClinicModel, TerminalModel
├── analysis/       # replications, warmup (Welch), CI, scenario comparison, CRN
├── input_modeling/ # distribution fitting, goodness-of-fit
├── envs/           # Gymnasium environments (Module M12)
└── plotting/       # shared matplotlib helpers
```

## Run Tests

```bash
pytest tests/ -v --cov=simdes
```

Coverage target: ≥ 80% on `simdes/models/` and `simdes/analysis/`.
