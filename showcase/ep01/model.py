"""
EP01 — Emergency Department Patient Flow: SimPy Model

Generated via AI copilot (Stage 3).  See prompts/p03_scaffold.md for the
original prompt and prompts/p04_debug.md for bugs found and fixed.

Run one replication:
    python showcase/ep01/model.py
"""

from __future__ import annotations

import dataclasses
import math
from typing import Optional

import numpy as np
import simpy

# ── Parameters ────────────────────────────────────────────────────────────────

# Patients per hour by time-of-day (weekday), indexed by hour 0–23.
HOURLY_RATE_WEEKDAY: list[float] = (
    [2.0] * 6     # 00–05
    + [5.0] * 4   # 06–09
    + [9.0] * 5   # 10–14
    + [11.0] * 5  # 15–19
    + [7.0] * 4   # 20–23
)
assert len(HOURLY_RATE_WEEKDAY) == 24
WEEKEND_MULTIPLIER = 1.25

ESI_PROBS = [0.02, 0.08, 0.35, 0.40, 0.15]  # ESI levels 1–5


def _lognorm_mu_sigma(mean_min: float, std_min: float) -> tuple[float, float]:
    """Convert (mean, std) in minutes to (μ, σ) of the underlying normal.

    NumPy's rng.lognormal(mu, sigma) expects the parameters of the underlying
    normal, NOT the mean/std of the lognormal itself.  Conversion:
        σ_ln² = log(1 + (std/mean)²)
        μ_ln  = log(mean) − σ_ln²/2
    """
    sigma2 = math.log(1.0 + (std_min / mean_min) ** 2)
    mu = math.log(mean_min) - sigma2 / 2.0
    return mu, math.sqrt(sigma2)


# Stage-4 fix: physician holds patient only for the initial assessment phase.
# See the full diagnosis in prompts/p04_debug.md.
# Calibrated so physician utilisation ρ ≈ 0.80 → LWBS ≈ 3–8 % at baseline.
PHYSICIAN_FRACTION: float = 0.20

# Total in-room duration from physician arrival to disposition readiness (μ_ln, σ_ln).
_TREATMENT_MEANS_STDS: dict[int, tuple[float, float]] = {
    1: (180, 60),   # L1
    2: (135, 50),   # L2–3
    3: (135, 50),
    4: (50, 20),    # L4–5
    5: (50, 20),
}
TREATMENT_PARAMS: dict[int, tuple[float, float]] = {
    esi: _lognorm_mu_sigma(m, s) for esi, (m, s) in _TREATMENT_MEANS_STDS.items()
}
# Physician direct-contact time = PHYSICIAN_FRACTION × total room-stay time.
PHYSICIAN_ENCOUNTER_PARAMS: dict[int, tuple[float, float]] = {
    esi: _lognorm_mu_sigma(PHYSICIAN_FRACTION * m, PHYSICIAN_FRACTION * s)
    for esi, (m, s) in _TREATMENT_MEANS_STDS.items()
}
LAB_PARAMS     = _lognorm_mu_sigma(65, 30)
IMAGING_PARAMS = _lognorm_mu_sigma(45, 20)

# Probabilities keyed by ESI level.
LAB_IMAGING_PROB: dict[int, float] = {1: 0.90, 2: 0.90, 3: 0.75, 4: 0.40, 5: 0.10}
ADMISSION_PROB:   dict[int, float] = {1: 0.80, 2: 0.80, 3: 0.35, 4: 0.05, 5: 0.00}

N_TRIAGE_NURSES   = 2
N_TREATMENT_ROOMS = 30
LWBS_PATIENCE_MIN = 90.0          # minutes without provider → patient leaves


# ── Patient record ────────────────────────────────────────────────────────────

@dataclasses.dataclass
class Patient:
    """All timestamps and disposition data for one ED visit."""

    pid:             int
    arrival_time:    float
    weekend:         bool
    esi:             int   = 0
    triage_start:    float = float("nan")
    triage_end:      float = float("nan")
    room_start:      float = float("nan")
    physician_start: float = float("nan")
    physician_end:   float = float("nan")
    lab_end:         float = float("nan")
    imaging_end:     float = float("nan")
    depart_time:     float = float("nan")
    disposition:     str   = ""    # "discharged" | "admitted" | "lwbs"
    boarding_start:  float = float("nan")
    boarding_end:    float = float("nan")


# ── Model ─────────────────────────────────────────────────────────────────────

