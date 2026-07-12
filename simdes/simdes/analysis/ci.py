"""Confidence interval utilities for simulation output."""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt
import scipy.stats as stats

FloatArray = npt.NDArray[np.float64]


def confidence_interval(
    data: FloatArray | list[float],
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Compute a two-sided t-confidence interval.

    Args:
        data: Array of independent replication means.
        alpha: Significance level (default 0.05 → 95% CI).

    Returns:
        Tuple (mean, lower, upper) where [lower, upper] is the CI.

    Example:
        >>> import numpy as np
        >>> rng = np.random.default_rng(0)
        >>> data = rng.normal(loc=5.0, scale=1.0, size=30)
        >>> mean, lo, hi = confidence_interval(data)
        >>> lo < mean < hi
        True
    """
    arr = np.asarray(data, dtype=float)
    n = len(arr)
    if n < 2:
        raise ValueError("Need at least 2 observations for a confidence interval.")
    mean = float(np.mean(arr))
    se = float(np.std(arr, ddof=1)) / math.sqrt(n)
    t_crit = float(stats.t.ppf(1 - alpha / 2, df=n - 1))
    half_width = t_crit * se
    return mean, mean - half_width, mean + half_width


def n_reps_required(
    pilot_std: float,
    half_width: float,
    alpha: float = 0.05,
    n_pilot: int = 10,
) -> int:
    """Estimate the number of replications required for a target half-width.

    Uses the pilot standard deviation to estimate sample size via the
    one-sample t formula.  The result is conservative (rounds up).

    Args:
        pilot_std: Sample standard deviation from a pilot run.
        half_width: Desired absolute half-width of the confidence interval.
        alpha: Significance level.
        n_pilot: Number of pilot replications (used to determine df for t).

    Returns:
        Required number of replications (integer, ≥ 1).
    """
    t_crit = float(stats.t.ppf(1 - alpha / 2, df=n_pilot - 1))
    n = math.ceil((t_crit * pilot_std / half_width) ** 2)
    return max(n, 1)
