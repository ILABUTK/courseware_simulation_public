"""ClinicEnv: Gymnasium environment wrapping the clinic simulation.

The agent controls how many nurses are active at each decision epoch.
The reward penalizes mean patient waiting time in the triage queue.

Observation: [queue_length_registration, queue_length_triage, queue_length_exam,
              utilization_nurses (fraction), simulated_time_fraction]
Action:      integer in [0, max_nurses-1] — maps to (action+1) active triage nurses
Reward:      -mean_wait_triage over the last decision interval
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast

import gymnasium as gym
import numpy as np
import numpy.typing as npt
import simpy

from simdes.envs.base_env import SimPyEnv

ObsArray = npt.NDArray[np.float32]


class ClinicEnv(SimPyEnv):
    """Clinic staffing control environment.

    Three-stage pipeline: registration (1 clerk) → triage (agent-controlled nurses)
    → exam (2 rooms). The agent sets the number of triage nurses each interval.

    Args:
        sim_time: Episode length in minutes (default 480 = 8-hour day).
        max_nurses: Maximum number of triage nurses the agent can deploy.
        decision_interval: Minutes between agent decisions.
        arrival_rate: Mean patient arrivals per minute (default 5/60 ≈ 0.083).
        reg_mean: Mean registration service time in minutes (default 3.0).
        triage_mean: Mean triage service time in minutes (default 8.0).
        exam_mean: Mean exam service time in minutes (default 15.0).
        seed: Base random seed.

    Example:
        >>> env = ClinicEnv(sim_time=480, max_nurses=4, seed=0)
        >>> obs, info = env.reset()
        >>> obs.shape
        (5,)
        >>> obs2, reward, terminated, truncated, info = env.step(2)
    """

    def __init__(
        self,
        sim_time: float = 480.0,
        max_nurses: int = 4,
        decision_interval: float = 30.0,
        arrival_rate: float = 5.0 / 60.0,
        reg_mean: float = 3.0,
        triage_mean: float = 8.0,
        exam_mean: float = 15.0,
        seed: int | None = None,
    ) -> None:
        super().__init__(sim_time=sim_time, seed=seed)
        self.max_nurses = max_nurses
        self.decision_interval = decision_interval
        self.arrival_rate = arrival_rate
        self.reg_mean = reg_mean
        self.triage_mean = triage_mean
        self.exam_mean = exam_mean

        self.observation_space = gym.spaces.Box(
            low=np.zeros(5, dtype=np.float32),
            high=np.array([50, 50, 50, 1.0, 1.0], dtype=np.float32),
        )
        self.action_space = cast(
            gym.spaces.Space[int],
            gym.spaces.Discrete(max_nurses),
        )

        # Internal state — populated in _build_sim
        self._reg_queue: int = 0
        self._triage_queue: int = 0
        self._exam_queue: int = 0
        self._nurse_util: float = 0.0
        self._interval_waits: list[float] = []
        self._n_nurses_active: int = 1

        # Resources — created in _build_sim after SimPy env exists
        self._reg_server: simpy.Resource | None = None
        self._nurses: simpy.Resource | None = None
        self._exam_rooms: simpy.Resource | None = None

    def _build_sim(self) -> None:
        """Create SimPy resources and start the arrivals process."""
        assert self._env is not None
        self._reg_server = simpy.Resource(self._env, capacity=1)
        self._nurses = simpy.Resource(self._env, capacity=1)
        self._exam_rooms = simpy.Resource(self._env, capacity=2)
        self._reg_queue = 0
        self._triage_queue = 0
        self._exam_queue = 0
        self._nurse_util = 0.0
        self._interval_waits = []
        self._n_nurses_active = 1
        self._env.process(self._arrivals())

    def _arrivals(self) -> Generator[Any, Any, None]:
        """Generate patient arrivals (Poisson process)."""
        assert self._env is not None and self._rng is not None
        while self._env.now < self.sim_time:
            iat = self._rng.exponential(1.0 / self.arrival_rate)
            yield self._env.timeout(iat)
            if self._env.now < self.sim_time:
                self._env.process(self._patient())

    def _patient(self) -> Generator[Any, Any, None]:
        """Three-stage patient service process: registration → triage → exam."""
        assert self._env is not None and self._rng is not None
        assert self._reg_server is not None
        assert self._nurses is not None
        assert self._exam_rooms is not None

        # Stage 1: Registration
        self._reg_queue += 1
        with self._reg_server.request() as req:
            yield req
            self._reg_queue -= 1
            yield self._env.timeout(self._rng.exponential(self.reg_mean))

        # Stage 2: Triage (nurse — capacity controlled by agent)
        self._triage_queue += 1
        arrive_triage = self._env.now
        with self._nurses.request() as req:
            yield req
            self._triage_queue -= 1
            self._interval_waits.append(self._env.now - arrive_triage)
            yield self._env.timeout(self._rng.exponential(self.triage_mean))

        # Stage 3: Exam room
        self._exam_queue += 1
        with self._exam_rooms.request() as req:
            yield req
            self._exam_queue -= 1
            yield self._env.timeout(self._rng.exponential(self.exam_mean))

    def _get_obs(self) -> ObsArray:
        t_frac = (self._env.now / self.sim_time) if self._env else 0.0
        if self._nurses is not None:
            self._nurse_util = self._nurses.count / max(1, self._nurses.capacity)
        return np.array(
            [
                self._reg_queue,
                self._triage_queue,
                self._exam_queue,
                self._nurse_util,
                min(t_frac, 1.0),
            ],
            dtype=np.float32,
        )

    def _step_sim(self, action: int) -> float:
        """Set active nurse count and advance simulation by one decision interval."""
        assert self._env is not None
        assert self._nurses is not None

        # Update nurse capacity based on action (action 0 → 1 nurse, etc.)
        n_nurses = max(1, int(action) + 1)
        self._nurses._capacity = n_nurses
        self._nurses._trigger_put(None)  # grant any waiting triage requests
        self._n_nurses_active = n_nurses

        # Advance simulation to next decision point
        target = min(self._env.now + self.decision_interval, self.sim_time)
        self._env.run(until=target)

        # Reward = negative mean triage wait over this interval
        reward = -float(np.mean(self._interval_waits)) if self._interval_waits else 0.0
        self._interval_waits = []
        return reward

    def _is_done(self) -> bool:
        assert self._env is not None
        return self._env.now >= self.sim_time
