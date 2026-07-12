# Problem 14.1 — MDP Formulation for a Queuing System

**Chapter**: 14 — Reinforcement Learning for Simulation  
**Type**: A (Analytical)  
**Difficulty**: ★★

---

## Background

A Markov Decision Process (MDP) is defined by the tuple $(\mathcal{S}, \mathcal{A}, P, R, \gamma)$:

- $\mathcal{S}$: state space
- $\mathcal{A}$: action space
- $P(s' \mid s, a)$: transition probability
- $R(s, a)$: expected immediate reward
- $\gamma \in [0, 1)$: discount factor

A DES system is natural to cast as an MDP when decisions are made at event times.

---

## Scenario

A hospital triage unit operates with $c \in \{1, 2, 3\}$ nurses, which can be adjusted once per hour.
- Patients arrive at rate $\lambda = 4$/hr.
- Each nurse serves at rate $\mu = 2$/hr.
- Nurse cost: \$40/hr per active nurse.
- Delay penalty: \$10 per patient-hour spent waiting in queue.
- Adjustment cost: \$5 per staffing change (absolute change in $c$).

At the beginning of each hour, the supervisor observes the queue length $n \in \{0, 1, 2, \ldots\}$ and chooses $c'$ for the next hour.

---

## Tasks

**(a)** Define the state space $\mathcal{S}$ for this MDP. Justify why the queue length $n$ (observed at decision epochs) is a sufficient Markov state — i.e., that knowing $n$ makes the future independent of how $n$ was reached.

**(b)** Define the action space $\mathcal{A}$ and identify the constraint that $c' \in \{1, 2, 3\}$.

**(c)** Write the reward function $R(n, c, c')$ for choosing $c'$ when the current queue is $n$ and the expiring staffing level is $c$.  
Include: nurse cost, expected delay penalty during the next hour, and adjustment cost.  
Assume the delay penalty approximates the queue as M/M/$c'$ in steady state.

**(d)** The Bellman optimality equation for discounted infinite-horizon MDPs is:

$$V^*(s) = \max_{a \in \mathcal{A}} \left[ R(s, a) + \gamma \sum_{s'} P(s' \mid s, a) V^*(s') \right]$$

With $\gamma = 0.95$ and states truncated at $n_{\max} = 15$, identify what $P(s' \mid s, a)$ represents in this problem.
(You do not need to compute it — describe the distribution family and its parameters.)

**(e)** Explain why the Gymnasium `SimDesEnv` environment (from the `simdes.envs` module) is preferable to solving the Bellman equation analytically for this problem when arrival rates are non-stationary (time-of-day variation).

---

## Notes

The M/M/$c$ mean queue length is:
$$L_q = \frac{C(c, \lambda/\mu) \cdot (\lambda/\mu)}{c - \lambda/\mu}$$
where $C(c, \lambda/\mu)$ is the Erlang-C formula.
