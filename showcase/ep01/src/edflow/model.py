"""Emergency department patient flow: the simulation model.

A patient arrives (non-stationary Poisson, weekly cycle), waits for one of the
triage nurses (first come, first served) and gets an ESI acuity level (1 = most
urgent, 5 = least). The patient then waits for a treatment room and, in the
room, for a physician; both queues serve the most urgent ESI level first
(priority without preemption). After the physician's assessment the patient
stays in the room for the rest of the treatment, any lab or imaging results,
and, if admitted, boarding until an inpatient bed opens. ESI 3-5 patients
who have not seen a physician within ``patience`` minutes of arrival leave
without being seen (LWBS). The number of physicians on duty follows the shift
schedule.

Times are in minutes; day 0 is a Monday and starts at midnight.

Design choices that matter for the analysis (see the technical report):

- **Common random numbers.** Each patient's attributes (ESI, service times,
  tests, admission, boarding, patience) are drawn when the patient arrives,
  from a stream used for nothing else, with a fixed number of draws per
  patient. Two scenarios run with the same seed therefore see the same
  patients; only the system's response differs.
- **Shift changes** use "off-duty" blockers: a physician going off shift
  finishes the current patient first, then leaves. This uses SimPy's public
  API only (no private ``_capacity`` changes).
- **Observation window.** Arrivals stop after ``days``; the model keeps running
  ``drain_days`` so every observed patient finishes. Statistics cover patients
  who arrive between ``warmup_days`` and ``days``.
"""

from __future__ import annotations

import math
from collections.abc import Generator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import simpy
from simdes.core.model import BaseModel

MIN_PER_HOUR = 60.0
MIN_PER_DAY = 1440.0
ESI_LEVELS = (1, 2, 3, 4, 5)

# Weekday arrivals per hour, hours 0-23 (EP01 problem statement).
HOURLY_RATES: tuple[float, ...] = (
    (2.0,) * 6  # 00-05
    + (5.0,) * 4  # 06-09
    + (9.0,) * 5  # 10-14
    + (11.0,) * 5  # 15-19
    + (7.0,) * 4  # 20-23
)


