"""Scenario comparison and common random numbers (CRN)."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy.stats as stats

FloatArray = npt.NDArray[np.float64]


def compare_scenarios(
    results_a: FloatArray,
    results_b: FloatArray,
    alpha: float = 0.05,
    label_a: str = "A",
    label_b: str = "B",
) -> pd.DataFrame:
    """Compare two simulation scenarios using a two-sample t-test.

    Args:
        results_a: 1-D array of metric values from scenario A replications.
        results_b: 1-D array of metric values from scenario B replications.
        alpha: Significance level.
        label_a: Label for scenario A.
        label_b: Label for scenario B.

    Returns:
        DataFrame with columns: scenario, mean, std, ci_lower, ci_upper, n.
    """
    rows = []
    for label, arr in [(label_a, results_a), (label_b, results_b)]:
        arr = np.asarray(arr, dtype=float)
        n = len(arr)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        se = std / np.sqrt(n)
        t_crit = float(stats.t.ppf(1 - alpha / 2, df=n - 1))
        hw = t_crit * se
        rows.append(
            {
                "scenario": label,
                "mean": mean,
                "std": std,
                "ci_lower": mean - hw,
                "ci_upper": mean + hw,
                "n": n,
            }
        )
    return pd.DataFrame(rows)


def paired_crn(
    results_a: FloatArray,
    results_b: FloatArray,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Paired t-test for two CRN-synchronized scenarios.

    Both arrays must have the same length (same seeds used across scenarios).

    Args:
        results_a: 1-D array of metric values from scenario A.
        results_b: 1-D array of metric values from scenario B.
        alpha: Significance level.

    Returns:
        Dict with keys: mean_diff, ci_lower, ci_upper, t_stat, p_value.
    """
    a = np.asarray(results_a, dtype=float)
    b = np.asarray(results_b, dtype=float)
    if len(a) != len(b):
        raise ValueError("CRN arrays must have equal length (paired replications).")
    diff = a - b
    n = len(diff)
    mean_d = float(np.mean(diff))
    se = float(np.std(diff, ddof=1)) / np.sqrt(n)
    t_crit = float(stats.t.ppf(1 - alpha / 2, df=n - 1))
    ttest = stats.ttest_rel(a, b)
    t_stat = float(ttest.statistic)
    p_val = float(ttest.pvalue)
    return {
        "mean_diff": mean_d,
        "ci_lower": mean_d - t_crit * se,
        "ci_upper": mean_d + t_crit * se,
        "t_stat": t_stat,
        "p_value": p_val,
    }
