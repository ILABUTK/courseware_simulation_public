"""Confidence intervals that also run in the browser.

The web app's static mode runs this package in Pyodide, where SciPy would add
a large download. So the Student t quantile is computed here from the
regularized incomplete beta function (NumPy and the standard library only).
``tests/test_stats.py`` checks it against SciPy and against
``simdes.analysis.ci.confidence_interval``, which the experiment scripts use.
"""

from __future__ import annotations

import math
from collections.abc import Iterable


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    """Cumulative distribution function of Student's t with ``df`` degrees of freedom."""
    x = df / (df + t * t)
    tail = 0.5 * _betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """Quantile of Student's t (inverse of :func:`t_cdf`), by bisection."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    if p == 0.5:
        return 0.0
    if p < 0.5:
        return -t_quantile(1.0 - p, df)
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12:
            break
    return 0.5 * (lo + hi)


def mean_ci(values: Iterable[float], alpha: float = 0.05) -> dict[str, float | int | None]:
    """Mean and two-sided t confidence interval of independent replication results.

    NaN values are dropped. With fewer than two values the interval is None.

    Returns:
        ``{"mean", "low", "high", "half_width", "sd", "n"}``.
    """
    data = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    n = len(data)
    if n == 0:
        return {"mean": None, "low": None, "high": None, "half_width": None, "sd": None, "n": 0}
    mean = sum(data) / n
    if n < 2:
        return {"mean": mean, "low": None, "high": None, "half_width": None, "sd": None, "n": 1}
    sd = math.sqrt(sum((v - mean) ** 2 for v in data) / (n - 1))
    half = t_quantile(1.0 - alpha / 2.0, n - 1) * sd / math.sqrt(n)
    return {
        "mean": mean, "low": mean - half, "high": mean + half, "half_width": half, "sd": sd,
        "n": n,
    }


def paired_ci(
    a: Iterable[float], b: Iterable[float], alpha: float = 0.05
) -> dict[str, float | int | None]:
    """Confidence interval for the mean of ``b - a`` over paired replications (CRN).

    Pairs where either value is NaN are dropped.
    """
    diffs = [
        float(y) - float(x)
        for x, y in zip(a, b, strict=True)
        if x is not None and y is not None and not math.isnan(float(x)) and not math.isnan(float(y))
    ]
    return mean_ci(diffs, alpha)
