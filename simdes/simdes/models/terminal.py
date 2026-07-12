"""TerminalModel: intermodal container terminal gate simulation.

Truck arrivals are processed at inspection gates, then directed to
a yard crane for container pickup/dropoff.  Used as the second running
case study across Modules M05–M12.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import simpy

from simdes.core.model import BaseModel


@dataclass
class TerminalParams:
    """Configuration parameters for the terminal model.

    Args:
        n_gates: Number of inspection / processing gates.
        n_cranes: Number of yard cranes.
        arrival_rate: Truck arrival rate (per hour).
        gate_mean: Mean gate processing time (minutes, exponential).
        crane_mean: Mean crane cycle time (minutes, exponential).
        sim_time: Simulation time (hours).
    """

    n_gates: int = 2
    n_cranes: int = 1
    arrival_rate: float = 10.0        # trucks per hour
    gate_mean: float = 5.0            # minutes
    crane_mean: float = 8.0           # minutes
    sim_time: float = 8.0             # hours (will be converted internally to minutes)


class TerminalModel(BaseModel):
    """Intermodal terminal gate and crane simulation.

    Args:
        params: :class:`TerminalParams` configuration.
        seed: Base random seed.

    Example:
        >>> p = TerminalParams(n_gates=3, n_cranes=2)
        >>> m = TerminalModel(params=p, seed=0)
        >>> result = m.run()
        >>> "mean_total_time" in result
        True
    """

    def __init__(
        self,
        params: TerminalParams | None = None,
        seed: int | None = None,
    ) -> None:
        params = params or TerminalParams()
        super().__init__(sim_time=params.sim_time * 60, seed=seed)  # hours → minutes
        self.params = params
        self._total_times: list[float] = []
        self._wait_gate: list[float] = []
        self._wait_crane: list[float] = []

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        self._total_times = []
        self._wait_gate = []
        self._wait_crane = []
        p = self.params
        gates = simpy.Resource(env, capacity=p.n_gates)
        cranes = simpy.Resource(env, capacity=p.n_cranes)
        env.process(self._arrivals(env, rng, gates, cranes))

    def _arrivals(
        self,
        env: simpy.Environment,
        rng: np.random.Generator,
        gates: simpy.Resource,
        cranes: simpy.Resource,
    ) -> Any:
        p = self.params
        rate_per_min = p.arrival_rate / 60.0
        while True:
            yield env.timeout(rng.exponential(1.0 / rate_per_min))
            env.process(self._truck(env, rng, gates, cranes))

    def _truck(
        self,
        env: simpy.Environment,
        rng: np.random.Generator,
        gates: simpy.Resource,
        cranes: simpy.Resource,
    ) -> Any:
        p = self.params
        t0 = env.now
        with gates.request() as req:
            yield req
            self._wait_gate.append(env.now - t0)
            yield env.timeout(rng.exponential(p.gate_mean))

        t1 = env.now
        with cranes.request() as req:
            yield req
            self._wait_crane.append(env.now - t1)
            yield env.timeout(rng.exponential(p.crane_mean))

        self._total_times.append(env.now - t0)

    def _collect(self) -> dict[str, Any]:
        def _mean(lst: list[float]) -> float:
            return float(np.mean(lst)) if lst else float("nan")

        return {
            "mean_total_time": _mean(self._total_times),
            "mean_wait_gate": _mean(self._wait_gate),
            "mean_wait_crane": _mean(self._wait_crane),
            "n_trucks": len(self._total_times),
        }
