"""Unit tests for Gymnasium environments: reset/step contract.

Skipped automatically if gymnasium is not installed (it is an optional
dependency; gymnasium is always present inside Docker).
"""

import numpy as np
import pytest

gymnasium = pytest.importorskip("gymnasium", reason="gymnasium not installed")

from simdes.envs.clinic_env import ClinicEnv
from simdes.envs.inventory_env import SSInventoryEnv
from simdes.envs.terminal_env import TerminalEnv


class TestClinicEnv:
    def test_reset_returns_observation(self):
        env = ClinicEnv(sim_time=480, max_nurses=3, seed=0)
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray)
        assert obs.shape == env.observation_space.shape

    def test_observation_in_space(self):
        env = ClinicEnv(sim_time=480, max_nurses=3, seed=0)
        obs, _ = env.reset()
        assert env.observation_space.contains(obs)

    def test_step_returns_correct_types(self):
        env = ClinicEnv(sim_time=480, max_nurses=3, seed=0)
        env.reset()
        obs, reward, terminated, truncated, info = env.step(1)
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_action_space_valid(self):
        env = ClinicEnv(sim_time=480, max_nurses=4, seed=0)
        assert env.action_space.n == 4

    def test_full_episode_terminates(self):
        env = ClinicEnv(sim_time=120, max_nurses=3, decision_interval=30.0, seed=1)
        obs, _ = env.reset()
        terminated = False
        steps = 0
        while not terminated and steps < 100:
            obs, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            steps += 1
        assert terminated, "episode should terminate within sim_time"

    def test_more_nurses_improves_reward(self):
        """More nurses should yield lower (less negative) mean triage wait."""
        rewards_few, rewards_many = [], []
        for seed in range(5):
            for nurses, bucket in ((0, rewards_few), (3, rewards_many)):
                env = ClinicEnv(
                    sim_time=480, max_nurses=4, decision_interval=30.0, seed=seed
                )
                obs, _ = env.reset()
                ep_reward = 0.0
                terminated = False
                while not terminated:
                    obs, r, terminated, _, _ = env.step(nurses)
                    ep_reward += r
                bucket.append(ep_reward)
        assert np.mean(rewards_many) > np.mean(rewards_few), (
            "4 nurses should outperform 1 nurse on average"
        )


class TestSSInventoryEnv:
    def test_reset(self):
        env = SSInventoryEnv(sim_time=500, seed=0)
        obs, info = env.reset()
        assert obs.shape == env.observation_space.shape

    def test_step(self):
        env = SSInventoryEnv(sim_time=500, seed=0)
        env.reset()
        obs, reward, terminated, truncated, info = env.step(3)
        assert isinstance(reward, float)


class TestTerminalEnv:
    def test_reset_returns_observation(self):
        env = TerminalEnv(sim_time=480, max_gates=4, seed=0)
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray)
        assert obs.shape == env.observation_space.shape

    def test_observation_in_space(self):
        env = TerminalEnv(sim_time=480, max_gates=4, seed=0)
        obs, _ = env.reset()
        assert env.observation_space.contains(obs)

    def test_step_returns_correct_types(self):
        env = TerminalEnv(sim_time=480, max_gates=4, seed=0)
        env.reset()
        obs, reward, terminated, truncated, info = env.step(1)
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_action_space_matches_max_gates(self):
        env = TerminalEnv(sim_time=480, max_gates=5, seed=0)
        assert env.action_space.n == 5

    def test_more_gates_improves_reward(self):
        """Reward (negative mean time) should be less negative with more gates."""
        rewards_few, rewards_many = [], []
        for seed in range(8):
            env = TerminalEnv(sim_time=480, max_gates=6, seed=seed)
            # 1 gate policy
            obs, _ = env.reset()
            r, done = 0.0, False
            while not done:
                obs, rew, done, _, _ = env.step(0)
                r += rew
            rewards_few.append(r)
            # 4 gates policy
            obs, _ = env.reset()
            r, done = 0.0, False
            while not done:
                obs, rew, done, _, _ = env.step(3)
                r += rew
            rewards_many.append(r)
        assert np.mean(rewards_many) > np.mean(rewards_few)

    def test_full_episode_terminates(self):
        env = TerminalEnv(sim_time=120, max_gates=3, seed=1)
        obs, _ = env.reset()
        terminated = False
        steps = 0
        while not terminated:
            obs, _, terminated, _, _ = env.step(1)
            steps += 1
        assert steps > 0
        assert float(obs[3]) == pytest.approx(1.0, abs=0.01)  # time_fraction ≈ 1
