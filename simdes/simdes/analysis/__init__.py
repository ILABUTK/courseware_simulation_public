"""Output analysis utilities."""

from simdes.analysis.ci import confidence_interval, n_reps_required
from simdes.analysis.replications import batch_means, run_replications
from simdes.analysis.scenarios import compare_scenarios, paired_crn
from simdes.analysis.warmup import welch_method

__all__ = [
    "confidence_interval",
    "n_reps_required",
    "run_replications",
    "batch_means",
    "welch_method",
    "compare_scenarios",
    "paired_crn",
]
