"""Queueing theory used to check the model.

None of these formulas describes the full ED (time-varying arrivals, two
resources in series, lognormal times, priorities and patience all at once).
Each one is exact for a *reduced* version of the model, which the tests build
by switching features off, or is a rough approximation that the web app's
"Compare with theory" view labels as such.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from edflow.model import ESI_LEVELS, MIN_PER_DAY, MIN_PER_HOUR, Params, lognormal_params


def erlang_c(lam: float, mu: float, c: int) -> tuple[float, float]:
    """M/M/c: probability of waiting and mean wait in queue Wq.

    Args:
        lam: Arrival rate.
        mu: Service rate of one server.
        c: Number of servers.

    Returns:
        ``(P(wait), Wq)`` in the time unit of the rates; ``(1, inf)`` if unstable.
    """
    a = lam / mu
    rho = a / c
    if rho >= 1:
        return 1.0, math.inf
    term, total = 1.0, 1.0  # a^k / k!, running sum for k < c
    for k in range(1, c):
        term *= a / k
        total += term
    last = term * a / c / (1 - rho)  # a^c / (c! (1 - rho))
    p_wait = last / (total + last)
    return p_wait, p_wait / (c * mu - lam)


def priority_waits(lams: Sequence[float], mu: float, c: int) -> list[float]:
    """Mean wait by class in M/M/c with non-preemptive priority (class 0 first).

    All classes share the exponential service rate ``mu`` (Cobham's formula):
    ``Wq_k = C(c, a) / (c mu (1 - s_{k-1}) (1 - s_k))``, with ``s_k`` the
    utilization of classes 0..k.
    """
    lam = sum(lams)
    p_wait, _ = erlang_c(lam, mu, c)
    waits, s_prev = [], 0.0
    for lam_k in lams:
        s_k = s_prev + lam_k / (c * mu)
        if s_k >= 1:
            waits.append(math.inf)
        else:
            waits.append(p_wait / (c * mu * (1 - s_prev) * (1 - s_k)))
        s_prev = s_k
    return waits


def erlang_a(
    lam: float, mu: float, c: int, theta: float, max_queue: int = 5000
) -> dict[str, float]:
    """M/M/c+M (Erlang A): exponential patience with rate ``theta``.

    Solved as a birth-death chain truncated at ``c + max_queue`` customers.

    Returns:
        ``p_abandon`` (share who leave), ``p_wait`` (share who find all servers
        busy), ``wq`` (mean time in queue over all arrivals).
    """
    # Unnormalized probabilities, in logs to avoid overflow.
    logp = [0.0]
    for n in range(1, c + max_queue + 1):
        death = min(n, c) * mu + max(n - c, 0) * theta
        logp.append(logp[-1] + math.log(lam) - math.log(death))
    top = max(logp)
    p = np.exp(np.array(logp) - top)
    p /= p.sum()
    n = np.arange(p.size)
    queue = np.maximum(n - c, 0)
    lq = float((queue * p).sum())
    return {
        "p_abandon": theta * lq / lam,
        "p_wait": float(p[c:].sum()),
        "wq": lq / lam,
    }


# -- quantities of the full model ---------------------------------------------


def mean_physician_time(p: Params) -> float:
    """Mean physician time per patient who is seen (minutes)."""
    pairs = zip(p.esi_probs, p.treatment_mean, strict=True)
    return p.physician_share * sum(q * m for q, m in pairs)


def mean_room_time(p: Params) -> float:
    """Mean room time per treated patient, without waiting for the physician (minutes)."""
    test = p.lab_share * p.lab_mean + (1 - p.lab_share) * p.imaging_mean
    return sum(
        q * (m + tp * test + ap * p.boarding_mean)
        for q, m, tp, ap in zip(
            p.esi_probs, p.treatment_mean, p.test_prob, p.admit_prob, strict=True
        )
    )


def hourly_load(p: Params) -> list[dict[str, float | int | None]]:
    """Offered load and a stationary approximation, hour by hour (weekday and weekend).

    For each clock hour: arrival rate, physicians on duty, physician
    utilization ``rho = lambda E[S_md] / c`` and an Erlang C wait for that
    hour as if it lasted forever (a "stationary independent period"
    approximation, SIPP). It ignores priorities, patience, lognormal times,
    rooms and the carry-over of queues between hours, so treat it as a rough
    check, not a prediction.
    """
    s_md = mean_physician_time(p)
    out: list[dict[str, float | int | None]] = []
    for h in range(24):
        c = p.physicians_at(h)
        row: dict[str, float | int | None] = {"hour": h, "physicians": c}
        for label, factor in (("weekday", 1.0), ("weekend", p.weekend_multiplier)):
            lam = p.arrival_rates[h] * factor * p.arrival_scale / MIN_PER_HOUR
            row[f"arrivals_{label}"] = lam * MIN_PER_HOUR
            rho = lam * s_md / c if c else math.inf
            row[f"rho_{label}"] = rho if math.isfinite(rho) else None
            if c and lam > 0:
                _, wq = erlang_c(lam, 1.0 / s_md, c)
                row[f"sipp_wait_{label}"] = wq if math.isfinite(wq) else None
            else:
                row[f"sipp_wait_{label}"] = 0.0 if lam == 0 else None
        out.append(row)
    return out


def rooms_infinite_server(p: Params, n_draws: int = 200_000, seed: int = 12345) -> list[float]:
    """Mean rooms occupied by clock hour if rooms and physicians never ran short.

    This is the M(t)/G/infinity result (Eick, Massey and Whitt 1993): with no
    waiting for a room or a physician, the number of patients in rooms at time
    ``t`` is Poisson with mean ``m(t) = int lambda(t - u) P(T <= u < T + S) du``,
    where ``T`` is the triage time and ``S`` the room time. The distribution of
    ``T + S`` is estimated from ``n_draws`` samples (fixed seed), the integral
    on a one-minute grid over the weekly cycle.

    Where the simulated occupancy falls below this curve, rooms or physicians
    are the bottleneck. The tests compare it with the model run with unlimited
    rooms and physicians, where it should match.
    """
    rng = np.random.default_rng(seed)
    probs = np.asarray(p.esi_probs)
    esi = rng.choice(len(ESI_LEVELS), size=n_draws, p=probs / probs.sum())
    treat = np.empty(n_draws)
    for k in range(5):
        idx = esi == k
        if p.service_family == "lognormal":
            mu, sigma = lognormal_params(p.treatment_mean[k], p.treatment_sd[k])
            treat[idx] = rng.lognormal(mu, sigma, idx.sum())
        else:
            mean = p.treatment_mean[k]
            treat[idx] = rng.exponential(p.physician_share * mean, idx.sum()) + rng.exponential(
                (1 - p.physician_share) * mean, idx.sum()
            )
    test_p = np.asarray(p.test_prob)[esi]
    tested = rng.random(n_draws) < test_p
    lab = rng.random(n_draws) < p.lab_share
    lab_mu, lab_s = lognormal_params(p.lab_mean, p.lab_sd)
    img_mu, img_s = lognormal_params(p.imaging_mean, p.imaging_sd)
    test_time = np.where(
        lab, rng.lognormal(lab_mu, lab_s, n_draws), rng.lognormal(img_mu, img_s, n_draws)
    )
    admit = rng.random(n_draws) < np.asarray(p.admit_prob)[esi]
    boarding = np.where(admit, rng.exponential(p.boarding_mean, n_draws), 0.0)
    room = treat + np.where(tested, test_time, 0.0) + boarding
    triage = rng.exponential(p.triage_mean, n_draws) if p.triage_mean > 0 else np.zeros(n_draws)

    week = int(7 * MIN_PER_DAY)
    grid = np.arange(week)  # minutes since Monday 00:00
    # P(T <= u < T + S) for u = 0, 1, ..., one week (longer stays are negligible).
    u = np.arange(week, dtype=float)
    in_room = np.searchsorted(np.sort(triage), u, side="right") - np.searchsorted(
        np.sort(triage + room), u, side="right"
    )
    kernel = in_room / n_draws
    lam = np.array([p.rate_per_hour(float(t)) / MIN_PER_HOUR for t in grid])
    # Circular convolution over the weekly cycle: m(t) = sum_u lam(t - u) kernel(u).
    m = np.real(np.fft.ifft(np.fft.fft(lam) * np.fft.fft(kernel)))
    by_hour = m.reshape(7, 24, 60).mean(axis=(0, 2))
    return [float(v) for v in by_hour]
