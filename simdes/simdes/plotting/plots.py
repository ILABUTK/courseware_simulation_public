"""Plotting functions for simulation analysis."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.axes import Axes

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int_]

# Color-blind-safe palette (Wong 2011)
_CB = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
}


def welch_plot(
    t: IntArray,
    y_smoothed: FloatArray,
    deletion_point: int | None = None,
    ax: Axes | None = None,
    ylabel: str = "Performance measure",
) -> Axes:
    """Plot the Welch smoothed time series for warm-up identification.

    Args:
        t: Index array from :func:`~simdes.analysis.warmup.welch_method`.
        y_smoothed: Smoothed ensemble average.
        deletion_point: If provided, draw a vertical dashed line here.
        ax: Existing Axes to plot on.  Created if None.
        ylabel: Y-axis label.

    Returns:
        The Axes object.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, y_smoothed, color=_CB["blue"], linewidth=1.5)
    if deletion_point is not None:
        ax.axvline(
            deletion_point,
            color=_CB["red"],
            linestyle="--",
            label=f"Delete t < {deletion_point}",
        )
        ax.legend()
    ax.set_xlabel("Observation index")
    ax.set_ylabel(ylabel)
    ax.set_title("Welch Method — Warm-up Identification")
    return ax


def output_hist(
    data: FloatArray,
    metric: str = "metric",
    ax: Axes | None = None,
    ci: tuple[float, float] | None = None,
) -> Axes:
    """Histogram of replication means with optional CI shading.

    Args:
        data: 1-D array of replication means.
        metric: Name of the metric (used in axis label).
        ax: Existing Axes.
        ci: (lower, upper) confidence interval bounds.

    Returns:
        The Axes object.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))
    ax.hist(data, bins="auto", color=_CB["sky"], edgecolor="white", alpha=0.85)
    if ci is not None:
        ax.axvline(
            ci[0],
            color=_CB["red"],
            linestyle="--",
            label=f"CI lower = {ci[0]:.3f}",
        )
        ax.axvline(
            ci[1],
            color=_CB["red"],
            linestyle=":",
            label=f"CI upper = {ci[1]:.3f}",
        )
        ax.axvline(
            float(np.mean(data)),
            color=_CB["blue"],
            linewidth=2,
            label=f"Mean = {np.mean(data):.3f}",
        )
        ax.legend(fontsize=8)
    ax.set_xlabel(metric)
    ax.set_ylabel("Count")
    return ax


def scenario_bars(
    df: Any,  # pd.DataFrame from compare_scenarios
    metric: str = "mean",
    ax: Axes | None = None,
) -> Axes:
    """Bar chart comparing scenarios with CI error bars.

    Args:
        df: Output of :func:`~simdes.analysis.scenarios.compare_scenarios`.
        metric: Column to plot (default ``"mean"``).
        ax: Existing Axes.

    Returns:
        The Axes object.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))
    scenarios = df["scenario"].tolist()
    means = df["mean"].to_numpy()
    lower_err = (means - df["ci_lower"].to_numpy())
    upper_err = (df["ci_upper"].to_numpy() - means)
    colors = [_CB["blue"], _CB["orange"], _CB["green"], _CB["purple"]]
    ax.bar(
        scenarios,
        means,
        yerr=[lower_err, upper_err],
        color=[colors[i % len(colors)] for i in range(len(scenarios))],
        capsize=5,
        width=0.5,
    )
    ax.set_ylabel(metric)
    ax.set_title("Scenario Comparison (95% CI)")
    return ax


def crn_plot(
    results_a: FloatArray,
    results_b: FloatArray,
    label_a: str = "A",
    label_b: str = "B",
    ax: Axes | None = None,
) -> Axes:
    """Scatter plot of paired CRN replication values.

    Points above the diagonal indicate B > A for that replication.

    Args:
        results_a: Replication values for scenario A.
        results_b: Replication values for scenario B.
        label_a: Label for scenario A.
        label_b: Label for scenario B.
        ax: Existing Axes.

    Returns:
        The Axes object.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))
    a, b = np.asarray(results_a), np.asarray(results_b)
    ax.scatter(a, b, color=_CB["blue"], alpha=0.7, s=30, edgecolors="white")
    lims = [min(a.min(), b.min()), max(a.max(), b.max())]
    ax.plot(lims, lims, "k--", linewidth=1, alpha=0.5)
    ax.set_xlabel(f"Scenario {label_a}")
    ax.set_ylabel(f"Scenario {label_b}")
    ax.set_title("CRN Paired Replications")
    return ax
