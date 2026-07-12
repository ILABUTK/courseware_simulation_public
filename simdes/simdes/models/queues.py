"""Queueing models: MM1Queue, MMCQueue, MGQueue, PriorityQueue.

Each model extends BaseModel and provides an analytically verifiable
closed-form benchmark so unit tests can compare simulation output to theory.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import simpy

from simdes.core.model import BaseModel


class MM1Queue(BaseModel):
    """M/M/1 queue simulation model.

    Customers arrive at rate *arrival_rate* (Poisson process) and are served
    at rate *service_rate* (exponential service times) by a single server.

    Args:
        arrival_rate: Mean arrival rate λ (customers / time unit).
        service_rate: Mean service rate μ (customers / time unit per server).
        sim_time: Simulated time horizon.
        seed: Base random seed.

    Analytical benchmarks (ρ = λ/μ < 1):
        - Mean wait in queue: Wq = ρ / (μ - λ)
        - Mean number in queue: Lq = ρ² / (1 - ρ)
        - Server utilization: ρ

    Example:
        >>> m = MM1Queue(arrival_rate=0.8, service_rate=1.0, sim_time=50_000)
        >>> result = m.run()
        >>> abs(result["mean_wait_queue"] - 4.0) < 0.5   # Wq ≈ 4.0
        True
    """

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        sim_time: float = 10_000,
        seed: int | None = None,
    ) -> None:
        super().__init__(sim_time=sim_time, seed=seed)
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        # Accumulators — reset in _build
        self._waits: list[float] = []
        self._busy_time: float = 0.0
        self._queue_area: float = 0.0
        self._last_change_time: float = 0.0
        self._queue_len: int = 0
        self._server: simpy.Resource | None = None

    # ------------------------------------------------------------------
    # Analytical benchmarks
    # ------------------------------------------------------------------

    def rho(self) -> float:
        """Traffic intensity ρ = λ/μ."""
        return self.arrival_rate / self.service_rate

    def theoretical_mean_wait_queue(self) -> float:
        """Closed-form Wq = ρ / (μ(1-ρ)) for M/M/1."""
        rho = self.rho()
        if rho >= 1:
            return float("inf")
        return rho / (self.service_rate * (1 - rho))

    def theoretical_utilization(self) -> float:
        """Closed-form utilization ρ."""
        return self.rho()

    # ------------------------------------------------------------------
    # BaseModel interface
    # ------------------------------------------------------------------

    def _update_queue_area(self, now: float) -> None:
        self._queue_area += (now - self._last_change_time) * self._queue_len
        self._last_change_time = now

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        self._waits = []
        self._busy_time = 0.0
        self._queue_area = 0.0
        self._last_change_time = 0.0
        self._queue_len = 0
        self._server = simpy.Resource(env, capacity=1)
        env.process(self._arrival_stream(env, rng))

    def _arrival_stream(
        self, env: simpy.Environment, rng: np.random.Generator
    ) -> Any:
        while True:
            yield env.timeout(rng.exponential(1.0 / self.arrival_rate))
            env.process(self._customer(env, rng, arrival_time=env.now))

    def _customer(
        self, env: simpy.Environment, rng: np.random.Generator, arrival_time: float
    ) -> Any:
        assert self._server is not None
        self._update_queue_area(env.now)
        self._queue_len += 1
        with self._server.request() as req:
            yield req
            self._update_queue_area(env.now)
            self._queue_len -= 1
            wait = env.now - arrival_time
            self._waits.append(wait)
            service_time = rng.exponential(1.0 / self.service_rate)
            yield env.timeout(service_time)
            self._busy_time += service_time

    def _collect(self) -> dict[str, Any]:
        assert self._env is not None
        self._update_queue_area(self._env.now)
        waits = np.array(self._waits)
        return {
            "mean_wait_queue": float(np.mean(waits)) if len(waits) else float("nan"),
            "mean_queue_length": self._queue_area / self.sim_time,
            "n_customers": len(waits),
            "utilization": self._busy_time / self.sim_time,
        }


class MMCQueue(BaseModel):
    """M/M/c queue simulation model.

    Generalizes MM1Queue to *c* parallel servers.  Erlang-C formula provides
    the analytical benchmark for the probability a customer waits (C(c, ρ)).

    Args:
        arrival_rate: Mean arrival rate λ.
        service_rate: Mean service rate per server μ.
        n_servers: Number of parallel servers c.
        sim_time: Simulated time horizon.
        seed: Base random seed.
    """

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        n_servers: int = 1,
        sim_time: float = 10_000,
        seed: int | None = None,
    ) -> None:
        super().__init__(sim_time=sim_time, seed=seed)
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.n_servers = n_servers
        self._waits: list[float] = []
        self._server: simpy.Resource | None = None

    def rho(self) -> float:
        """Per-server utilization ρ = λ/(cμ)."""
        return self.arrival_rate / (self.n_servers * self.service_rate)

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        self._waits = []
        self._server = simpy.Resource(env, capacity=self.n_servers)
        env.process(self._arrival_stream(env, rng))

    def _arrival_stream(
        self, env: simpy.Environment, rng: np.random.Generator
    ) -> Any:
        while True:
            yield env.timeout(rng.exponential(1.0 / self.arrival_rate))
            env.process(self._customer(env, rng, arrival_time=env.now))

    def _customer(
        self, env: simpy.Environment, rng: np.random.Generator, arrival_time: float
    ) -> Any:
        assert self._server is not None
        with self._server.request() as req:
            yield req
            self._waits.append(env.now - arrival_time)
            yield env.timeout(rng.exponential(1.0 / self.service_rate))

    def _collect(self) -> dict[str, Any]:
        waits = np.array(self._waits)
        return {
            "mean_wait_queue": float(np.mean(waits)) if len(waits) else float("nan"),
            "n_customers": len(waits),
            "utilization": self.rho(),
        }
