"""SSInventoryEnv: Gymnasium environment for (s,S) inventory control.

The agent selects the reorder point s and order-up-to level S at each
review epoch.  The reward is negative total cost (holding + backorder).
"""

from __future__ import annotations

from typing import cast

import gymnasium as gym
import numpy as np
import numpy.typing as npt

from simdes.envs.base_env import SimPyEnv

ObsArray = npt.NDArray[np.float32]


class SSInventoryEnv(SimPyEnv):
    """(s, S) inventory control environment.

    Observation: [inventory_level, pending_order (0/1), time_fraction]
    Action:      Discrete — index into a predefined grid of (s, S) pairs
    Reward:      -(holding_cost + backorder_cost) over the decision interval

    Args:
        capacity: Maximum inventory capacity (= S upper bound).
        holding_cost: Cost per unit per time.
        backorder_cost: Shortage cost per unit per time.
        demand_rate: Poisson demand arrival rate.
        sim_time: Episode horizon.
        seed: Base random seed.
    """

    def __init__(
        self,
        capacity: float = 50.0,
        holding_cost: float = 1.0,
        backorder_cost: float = 10.0,
        demand_rate: float = 2.0,
        sim_time: float = 500.0,
        seed: int | None = None,
    ) -> None:
        super().__init__(sim_time=sim_time, seed=seed)
        self.capacity = capacity
        self.holding_cost = holding_cost
        self.backorder_cost = backorder_cost
        self.demand_rate = demand_rate

        self.observation_space = gym.spaces.Box(
            low=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([capacity, 1.0, 1.0], dtype=np.float32),
        )
        # Action: choose reorder point as a fraction of capacity (10 levels)
        self.action_space = cast(gym.spaces.Space[int], gym.spaces.Discrete(10))

    def _build_sim(self) -> None:
        pass  # TODO: implement with SimPy Container and event stepping

    def _get_obs(self) -> ObsArray:
        return np.zeros(3, dtype=np.float32)

    def _step_sim(self, action: int) -> float:
        return 0.0
