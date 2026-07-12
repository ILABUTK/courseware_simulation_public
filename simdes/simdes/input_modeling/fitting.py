"""Distribution fitting utilities using scipy.stats."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
import scipy.stats as stats

FloatArray = npt.NDArray[np.float64]

# Distributions considered by default when no candidate is specified
_CANDIDATE_DISTS = [
    "expon", "norm", "lognorm", "gamma", "weibull_min",
    "triang", "uniform", "erlang",
]


def fit_distribution(
    data: FloatArray | list[float],
    candidates: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Fit candidate distributions to *data* and rank by KS statistic.

    Args:
        data: 1-D array of observed values.
        candidates: List of ``scipy.stats`` distribution names to try.
            Defaults to :data:`_CANDIDATE_DISTS`.

    Returns:
        List of dicts sorted by ascending KS statistic, each containing:
        ``dist``, ``params``, ``ks_stat``, ``ks_pvalue``.

    Example:
        >>> import numpy as np
        >>> rng = np.random.default_rng(42)
        >>> data = rng.exponential(scale=2.0, size=200)
        >>> results = fit_distribution(data, candidates=["expon", "norm"])
        >>> results[0]["dist"]  # exponential should win
        'expon'
    """
    arr = np.asarray(data, dtype=float)
    if candidates is None:
        candidates = _CANDIDATE_DISTS

    results = []
    for name in candidates:
        dist = getattr(stats, name)
        try:
            params = dist.fit(arr)
            ks_stat, ks_p = stats.kstest(arr, name, args=params)
            results.append(
                {
                    "dist": name,
                    "params": params,
                    "ks_stat": float(ks_stat),
                    "ks_pvalue": float(ks_p),
                }
            )
        except Exception:
            continue

    results.sort(key=lambda r: r["ks_stat"])
    return results


def ks_test(
    data: FloatArray | list[float],
    dist_name: str,
    params: tuple[float, ...],
) -> tuple[float, float]:
    """Run a one-sample Kolmogorov-Smirnov test.

    Args:
        data: Observed data.
        dist_name: ``scipy.stats`` distribution name (e.g., ``"expon"``).
        params: Distribution parameters as returned by ``dist.fit()``.

    Returns:
        Tuple (ks_stat, p_value).
    """
    arr = np.asarray(data, dtype=float)
    ks_stat, p_value = stats.kstest(arr, dist_name, args=params)
    return float(ks_stat), float(p_value)
