"""Replication runners and batch means."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatArray = npt.NDArray[np.float64]


def run_replications(
    model_factory: Callable[[], Any],
    n: int,
    metric: str | None = None,
) -> pd.DataFrame | FloatArray:
    """Run *n* independent replications of a model returned by *model_factory*.

    Each call to ``model_factory()`` should return a fresh model instance with
    a unique seed.  Use a closure or ``functools.partial`` to vary the seed:

    .. code-block:: python

        from functools import partial
        from simdes.models.queues import MM1Queue

        factory = partial(MM1Queue, arrival_rate=0.8, service_rate=1.0,
                          sim_time=10_000)
        df = run_replications(lambda: factory(seed=i), n=30)

    Prefer :meth:`BaseModel.run_replications` for direct use.  This function
    is useful when the factory handles seed management externally.

    Args:
        model_factory: Callable returning a model instance ready to run.
        n: Number of replications.
        metric: If provided, return a 1-D numpy array of that metric only.

    Returns:
        DataFrame of all metrics, or 1-D array if *metric* is given.
    """
    records = []
    for _ in range(n):
        model = model_factory()
        records.append(model.run())
    df = pd.DataFrame(records)
    if metric is not None:
        return df[metric].to_numpy()
    return df


def batch_means(
    series: FloatArray | list[float],
    n_batches: int = 10,
) -> FloatArray:
    """Split *series* into *n_batches* non-overlapping batches and return means.

    Useful for computing a confidence interval from a single long run under
    the assumption that batch means are approximately independent.

    Args:
        series: 1-D array of sequential observations (e.g., per-customer waits).
        n_batches: Number of batches.  The series is truncated to the largest
            multiple of *n_batches*.

    Returns:
        1-D array of length *n_batches* containing batch means.
    """
    arr = np.asarray(series, dtype=float)
    batch_size = len(arr) // n_batches
    if batch_size == 0:
        raise ValueError(
            f"Series length {len(arr)} is shorter than n_batches={n_batches}."
        )
    trimmed = arr[: batch_size * n_batches]
    return np.asarray(trimmed.reshape(n_batches, batch_size).mean(axis=1), dtype=float)
