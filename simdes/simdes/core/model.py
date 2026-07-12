"""BaseModel: common interface for all simdes simulation models."""

from __future__ import annotations

import abc
from typing import Any

import numpy as np
import pandas as pd
import simpy


class BaseModel(abc.ABC):
    """Abstract base class for all simdes simulation models.

    Subclasses must implement :meth:`_build` (populate the SimPy environment)
    and :meth:`_collect` (extract performance measures after the run).

    Args:
        sim_time: Simulated time horizon for each run.
        seed: Base random seed.  Each replication increments this by one so
            that replications are independent but reproducible.
    """

    def __init__(self, sim_time: float, seed: int | None = None) -> None:
        self.sim_time = sim_time
        self.seed = seed
        self._rng: np.random.Generator | None = None
        self._env: simpy.Environment | None = None

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

    def run(self) -> dict[str, Any]:
        """Execute one replication and return performance measures.

        Returns:
            dict mapping metric names to scalar values.
        """
        seed = self.seed if self.seed is not None else 0
        self._rng = np.random.default_rng(seed)
        self._env = simpy.Environment()
        self._build(self._env, self._rng)
        self._env.run(until=self.sim_time)
        return self._collect()

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