class EDModel:
    """Discrete-event simulation of a 30-bed academic emergency department.

    Args:
        env: SimPy Environment.
        rng: NumPy Generator — must be seeded externally for reproducibility.
        night_physicians: Override for the night-shift physician count (default 2).
        boarding_mean_minutes: Override for mean inpatient boarding time (default 90).
    """

    def __init__(
        self,
        env: simpy.Environment,
        rng: np.random.Generator,
        day_physicians: int = 4,
        evening_physicians: int = 3,
        night_physicians: int = 2,
        boarding_mean_minutes: float = 90.0,
        arrival_scale: float = 1.0,
        lwbs_patience_minutes: float = 90.0,
    ) -> None:
        self.env = env
        self.rng = rng
        self.day_physicians = day_physicians
        self.evening_physicians = evening_physicians
        self.night_physicians = night_physicians
        self.boarding_mean_minutes = boarding_mean_minutes
        self.arrival_scale = arrival_scale
        self.lwbs_patience_minutes = lwbs_patience_minutes

        self.triage_nurses   = simpy.Resource(env, capacity=N_TRIAGE_NURSES)
        self.treatment_rooms = simpy.PriorityResource(env, capacity=N_TREATMENT_ROOMS)
        # Initial capacity = night shift; shift_manager corrects at 07:00.
        self.physicians      = simpy.PriorityResource(env, capacity=night_physicians)

        self.patients: list[Patient] = []
        self._pid = 0

        # Occupancy monitoring: (sim_time, rooms_occupied) samples every 5 min.
        self._occ_samples: list[tuple[float, int]] = []

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _hour_of_day(self) -> float:
        """Fractional hour within the current 24-h cycle."""
        return (self.env.now % (24.0 * 60.0)) / 60.0

    def _is_weekend(self, now_min: float) -> bool:
        """True if now_min falls on a Saturday or Sunday (day 0 = Monday)."""
        return int(now_min / (24.0 * 60.0)) % 7 >= 5

    def _arrival_rate(self) -> float:
        """Patients per hour at the current simulation time."""
        hour = int(self._hour_of_day())
        base = HOURLY_RATE_WEEKDAY[hour]
        if self._is_weekend(self.env.now):
            base *= WEEKEND_MULTIPLIER
        return base * self.arrival_scale

    def _n_physicians_for_hour(self, hour: float) -> int:
        """Physician count for a given (possibly fractional) hour-of-day."""
        h = hour % 24.0
        if 7.0 <= h < 19.0:
            return self.day_physicians
        if 19.0 <= h < 23.0:
            return self.evening_physicians
        return self.night_physicians

    # ── Coroutines ────────────────────────────────────────────────────────────

    def shift_manager(self) -> simpy.events.Event:
        """Wakes at each shift boundary and adjusts physician pool capacity.

        Boundaries: 07:00, 19:00, 23:00 (local day time).  Runs indefinitely.
        After increasing capacity, calls _trigger_put so any waiting patients
        in the physician queue are immediately served if slots are now free.
        """
        boundaries = [7.0, 19.0, 23.0]
        while True:
            hod = self._hour_of_day()
            next_bh = next((b for b in boundaries if b > hod), None)
            if next_bh is None:
                # Past 23:00 — wrap to next day's 07:00
                next_bh = 7.0
                sleep_min = (24.0 - hod + next_bh) * 60.0
            else:
                sleep_min = (next_bh - hod) * 60.0

            yield self.env.timeout(sleep_min)

            new_cap = self._n_physicians_for_hour(next_bh)
            self.physicians._capacity = new_cap
            # Notify the resource so pending requests are served if slots opened.
            self.physicians._trigger_put(None)

    def occupancy_monitor(self, interval: float = 5.0) -> simpy.events.Event:
        """Samples room occupancy every `interval` minutes for time-averaging."""
        while True:
            self._occ_samples.append(
                (self.env.now, len(self.treatment_rooms.users))
            )
            yield self.env.timeout(interval)

    def arrival_generator(self) -> simpy.events.Event:
        """Generates patients with time-varying Poisson inter-arrivals.

        Rate λ(t) is looked up per hour; inter-arrival ~ Exp(60/λ) minutes.
        """
        while True:
            rate = self._arrival_rate()
            yield self.env.timeout(self.rng.exponential(60.0 / rate))
            self._pid += 1
            pat = Patient(
                pid=self._pid,
                arrival_time=self.env.now,
                weekend=self._is_weekend(self.env.now),
            )
            self.patients.append(pat)
            self.env.process(self.patient_process(pat))

    def patient_process(self, pat: Patient) -> simpy.events.Event:
        """Simulate one patient's ED visit end-to-end.

        Uses nested `with resource.request()` blocks so SimPy's context
        manager correctly releases granted resources and cancels pending
        (ungranted) requests on any exit path, including LWBS early return.

        Args:
            pat: Patient record mutated in-place with timestamps and disposition.
        """
        env, rng = self.env, self.rng

        # ── 1. Triage (FCFS, 2 nurses) ────────────────────────────────────
        with self.triage_nurses.request() as nurse_req:
            yield nurse_req
            pat.triage_start = env.now
            yield env.timeout(rng.exponential(4.0))
            pat.esi = int(rng.choice(5, p=ESI_PROBS)) + 1  # 1–5
            pat.triage_end = env.now
        # Nurse released here.

        # ── 2. Treatment room (priority = ESI; lower number = higher acuity) ─
        with self.treatment_rooms.request(priority=pat.esi) as room_req:
            yield room_req
            pat.room_start = env.now

            # ── 3. Physician with LWBS reneging ───────────────────────────
            # The 90-min LWBS timer starts here (first physician queue entry).
            # env.any_of() races the physician request against the timeout.
            # SimPy's Request context manager handles both exit paths:
            #   - Triggered (granted): __exit__ releases the physician slot.
            #   - Not triggered (LWBS): __exit__ cancels the pending request.
            with self.physicians.request(priority=pat.esi) as phys_req:
                result = yield env.any_of(
                    [phys_req, env.timeout(self.lwbs_patience_minutes)]
                )

                if phys_req not in result:
                    # Timer fired first — patient leaves without being seen.
                    pat.disposition = "lwbs"
                    pat.depart_time = env.now
                    return  # exits all with-blocks; room and physician req cleaned up

                pat.physician_start = env.now

                # ── 4. Physician direct contact (initial assessment) ──────
                # Stage-4 fix: hold physician only for PHYSICIAN_FRACTION of the
                # total room-stay time.  The problem says lab/imaging results
                # "hold the room" — not the physician.  Holding the physician for
                # the full treatment time gives ρ ≈ 3.1 and 84 % LWBS (see
                # p04_debug.md for full diagnosis).
                encounter_time = rng.lognormal(*PHYSICIAN_ENCOUNTER_PARAMS[pat.esi])
                yield env.timeout(encounter_time)
                pat.physician_end = env.now
            # Physician released here; lab/imaging runs without physician.

            # ── 5. Lab / Imaging (pure delay; room held, no physician) ────
            if rng.random() < LAB_IMAGING_PROB[pat.esi]:
                if rng.random() < 0.5:  # 50/50 lab vs. imaging
                    yield env.timeout(rng.lognormal(*LAB_PARAMS))
                    pat.lab_end = env.now
                else:
                    yield env.timeout(rng.lognormal(*IMAGING_PARAMS))
                    pat.imaging_end = env.now

            # ── 6. Disposition (room still held) ──────────────────────────
            if rng.random() < ADMISSION_PROB[pat.esi]:
                pat.disposition = "admitted"
                pat.boarding_start = env.now
                yield env.timeout(rng.exponential(self.boarding_mean_minutes))
                pat.boarding_end = env.now
            else:
                pat.disposition = "discharged"

            pat.depart_time = env.now
        # Room released here.


