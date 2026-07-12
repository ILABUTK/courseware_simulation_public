"""Abstract SimPyEnv base class for all Gymnasium wrappers."""

from __future__ import annotations

import abc
from typing import Any

import gymnasium as gym
import numpy as np
import numpy.typing as npt
import simpy

ObsArray = npt.NDArray[np.float32]


class SimPyEnv(gym.Env[ObsArray, int], abc.ABC):
    """Abstract base for SimPy-backed Gymnasium environments.

    Subclasses implement :meth:`_build_sim` (construct the SimPy model),
    :meth:`_get_obs` (return current observation), and :meth:`_step_sim`
    (advance the simulation by one decision epoch and return reward).

    The episode runs until the SimPy environment reaches ``sim_time`` or a
    terminal condition is flagged by :meth:`_is_done`.

    Args:
        sim_time: Simulated time horizon per episode.
        seed: Random seed for reproducibility.
    """

    metadata: dict[str, Any] = {"render_modes": []}

    def __init__(self, sim_time: float = 480.0, seed: int | None = None) -> None:
        super().__init__()
        self.sim_time = sim_time
        self._base_seed = seed
        self._env: simpy.Environment | None = None
        self._rng: np.random.Generator | None = None
        self._episode_seed: int = seed or 0

    # ------------------------------------------------------------------
    # Abstract interface for subclasses
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def _build_sim(self) -> None:
        """Construct SimPy processes.  Called once per :meth:`reset`."""

    @abc.abstractmethod
    def _get_obs(self) -> ObsArray:
        """Return the current observation vector."""

    @abc.abstractmethod
    def _step_sim(self, action: int) -> float:
        """Apply *action*, advance simulation, and return scalar reward."""

    def _is_done(self) -> bool:
        """Return True when the episode should terminate."""
        assert self._env is not None
        return self._env.now >= self.sim_time

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[ObsArray, dict[str, Any]]:
        super().reset(seed=seed)
        self._episode_seed = seed if seed is not None else self._episode_seed + 1
        self._rng = np.random.default_rng(self._episode_seed)
        self._env = simpy.Environment()
        self._build_sim()
        return self._get_obs(), {}

    def step(
        self, action: int
    ) -> tuple[ObsArray, float, bool, bool, dict[str, Any]]:
        reward = self._step_sim(action)
        obs = self._get_obs()
        terminated = self._is_done()
        return obs, reward, terminated, False, {}

    def render(self) -> None:
        pass
