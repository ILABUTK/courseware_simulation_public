"""BaseModel: common interface for all simdes simulation models."""

from __future__ import annotations

import abc
from typing import Any

import numpy as np
import pandas as pd
import simpy

from simdes.trace import Trace


class BaseModel(abc.ABC):
    """Abstract base class for all simdes simulation models.

    Subclasses must implement :meth:`_build` (populate the SimPy environment)
    and :meth:`_collect` (extract performance measures after the run).

    Subclasses that support tracing declare their stations with
    :meth:`_trace_station` in ``_build`` and record movements with
    :meth:`_log`. Both do nothing unless the run was started with
    ``run(trace=True)``.

    Args:
        sim_time: Simulated time horizon for each run.
        seed: Base random seed.  Each replication increments this by one so
            that replications are independent but reproducible.
    """

    time_unit: str = "time units"
    """Unit of simulated time, used to label traces and displays."""

    def __init__(self, sim_time: float, seed: int | None = None) -> None:
        self.sim_time = sim_time
        self.seed = seed
        self._rng: np.random.Generator | None = None
        self._env: simpy.Environment | None = None
        self.trace: Trace | None = None
        self._tracing = False
        self._entity_count = 0

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        """Populate *env* with SimPy processes.  Called once per run."""

    @abc.abstractmethod
    def _collect(self) -> dict[str, Any]:
        """Return a dict of scalar performance measures after the run ends."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *, trace: bool = False) -> dict[str, Any]:
        """Execute one replication and return performance measures.

        Args:
            trace: Record an event trace of this run in :attr:`trace`
                (see :mod:`simdes.trace`). Tracing draws no random numbers,
                so results are identical with or without it.

        Returns:
            dict mapping metric names to scalar values.
        """
        seed = self.seed if self.seed is not None else 0
        self._rng = np.random.default_rng(seed)
        self._env = simpy.Environment()
        self._entity_count = 0
        self._tracing = trace
        self.trace = (
            Trace(
                model=type(self).__name__,
                params=self._trace_params(),
                seed=seed,
                horizon=float(self.sim_time),
                time_unit=self.time_unit,
            )
            if trace
            else None
        )
        self._build(self._env, self._rng)
        self._env.run(until=self.sim_time)
        results = self._collect()
        if self.trace is not None:
            self.trace.results = dict(results)
        self._tracing = False
        return results

    # ------------------------------------------------------------------
    # Tracing helpers for subclasses
    # ------------------------------------------------------------------

    def _trace_params(self) -> dict[str, Any]:
        """Model parameters to store in a trace.

        The default takes the public attributes that are plain numbers,
        strings or booleans. Override it to describe nested parameters.
        """
        skip = {"sim_time", "seed", "trace", "time_unit"}
        return {
            k: v
            for k, v in vars(self).items()
            if not k.startswith("_")
            and k not in skip
            and isinstance(v, int | float | str | bool)
        }

    def _new_entity(self) -> int:
        """Return the next entity identifier (0, 1, 2, ...) for this run."""
        n = self._entity_count
        self._entity_count += 1
        return n

    def _trace_station(
        self, id: str, label: str | None = None, capacity: int = 1
    ) -> None:
        """Declare a station in the trace (no-op when not tracing)."""
        if self.trace is not None:
            self.trace.add_station(id, label, capacity)

    def _log(self, entity: int, type: str, station: str | None = None) -> None:
        """Record an event at the current simulated time (no-op when not tracing)."""
        if self.trace is not None and self._tracing:
            assert self._env is not None
            self.trace.log(self._env.now, entity, type, station)

    def run_replications(self, n: int) -> pd.DataFrame:
        """Execute *n* independent replications.

        Each replication uses seed ``self.seed + i`` so results are
        reproducible but independent.

        Args:
            n: Number of replications.

        Returns:
            DataFrame with one row per replication and one column per metric.
        """
        original_seed = self.seed
        records = []
        for i in range(n):
            self.seed = (original_seed or 0) + i
            records.append(self.run())
        self.seed = original_seed
        return pd.DataFrame(records)
