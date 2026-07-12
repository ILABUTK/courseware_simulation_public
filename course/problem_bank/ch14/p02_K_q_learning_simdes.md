# Problem 14.2 — Q-Learning with the SimDes Gymnasium Environment

**Chapter**: 14 — Reinforcement Learning for Simulation  
**Type**: K (Coding)  
**Difficulty**: ★★★

---

## Background

The `simdes` package provides `simdes.envs.ClinicEnv`, a Gymnasium-compatible environment wrapping the SimPy clinic model.
Q-learning is a model-free, off-policy RL algorithm that estimates the optimal action-value function:

$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]$$

---

## Setup

```python
import gymnasium as gym
import simdes.envs  # registers ClinicEnv
import numpy as np

env = gym.make('simdes/ClinicEnv-v0',
               n_nurses_choices=[1, 2, 3],
               lam=4.0,          # patients/hr
               mu=2.0,           # service rate per nurse
               decision_interval=1.0,  # hours
               max_queue=15,
               nurse_cost=40.0,
               delay_cost=10.0,
               adjust_cost=5.0)
```

The observation is the queue length at decision epochs; the action is the number of nurses to deploy.

---

## Tasks

**(a)** Inspect the environment:

```python
obs, info = env.reset(seed=0)
print("Observation space:", env.observation_space)
print("Action space:     ", env.action_space)
print("Initial obs:      ", obs)
```

What are the shapes and ranges of the observation and action spaces?

**(b)** Implement a tabular $\varepsilon$-greedy Q-learning agent.
Use a $Q$-table of shape `(n_states, n_actions)` initialized to zero.

```python
def q_learning(env, n_episodes=5000, alpha=0.1, gamma=0.95,
               eps_start=1.0, eps_end=0.05, eps_decay=0.995):
    n_states  = env.observation_space.n
    n_actions = env.action_space.n
    Q = np.zeros((n_states, n_actions))
    eps = eps_start
    episode_returns = []

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=ep)
        total_reward = 0.0
        done = False
        while not done:
            # TODO: epsilon-greedy action selection
            # TODO: Q-table update
            pass
        eps = max(eps_end, eps * eps_decay)
        episode_returns.append(total_reward)
    return Q, episode_returns
```

Fill in the two `# TODO` lines.

**(c)** Train the agent for 5000 episodes. Plot the *smoothed* episode return (rolling mean over 200 episodes).
Does the agent converge? At what episode does the rolling mean stabilize?

**(d)** Extract the learned policy $\pi(n) = \arg\max_a Q(n, a)$ for queue lengths $n = 0, 1, \ldots, 15$.
Plot the policy as a step function of queue length.
Describe the policy qualitatively: does the agent deploy more nurses as the queue grows?

**(e)** Compare the learned policy against two heuristics over 100 evaluation episodes (no exploration, fixed seed range 10001–10100):
- **Heuristic 1**: always deploy 1 nurse
- **Heuristic 2**: always deploy 2 nurses
- **Heuristic 3**: use the learned Q-policy

Report mean ± std of total return per episode for each. Is the Q-policy statistically better than Heuristic 2 at $\alpha = 0.05$?

**(f)** *(Bonus)* The ClinicEnv uses a constant arrival rate. Modify the environment to simulate a **time-of-day arrival rate** that is 2× higher from hours 8–12:

```python
def time_varying_lam(t):
    hour = t % 24
    return 8.0 if 8 <= hour < 12 else 4.0
```

Re-train and report whether the learned policy adapts to peak hours.

---

## Notes

- The state must be discretized to an integer index for tabular Q-learning. Use `int(obs)` directly since the observation is already the queue length.
- Clip observations to $[0, n_{\max}]$ to avoid index-out-of-bounds errors.
- Use `env.reset(seed=ep)` for reproducible training; use fixed seeds for evaluation.
