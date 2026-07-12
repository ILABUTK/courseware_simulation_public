"""TerminalEnv: Gymnasium environment wrapping the terminal simulation.

The agent controls the number of active inspection gates.
Truck arrivals pass through a gate (inspection) stage then a crane (loading)
stage.  At each decision epoch the agent sets how many gates are open; reward
is the negative mean truck total time experienced over that interval.
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


class TerminalEnv(SimPyEnv):
    """Terminal gate staffing control environment.

    The simulation models trucks arriving at an intermodal terminal, queuing
    for gate inspection, then queuing for a yard crane.  The agent decides
    how many gates to staff at each ``decision_interval``-minute epoch.

    Args:
        sim_time: Episode length in minutes (default 480 = 8-hour shift).
        max_gates: Maximum number of inspection gates available.
        decision_interval: Minutes between agent decisions.
        arrival_rate: Truck arrival rate (trucks per hour).
        gate_mean: Mean gate service time (minutes, exponential).
        crane_mean: Mean crane cycle time (minutes, exponential).
        n_cranes: Number of yard cranes (fixed throughout the episode).
        seed: Base random seed.

    Observation (shape ``(4,)``):
        ``[gate_queue_len, crane_queue_len, gate_utilization, time_fraction]``

    Action:
        Integer in ``{0, …, max_gates-1}``; interpreted as ``n_gates = action + 1``.

    Reward:
        Negative mean truck total time (arrival → crane release) over the last
        decision interval.  Returns 0 when no trucks complete in the interval.

    Example:
        >>> env = TerminalEnv(sim_time=480, max_gates=4, seed=0)
        >>> obs, info = env.reset()
        >>> obs.shape
        (4,)
        >>> obs2, reward, terminated, truncated, info = env.step(1)
    """

    def __init__(
        self,
        sim_time: float = 480.0,
        max_gates: int = 6,
        decision_interval: float = 30.0,
        arrival_rate: float = 10.0,
        gate_mean: float = 5.0,
        crane_mean: float = 8.0,
        n_cranes: int = 1,
        seed: int | None = None,
    ) -> None:
        super().__init__(sim_time=sim_time, seed=seed)
        self.max_gates = max_gates
        self.decision_interval = decision_interval
        self.arrival_rate = arrival_rate
        self.gate_mean = gate_mean
        self.crane_mean = crane_mean
        self.n_cranes = n_cranes

        self.observation_space = gym.spaces.Box(
            low=np.zeros(4, dtype=np.float32),
            high=np.array([100.0, 50.0, 1.0, 1.0], dtype=np.float32),
        )
        self.action_space = cast(gym.spaces.Space[int], gym.spaces.Discrete(max_gates))

        # Internal state — populated in _build_sim
        self._gates: simpy.Resource | None = None
        self._cranes_res: simpy.Resource | None = None
        self._interval_waits: list[float] = []
        self._n_gates_active: int = 1

    # ------------------------------------------------------------------
    # SimPy processes
    # ------------------------------------------------------------------

    def _arrivals(self) -> Generator[Any, Any, None]:
        """Generate truck arrivals at exponential inter-arrival times."""
        assert self._env is not None
        assert self._rng is not None
        rate_per_min = self.arrival_rate / 60.0
        while True:
            yield self._env.timeout(self._rng.exponential(1.0 / rate_per_min))
            self._env.process(self._truck())

    def _truck(self) -> Generator[Any, Any, None]:
        """Simulate one truck through gate then crane stages."""
        assert self._env is not None
        assert self._rng is not None
        assert self._gates is not None
        assert self._cranes_res is not None

        t_arrive = self._env.now

        with self._gates.request() as req:
            yield req
            yield self._env.timeout(self._rng.exponential(self.gate_mean))

        with self._cranes_res.request() as req:
            yield req
            yield self._env.timeout(self._rng.exponential(self.crane_mean))

        self._interval_waits.append(self._env.now - t_arrive)

    # ------------------------------------------------------------------
    # SimPyEnv interface
    # ------------------------------------------------------------------

    def _build_sim(self) -> None:
        """Initialise SimPy resources and start the arrivals process."""
        assert self._env is not None
        assert self._rng is not None

        self._interval_waits = []
        self._n_gates_active = 1

        self._gates = simpy.Resource(self._env, capacity=self._n_gates_active)
        self._cranes_res = simpy.Resource(self._env, capacity=self.n_cranes)

        self._env.process(self._arrivals())

    def _get_obs(self) -> ObsArray:
        """Return current [gate_queue, crane_queue, gate_util, time_frac]."""
        if self._env is None or self._gates is None or self._cranes_res is None:
            return np.zeros(4, dtype=np.float32)
        t_frac = min(self._env.now / self.sim_time, 1.0)
        cap = max(1, self._gates.capacity)
        gate_util = float(self._gates.count) / cap
        return np.array(
            [
                float(len(self._gates.queue)),
                float(len(self._cranes_res.queue)),
                gate_util,
                t_frac,
            ],
            dtype=np.float32,
        )

    def _step_sim(self, action: int) -> float:
        """Set gate count, advance simulation by one epoch, return reward."""
        assert self._env is not None
        assert self._gates is not None

        # Map discrete action {0,…,max_gates-1} → n_gates {1,…,max_gates}
        n_gates = max(1, int(action) + 1)

        # Dynamically resize the gate resource
        if n_gates != self._gates._capacity:
            old_cap = int(self._gates._capacity)
            self._gates._capacity = n_gates
            if n_gates > old_cap:
                # Grant pending requests that can now be served
                self._gates._trigger_put(None)
        self._n_gates_active = n_gates

        # Advance the simulation to the next decision epoch
        self._interval_waits = []
        target = min(self._env.now + self.decision_interval, self.sim_time)
        self._env.run(until=target)

        # Reward: negative mean truck total time (lower wait = higher reward)
        reward = (
            -float(np.mean(self._interval_waits))
            if self._interval_waits
            else 0.0
        )
        return reward
