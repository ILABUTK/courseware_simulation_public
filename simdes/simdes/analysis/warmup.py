"""Warm-up detection using the Welch method."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int_]


def welch_method(
    replications: FloatArray,
    window: int | None = None,
) -> tuple[IntArray, FloatArray]:
    """Apply the Welch graphical method to identify a warm-up period.

    Averages time-series observations across replications, then smooths with a
    moving-average window.  The practitioner inspects the plot and selects the
    deletion point visually.

    Args:
        replications: 2-D array of shape (n_reps, T) where each row is one
            replication's time series of per-observation means (e.g.,
            cumulative average wait at each arrival epoch).
        window: Moving-average half-window *w*; output is smoothed over
            ``2w + 1`` points.  Defaults to ``T // 10``.

    Returns:
        Tuple (t, y_smoothed):
        - ``t``: index array 0 … T-1
        - ``y_smoothed``: smoothed ensemble average

    Example:
        >>> import numpy as np
        >>> rng = np.random.default_rng(0)
        >>> reps = rng.normal(loc=3.0, size=(5, 200))
        >>> t, y = welch_method(reps, window=10)
        >>> len(t) == 200
        True
    """
    arr = np.asarray(replications, dtype=float)
    if arr.ndim == 1:
        arr = arr[np.newaxis, :]
    T = arr.shape[1]
    if window is None:
        window = max(1, T // 10)

    ensemble = arr.mean(axis=0)
    # Moving average via convolution
    kernel = np.ones(2 * window + 1) / (2 * window + 1)
    padded = np.pad(ensemble, window, mode="edge")
    smoothed = np.convolve(padded, kernel, mode="valid")
    return np.arange(T), smoothed