# ── Replication runner ────────────────────────────────────────────────────────

def run_replication(
    seed: int | np.random.SeedSequence,
    warmup_minutes: float = 2880.0,    # 48 h
    horizon_minutes: float = 43200.0,  # 30 days (warmup + obs)
    day_physicians: int = 4,
    evening_physicians: int = 3,
    night_physicians: int = 2,
    boarding_mean_minutes: float = 90.0,
    arrival_scale: float = 1.0,
    lwbs_patience_minutes: float = 90.0,
    export_patients: Optional[list] = None,
) -> dict[str, float]:
    """Run one replication and return a post-warmup KPI summary.

    Args:
        seed: Integer seed or SeedSequence child (for CRN via SeedSequence.spawn).
        warmup_minutes: Observations before this time are discarded.
        horizon_minutes: Total simulation run length including warmup.
        night_physicians: Night-shift physician count (23:00–07:00). Default 2.
        boarding_mean_minutes: Mean inpatient boarding wait (minutes). Default 90.
        export_patients: If a list is provided, post-warmup Patient records are
            appended to it (for per-patient analyses such as by-hour DTP).

    Returns:
        Dict of scalar KPI values with keys:
        n_patients, lwbs_rate,
        door_to_triage_mean, door_to_triage_p50, door_to_triage_p90,
        door_to_provider_mean, door_to_provider_p50, door_to_provider_p90,
        los_mean, los_esi{1..5}, boarding_mean, occupancy_mean.
    """
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    model = EDModel(env, rng,
                    day_physicians=day_physicians,
                    evening_physicians=evening_physicians,
                    night_physicians=night_physicians,
                    boarding_mean_minutes=boarding_mean_minutes,
                    arrival_scale=arrival_scale,
                    lwbs_patience_minutes=lwbs_patience_minutes)

    env.process(model.arrival_generator())
    env.process(model.shift_manager())
    env.process(model.occupancy_monitor(interval=5.0))
    env.run(until=horizon_minutes)

    # Post-warmup patients with a recorded departure time.
    completed = [
        p for p in model.patients
        if not math.isnan(p.depart_time) and p.depart_time > warmup_minutes
    ]
    if not completed:
        return {"n_patients": 0}

    if export_patients is not None:
        export_patients.extend(completed)

    n      = len(completed)
    lwbs   = [p for p in completed if p.disposition == "lwbs"]
    seen   = [p for p in completed if p.disposition != "lwbs"]
    admtd  = [p for p in completed if p.disposition == "admitted"]

    def _mean(vals: list[float]) -> float:
        return float(np.nanmean(vals)) if vals else float("nan")

    def _pct(vals: list[float], q: float) -> float:
        return float(np.nanpercentile(vals, q)) if vals else float("nan")

    dtt = [p.triage_start    - p.arrival_time for p in completed
           if not math.isnan(p.triage_start)]
    dtp = [p.physician_start - p.arrival_time for p in seen
           if not math.isnan(p.physician_start)]
    los = [p.depart_time     - p.arrival_time for p in completed]
    brd = [p.boarding_end    - p.boarding_start for p in admtd
           if not math.isnan(p.boarding_end)]
    mdq = [p.physician_start - p.room_start for p in seen
           if not math.isnan(p.physician_start) and not math.isnan(p.room_start)]

    # Time-average occupancy post-warmup: mean(rooms_in_use / N_ROOMS)
    occ_post = [(t, n_r) for t, n_r in model._occ_samples if t >= warmup_minutes]
    if len(occ_post) >= 2:
        times   = [s[0] for s in occ_post]
        n_rooms = [s[1] for s in occ_post]
        # Trapezoidal area under rooms-occupied curve, normalised by N_ROOMS
        area = float(np.trapz(n_rooms, times))
        span = times[-1] - times[0]
        occupancy_mean = (area / span) / N_TREATMENT_ROOMS if span > 0 else float("nan")
    else:
        occupancy_mean = float("nan")

    kpis: dict[str, float] = {
        "n_patients":                   float(n),
        "lwbs_rate":                    len(lwbs) / n,
        "door_to_triage_mean":          _mean(dtt),
        "door_to_triage_p50":           _pct(dtt, 50),
        "door_to_triage_p90":           _pct(dtt, 90),
        "door_to_provider_mean":        _mean(dtp),
        "door_to_provider_p50":         _pct(dtp, 50),
        "door_to_provider_p90":         _pct(dtp, 90),
        "los_mean":                     _mean(los),
        "los_p50":                      _pct(los, 50),
        "physician_queue_wait_p50":     _pct(mdq, 50),
        "boarding_mean":                _mean(brd),
        "occupancy_mean":               occupancy_mean,
    }
    for esi in range(1, 6):
        vals = [p.depart_time - p.arrival_time for p in completed if p.esi == esi]
        kpis[f"los_esi{esi}"] = _mean(vals)

    return kpis


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EP01 — one replication  (seed=42, warmup=48 h, horizon=30 days)")
    print("Running...", flush=True)
    kpis = run_replication(seed=42)

    print(f"\n{'KPI':<30} {'Value':>12}")
    print("-" * 44)
    for key, val in kpis.items():
        if key == "n_patients":
            print(f"{key:<30} {int(val):>12,}")
        elif "rate" in key or "occupancy" in key:
            print(f"{key:<30} {val * 100:>11.2f}%")
        else:
            print(f"{key:<30} {val:>10.1f} min")