@dataclass
class Params:
    """Inputs of the ED model. Times are in minutes, rates in patients per hour.

    Tuples indexed by ESI level hold five values, for ESI 1 to 5.

    Args:
        arrival_rates: Weekday arrivals per hour for hours 0-23.
        weekend_multiplier: Factor on every hour on Saturday and Sunday.
        arrival_scale: Factor on all arrivals (demand growth or decline).
        esi_probs: Share of patients at each ESI level.
        triage_nurses: Triage nurses on duty (all day).
        triage_mean: Mean triage time (exponential).
        rooms: Treatment rooms.
        day_physicians: Physicians on the day shift, 07:00-19:00.
        evening_physicians: Physicians on the evening shift, ``evening_start``-23:00.
        night_physicians: Physicians on the night shift, 23:00-07:00.
        evening_start: Hour the evening shift starts. The problem statement
            says 15 (it overlaps the day shift at the 15:00-19:00 peak); 19
            gives the non-overlapping reading used by the 2026 version.
        treatment_mean: Mean in-room treatment time by ESI level (lognormal).
        treatment_sd: Standard deviation of the treatment time by ESI level.
        physician_share: Share of the treatment time the physician spends with
            the patient (the assessment, at the start). Not in the data: an
            assumption, varied in the sensitivity analysis.
        service_family: ``"lognormal"`` (the data) or ``"exponential"`` with
            the same means; exponential exists only to compare with queueing
            theory in the tests.
        test_prob: Probability of lab or imaging, by ESI level.
        lab_share: Share of tested patients who get lab work (the rest imaging).
        lab_mean: Mean lab turnaround (lognormal).
        lab_sd: Standard deviation of the lab turnaround.
        imaging_mean: Mean imaging turnaround (lognormal).
        imaging_sd: Standard deviation of the imaging turnaround.
        admit_prob: Probability of admission, by ESI level.
        boarding_mean: Mean boarding time of admitted patients (exponential).
        patience: Minutes from arrival a patient waits for a physician before
            leaving without being seen. ``math.inf`` turns LWBS off.
        patience_family: ``"fixed"`` (everyone waits exactly ``patience``) or
            ``"exponential"`` (mean ``patience``).
        lwbs_min_esi: Lowest ESI level that may leave (3: ESI 1-2 never leave).
        days: Days during which patients arrive.
        warmup_days: Days discarded at the start (the ED opens empty).
        drain_days: Days the model keeps running after arrivals stop.
    """

    arrival_rates: tuple[float, ...] = HOURLY_RATES
    weekend_multiplier: float = 1.25
    arrival_scale: float = 1.0
    esi_probs: tuple[float, ...] = (0.02, 0.08, 0.35, 0.40, 0.15)
    triage_nurses: int = 2
    triage_mean: float = 4.0
    rooms: int = 30
    day_physicians: int = 4
    evening_physicians: int = 3
    night_physicians: int = 2
    evening_start: int = 15
    treatment_mean: tuple[float, ...] = (180.0, 135.0, 135.0, 50.0, 50.0)
    treatment_sd: tuple[float, ...] = (60.0, 50.0, 50.0, 20.0, 20.0)
    physician_share: float = 0.20
    service_family: str = "lognormal"
    test_prob: tuple[float, ...] = (0.90, 0.90, 0.75, 0.40, 0.10)
    lab_share: float = 0.5
    lab_mean: float = 65.0
    lab_sd: float = 30.0
    imaging_mean: float = 45.0
    imaging_sd: float = 20.0
    admit_prob: tuple[float, ...] = (0.80, 0.80, 0.35, 0.05, 0.0)
    boarding_mean: float = 90.0
    patience: float = 90.0
    patience_family: str = "fixed"
    lwbs_min_esi: int = 3
    days: float = 30.0
    warmup_days: float = 2.0
    drain_days: float = 1.0

    def __post_init__(self) -> None:
        if len(self.arrival_rates) != 24:
            raise ValueError("arrival_rates needs 24 hourly values")
        for name in ("esi_probs", "treatment_mean", "treatment_sd", "test_prob", "admit_prob"):
            if len(getattr(self, name)) != 5:
                raise ValueError(f"{name} needs one value per ESI level (5)")
        if not math.isclose(sum(self.esi_probs), 1.0, abs_tol=1e-9):
            raise ValueError("esi_probs must sum to 1")
        if self.service_family not in ("lognormal", "exponential"):
            raise ValueError("service_family must be 'lognormal' or 'exponential'")
        if self.patience_family not in ("fixed", "exponential"):
            raise ValueError("patience_family must be 'fixed' or 'exponential'")
        if not 0 < self.physician_share <= 1:
            raise ValueError("physician_share must be in (0, 1]")
        if self.warmup_days >= self.days:
            raise ValueError("warmup_days must be shorter than days")
        if self.triage_nurses < 1 or self.rooms < 1:
            raise ValueError("need at least one triage nurse and one room")
        if max(self.physicians_by_hour()) < 1:
            raise ValueError("need at least one physician on some shift")

    # -- derived quantities ------------------------------------------------

    def physicians_at(self, hour: int) -> int:
        """Physicians on duty during clock hour ``hour`` (0-23)."""
        h = hour % 24
        n = 0
        if 7 <= h < 19:
            n += self.day_physicians
        if self.evening_start <= h < 23:
            n += self.evening_physicians
        if h >= 23 or h < 7:
            n += self.night_physicians
        return n

    def physicians_by_hour(self) -> list[int]:
        """Physicians on duty for each clock hour 0-23."""
        return [self.physicians_at(h) for h in range(24)]

    def rate_per_hour(self, t: float) -> float:
        """Arrival rate (patients per hour) at simulated time ``t`` (minutes)."""
        hour = int((t % MIN_PER_DAY) // MIN_PER_HOUR)
        weekday = int(t // MIN_PER_DAY) % 7
        factor = self.weekend_multiplier if weekday >= 5 else 1.0
        return self.arrival_rates[hour] * factor * self.arrival_scale

    def max_rate_per_hour(self) -> float:
        """Upper bound of the arrival rate, for thinning."""
        return max(self.arrival_rates) * max(1.0, self.weekend_multiplier) * self.arrival_scale

    @property
    def arrival_horizon(self) -> float:
        """Time (minutes) after which no more patients arrive."""
        return self.days * MIN_PER_DAY

    @property
    def warmup(self) -> float:
        """End of the warm-up period (minutes)."""
        return self.warmup_days * MIN_PER_DAY

    @property
    def horizon(self) -> float:
        """Length of the whole run, including the drain period (minutes)."""
        return (self.days + self.drain_days) * MIN_PER_DAY


@dataclass(slots=True)
class Patient:
    """One ED visit: attributes drawn at arrival, then the times it reached each step.

    Durations are in minutes; times are simulated clock times (NaN if never reached).
    """

    id: int
    arrival: float
    esi: int
    triage_time: float
    md_time: float
    rest_time: float
    test: str  # "" (none), "lab" or "imaging"
    test_time: float
    admit: bool
    boarding_time: float
    patience: float
    triage_start: float = math.nan
    triage_end: float = math.nan
    room_start: float = math.nan
    md_start: float = math.nan
    md_end: float = math.nan
    boarding_start: float = math.nan
    depart: float = math.nan
    outcome: str = ""  # "discharged", "admitted" or "lwbs"


@dataclass
class ScriptedPatient:
    """A patient with given (not random) times, for hand traces and tests."""

    arrival: float
    esi: int = 3
    triage_time: float = 4.0
    md_time: float = 20.0
    rest_time: float = 0.0
    test_time: float = 0.0
    admit: bool = False
    boarding_time: float = 0.0
    patience: float = math.inf


def lognormal_params(mean: float, sd: float) -> tuple[float, float]:
    """(mu, sigma) of the underlying normal for a lognormal with this mean and sd.

    NumPy's ``lognormal(mu, sigma)`` takes the normal's parameters, not the
    lognormal's mean and standard deviation.
    """
    sigma2 = math.log(1.0 + (sd / mean) ** 2)
    return math.log(mean) - sigma2 / 2.0, math.sqrt(sigma2)


@dataclass
class _Draws:
    """Per-run constants used to turn standard random draws into patient attributes."""

    esi_cdf: np.ndarray
    treat: list[tuple[float, float]]
    lab: tuple[float, float]
    imaging: tuple[float, float]
    extra: dict[str, Any] = field(default_factory=dict)


class EDModel(BaseModel):
    """Emergency department patient flow.

    Args:
        params: Model inputs.
        seed: Random seed. The same seed gives the same run; two parameter
            sets run with the same seed see the same patients (common random
            numbers).
        script: Patients with given times instead of random arrivals (for
            hand traces). When given, the arrival process is not used.
    """

    time_unit = "min"

    def __init__(
        self,
        params: Params | None = None,
        seed: int | None = None,
        script: Sequence[ScriptedPatient] | None = None,
    ) -> None:
        self.params = params or Params()
        super().__init__(sim_time=self.params.horizon, seed=seed)
        self.script = list(script) if script is not None else None
        self.patients: list[Patient] = []
        self.staffing: list[tuple[float, int]] = []
        self.profiles: dict[str, list[float | None]] = {}

    def _trace_params(self) -> dict[str, Any]:
        return asdict(self.params)

    # -- building the run ---------------------------------------------------

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        p = self.params
        self.patients = []
        self.staffing = []
        self.profiles = {}
        # Two independent streams from the run's generator: one for the arrival
        # times, one for patient attributes (common random numbers).
        arrival_rng, patient_rng = rng.spawn(2)
        self._draws = _Draws(
            esi_cdf=np.cumsum(p.esi_probs),
            treat=[
                lognormal_params(m, s)
                for m, s in zip(p.treatment_mean, p.treatment_sd, strict=True)
            ],
            lab=lognormal_params(p.lab_mean, p.lab_sd),
            imaging=lognormal_params(p.imaging_mean, p.imaging_sd),
        )
        max_md = max(p.physicians_by_hour())
        triage = simpy.Resource(env, capacity=p.triage_nurses)
        rooms = simpy.PriorityResource(env, capacity=p.rooms)
        physicians = simpy.PriorityResource(env, capacity=max_md)
        self._trace_station("triage", "Triage", capacity=p.triage_nurses)
        self._trace_station("room", "Treatment rooms", capacity=p.rooms)
        self._trace_station("physician", "Physicians", capacity=max_md)
        self._trace_station("tests", "Lab / imaging (in room)", capacity=p.rooms)
        self._trace_station("boarding", "Boarding (in room)", capacity=p.rooms)
        self._res = (triage, rooms, physicians)
        env.process(self._shifts(env, physicians, max_md))
        if self.script is not None:
            env.process(self._scripted_arrivals(env))
        else:
            env.process(self._arrivals(env, arrival_rng, patient_rng))

    def _shifts(
        self, env: simpy.Environment, physicians: simpy.PriorityResource, max_md: int
    ) -> Generator[simpy.Event, Any, None]:
        """Keep (max on duty - on duty now) physicians blocked, changing each clock hour."""
        p = self.params
        off_duty: list[simpy.Event] = []  # one release event per blocked physician
        while True:
            hour = int((env.now % MIN_PER_DAY) // MIN_PER_HOUR)
            on_duty = p.physicians_at(hour)
            if not self.staffing or self.staffing[-1][1] != on_duty:
                self.staffing.append((env.now, on_duty))
            target = max_md - on_duty
            while len(off_duty) < target:
                release = env.event()
                off_duty.append(release)
                env.process(self._off_duty(physicians, release))
            while len(off_duty) > target:
                off_duty.pop().succeed()
            yield env.timeout(MIN_PER_HOUR - env.now % MIN_PER_HOUR)

    @staticmethod
    def _off_duty(
        physicians: simpy.PriorityResource, release: simpy.Event
    ) -> Generator[simpy.Event, Any, None]:
        # Priority 0 beats every ESI level: the next physician to finish a
        # patient goes off duty. If the shift starts again first, give up.
        with physicians.request(priority=0) as request:
            yield request | release
            if not release.triggered:
                yield release

    def _arrivals(
        self, env: simpy.Environment, arrival_rng: np.random.Generator,
        patient_rng: np.random.Generator,
    ) -> Generator[simpy.Event, Any, None]:
        """Non-stationary Poisson arrivals by thinning (Lewis and Shedler)."""
        p = self.params
        lam_max = p.max_rate_per_hour() / MIN_PER_HOUR
        if lam_max <= 0:
            return
        t = 0.0
        while True:
            t += arrival_rng.exponential(1.0 / lam_max)
            if t >= p.arrival_horizon:
                return
            if arrival_rng.random() * lam_max > p.rate_per_hour(t) / MIN_PER_HOUR:
                continue  # thinned out
            yield env.timeout(t - env.now)
            patient = self._new_patient(env.now, patient_rng)
            env.process(self._visit(env, patient))

    def _scripted_arrivals(self, env: simpy.Environment) -> Generator[simpy.Event, Any, None]:
        assert self.script is not None
        for s in sorted(self.script, key=lambda s: s.arrival):
            yield env.timeout(s.arrival - env.now)
            patient = Patient(
                id=self._new_entity(), arrival=env.now, esi=s.esi, triage_time=s.triage_time,
                md_time=s.md_time, rest_time=s.rest_time, test="lab" if s.test_time > 0 else "",
                test_time=s.test_time, admit=s.admit, boarding_time=s.boarding_time,
                patience=s.patience if s.esi >= self.params.lwbs_min_esi else math.inf,
            )
            self.patients.append(patient)
            env.process(self._visit(env, patient))

    def _new_patient(self, now: float, rng: np.random.Generator) -> Patient:
        """Draw every attribute of a new patient (always the same number of draws)."""
        p, d = self.params, self._draws
        u = rng.random(4)  # ESI, test yes/no, lab or imaging, admission
        z = rng.standard_normal(2)  # treatment, test turnaround
        e = rng.standard_exponential(5)  # triage, boarding, patience, 2 for exponential service
        esi = int(np.searchsorted(d.esi_cdf, u[0], side="right")) + 1
        esi = min(esi, 5)
        k = esi - 1
        if p.service_family == "lognormal":
            mu, sigma = d.treat[k]
            treatment = math.exp(mu + sigma * z[0])
            md_time = p.physician_share * treatment
            rest_time = treatment - md_time
        else:  # exponential, same means (verification only)
            md_time = p.physician_share * p.treatment_mean[k] * e[3]
            rest_time = (1.0 - p.physician_share) * p.treatment_mean[k] * e[4]
        test, test_time = "", 0.0
        if u[1] < p.test_prob[k]:
            test = "lab" if u[2] < p.lab_share else "imaging"
            mu, sigma = d.lab if test == "lab" else d.imaging
            test_time = math.exp(mu + sigma * z[1])
        admit = bool(u[3] < p.admit_prob[k])
        if esi < p.lwbs_min_esi or math.isinf(p.patience):
            patience = math.inf
        elif p.patience_family == "fixed":
            patience = p.patience
        else:
            patience = p.patience * e[2]
        patient = Patient(
            id=self._new_entity(), arrival=now, esi=esi, triage_time=p.triage_mean * e[0],
            md_time=md_time, rest_time=rest_time, test=test, test_time=test_time,
            admit=admit, boarding_time=p.boarding_mean * e[1] if admit else 0.0,
            patience=patience,
        )
        self.patients.append(patient)
        return patient

    # -- one patient's visit ----------------------------------------------

    def _visit(self, env: simpy.Environment, pt: Patient) -> Generator[simpy.Event, Any, None]:
        triage, rooms, physicians = self._res
        self._log(pt.id, "arrive")
        self._log(pt.id, "queue", "triage")
        with triage.request() as req:
            yield req
            pt.triage_start = env.now
            self._log(pt.id, "start", "triage")
            yield env.timeout(pt.triage_time)
            self._log(pt.id, "finish", "triage")
        pt.triage_end = env.now
        deadline = pt.arrival + pt.patience

        self._log(pt.id, "queue", "room")
        with rooms.request(priority=pt.esi) as room:
            got_room = yield from self._wait(env, room, deadline)
            if not got_room:
                self._leave(env, pt, "room")
                return
            pt.room_start = env.now
            self._log(pt.id, "start", "room")

            self._log(pt.id, "queue", "physician")
            with physicians.request(priority=pt.esi) as md:
                seen = yield from self._wait(env, md, deadline)
                if not seen:
                    self._log(pt.id, "finish", "room")
                    self._leave(env, pt, "physician")
                    return
                pt.md_start = env.now
                self._log(pt.id, "start", "physician")
                yield env.timeout(pt.md_time)
                self._log(pt.id, "finish", "physician")
            pt.md_end = env.now

            # Rest of the treatment, then results, then boarding: the room stays taken.
            yield env.timeout(pt.rest_time)
            if pt.test:
                self._log(pt.id, "queue", "tests")
                self._log(pt.id, "start", "tests")
                yield env.timeout(pt.test_time)
                self._log(pt.id, "finish", "tests")
            if pt.admit:
                pt.boarding_start = env.now
                self._log(pt.id, "queue", "boarding")
                self._log(pt.id, "start", "boarding")
                yield env.timeout(pt.boarding_time)
                self._log(pt.id, "finish", "boarding")
            self._log(pt.id, "finish", "room")
        pt.depart = env.now
        pt.outcome = "admitted" if pt.admit else "discharged"
        self._log(pt.id, "depart")

    @staticmethod
    def _wait(
        env: simpy.Environment, request: simpy.events.Event, deadline: float
    ) -> Generator[simpy.Event, Any, bool]:
        """Wait for ``request`` until ``deadline``. True if it was granted in time."""
        if math.isinf(deadline):
            yield request
            return True
        remaining = deadline - env.now
        if remaining <= 0:
            if request.triggered:  # free capacity: granted on the spot
                yield request
                return True
            return False
        result = yield request | env.timeout(remaining)
        return request in result

    def _leave(self, env: simpy.Environment, pt: Patient, station: str) -> None:
        pt.depart = env.now
        pt.outcome = "lwbs"
        self._log(pt.id, "leave", station)

    # -- results ------------------------------------------------------------

    def observed(self) -> list[Patient]:
        """Patients who arrived during the observation window."""
        p = self.params
        return [pt for pt in self.patients if p.warmup <= pt.arrival < p.arrival_horizon]

    def _collect(self) -> dict[str, Any]:
        p = self.params
        obs = self.observed()
        lo, hi = p.warmup, p.arrival_horizon
        out: dict[str, Any] = {"patients": len(obs)}
        done = [pt for pt in obs if pt.outcome]
        out["unfinished"] = len(obs) - len(done)
        lwbs = [pt for pt in done if pt.outcome == "lwbs"]
        treated = [pt for pt in done if pt.outcome != "lwbs"]
        admitted = [pt for pt in treated if pt.outcome == "admitted"]
        n = len(done)

        dtt = np.array([pt.triage_start - pt.arrival for pt in done])
        dtp = np.array([pt.md_start - pt.arrival for pt in treated])
        los = np.array([pt.depart - pt.arrival for pt in treated])
        room_wait = np.array([pt.room_start - pt.triage_end for pt in treated])
        boarding = np.array([pt.boarding_time for pt in admitted])

        out["lwbs_rate"] = len(lwbs) / n if n else math.nan
        out["dtt_mean"] = _mean(dtt)
        out["dtt_p90"] = _quantile(dtt, 0.9)
        out["dtp_mean"] = _mean(dtp)
        out["dtp_median"] = _quantile(dtp, 0.5)
        out["dtp_p90"] = _quantile(dtp, 0.9)
        out["seen_within_30"] = float(np.mean(dtp <= 30.0)) if dtp.size else math.nan
        out["room_wait_mean"] = _mean(room_wait)
        out["los_mean"] = _mean(los)
        for esi in ESI_LEVELS:
            out[f"los_esi{esi}"] = _mean(
                np.array([pt.depart - pt.arrival for pt in treated if pt.esi == esi])
            )
            out[f"dtp_esi{esi}"] = _mean(
                np.array([pt.md_start - pt.arrival for pt in treated if pt.esi == esi])
            )
        out["boarding_mean"] = _mean(boarding)
        out["admitted_share"] = len(admitted) / n if n else math.nan

        # Time averages over the window, from every patient's busy intervals
        # (including patients who arrived during the warm-up).
        everyone = self.patients
        room_s = np.array([pt.room_start for pt in everyone])
        room_e = np.array([pt.depart for pt in everyone])
        md_s = np.array([pt.md_start for pt in everyone])
        md_e = np.array([pt.md_end for pt in everyone])
        wait_s = np.array([pt.triage_end for pt in everyone])
        wait_e = np.array(
            [pt.room_start if not math.isnan(pt.room_start) else pt.depart for pt in everyone]
        )
        rooms_by_hour, rooms_avg = level_by_hour(room_s, room_e, lo, hi)
        md_by_hour, md_avg = level_by_hour(md_s, md_e, lo, hi)
        wr_by_hour, wr_avg = level_by_hour(wait_s, wait_e, lo, hi)
        duty_by_hour = np.array(p.physicians_by_hour(), dtype=float)
        out["room_occupancy"] = rooms_avg / p.rooms
        out["physician_utilization"] = md_avg / float(np.mean(duty_by_hour))
        out["waiting_room_mean"] = wr_avg

        # Hour-of-day profiles (not scalars: kept apart from the results).
        days_obs = (hi - lo) / MIN_PER_DAY
        arr_hour = np.array([int((pt.arrival % MIN_PER_DAY) // MIN_PER_HOUR) for pt in done])
        is_lwbs = np.array([pt.outcome == "lwbs" for pt in done])
        dtp_all = np.array([pt.md_start - pt.arrival for pt in done])
        prof: dict[str, list[float | None]] = {
            "arrivals": [], "lwbs_rate": [], "dtp_mean": [],
        }
        for h in range(24):
            in_h = arr_hour == h
            prof["arrivals"].append(float(in_h.sum()) / days_obs)
            prof["lwbs_rate"].append(_none(float(is_lwbs[in_h].mean())) if in_h.any() else None)
            seen_h = in_h & ~is_lwbs
            prof["dtp_mean"].append(_none(float(dtp_all[seen_h].mean())) if seen_h.any() else None)
        prof["rooms_busy"] = [float(v) for v in rooms_by_hour]
        prof["physicians_busy"] = [float(v) for v in md_by_hour]
        prof["physicians_on_duty"] = [float(v) for v in duty_by_hour]
        prof["waiting_room"] = [float(v) for v in wr_by_hour]
        self.profiles = prof
        return out


# -- helpers ------------------------------------------------------------------


def _mean(values: np.ndarray) -> float:
    return float(np.mean(values)) if values.size else math.nan


def _quantile(values: np.ndarray, q: float) -> float:
    return float(np.quantile(values, q)) if values.size else math.nan


def _none(value: float) -> float | None:
    return None if math.isnan(value) else value


def level_by_hour(
    starts: np.ndarray, ends: np.ndarray, lo: float, hi: float
) -> tuple[np.ndarray, float]:
    """Time-average number of open intervals, by clock hour and overall.

    Each interval ``[start, end)`` adds one to the level while it is open;
    intervals with a NaN start never opened, a NaN end means still open at
    ``hi``. ``lo`` and ``hi`` must fall on whole hours.

    Returns:
        (mean level for each clock hour 0-23, mean level over ``[lo, hi)``).
    """
    starts = np.asarray(starts, dtype=float)
    ends = np.asarray(ends, dtype=float)
    ok = ~np.isnan(starts)
    s = np.clip(starts[ok], lo, hi)
    e = np.clip(np.where(np.isnan(ends[ok]), hi, ends[ok]), lo, hi)
    keep = e > s
    s, e = s[keep], e[keep]
    marks = np.arange(lo, hi, MIN_PER_HOUR)
    times = np.concatenate([s, e, marks])
    steps = np.concatenate([np.ones(s.size), -np.ones(e.size), np.zeros(marks.size)])
    order = np.argsort(times, kind="stable")
    times, steps = times[order], steps[order]
    level = np.cumsum(steps)
    length = np.diff(np.append(times, hi))
    hour = ((times // MIN_PER_HOUR) % 24).astype(int)
    area = np.bincount(hour, weights=level * length, minlength=24)
    span = np.bincount(hour, weights=length, minlength=24)
    by_hour = np.divide(area, span, out=np.zeros(24), where=span > 0)
    return by_hour, float(area.sum() / (hi - lo))
