"""ClinicModel: multi-stage healthcare simulation.

Models a primary care clinic with a registration desk, triage nurse,
and examination rooms.  Used as the running case study across Modules M05–M12.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import simpy

from simdes.core.model import BaseModel


@dataclass
class ClinicParams:
    """Configuration parameters for the clinic model.

    Args:
        n_registration: Number of registration clerks.
        n_nurses: Number of triage nurses.
        n_exam_rooms: Number of examination rooms / doctors.
        arrival_rate: Patient arrival rate (per minute).
        reg_mean: Mean registration time (minutes, exponential).
        triage_mean: Mean triage time (minutes, exponential).
        exam_mean: Mean examination time (minutes, exponential).
        sim_time: Clinic operating hours (minutes).
    """

    n_registration: int = 1
    n_nurses: int = 1
    n_exam_rooms: int = 2
    arrival_rate: float = 5.0 / 60.0   # 5 patients/hour → per minute
    reg_mean: float = 3.0
    triage_mean: float = 8.0
    exam_mean: float = 15.0
    sim_time: float = 480.0            # 8-hour day


class ClinicModel(BaseModel):
    """Multi-stage clinic simulation.

    Args:
        params: :class:`ClinicParams` configuration.
        seed: Base random seed.

    Example:
        >>> p = ClinicParams(n_nurses=2, sim_time=480)
        >>> m = ClinicModel(params=p, seed=0)
        >>> result = m.run()
        >>> "mean_total_time" in result
        True
    """

    def __init__(
        self,
        params: ClinicParams | None = None,
        seed: int | None = None,
    ) -> None:
        params = params or ClinicParams()
        super().__init__(sim_time=params.sim_time, seed=seed)
        self.params = params
        self._total_times: list[float] = []
        self._wait_reg: list[float] = []
        self._wait_triage: list[float] = []
        self._wait_exam: list[float] = []

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        self._total_times = []
        self._wait_reg = []
        self._wait_triage = []
        self._wait_exam = []
        p = self.params
        registration = simpy.Resource(env, capacity=p.n_registration)
        triage = simpy.Resource(env, capacity=p.n_nurses)
        exam = simpy.Resource(env, capacity=p.n_exam_rooms)
        env.process(self._arrivals(env, rng, registration, triage, exam))

    def _arrivals(
        self,
        env: simpy.Environment,
        rng: np.random.Generator,
        registration: simpy.Resource,
        triage: simpy.Resource,
        exam: simpy.Resource,
    ) -> Any:
        p = self.params
        while True:
            yield env.timeout(rng.exponential(1.0 / p.arrival_rate))
            env.process(self._patient(env, rng, registration, triage, exam))

    def _patient(
        self,
        env: simpy.Environment,
        rng: np.random.Generator,
        registration: simpy.Resource,
        triage: simpy.Resource,
        exam: simpy.Resource,
    ) -> Any:
        p = self.params
        t0 = env.now

        # Registration
        with registration.request() as req:
            yield req
            self._wait_reg.append(env.now - t0)
            yield env.timeout(rng.exponential(p.reg_mean))

        # Triage
        t1 = env.now
        with triage.request() as req:
            yield req
            self._wait_triage.append(env.now - t1)
            yield env.timeout(rng.exponential(p.triage_mean))

        # Examination
        t2 = env.now
        with exam.request() as req:
            yield req
            self._wait_exam.append(env.now - t2)
            yield env.timeout(rng.exponential(p.exam_mean))

        self._total_times.append(env.now - t0)

    def _collect(self) -> dict[str, Any]:
        def _mean(lst: list[float]) -> float:
            return float(np.mean(lst)) if lst else float("nan")

        return {
            "mean_total_time": _mean(self._total_times),
            "mean_wait_registration": _mean(self._wait_reg),
            "mean_wait_triage": _mean(self._wait_triage),
            "mean_wait_exam": _mean(self._wait_exam),
            "n_patients": len(self._total_times),
        }
