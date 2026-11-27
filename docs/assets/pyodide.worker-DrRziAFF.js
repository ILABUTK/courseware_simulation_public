var h=`"""Your simulation study. Start in model.py."""
`,c=`"""Emergency department patient flow: the simulation model.

A patient arrives (non-stationary Poisson, weekly cycle), waits for one of the
triage nurses (first come, first served) and gets an ESI acuity level (1 = most
urgent, 5 = least). The patient then waits for a treatment room and, in the
room, for a physician; both queues serve the most urgent ESI level first
(priority without preemption). After the physician's assessment the patient
stays in the room for the rest of the treatment, any lab or imaging results,
and, if admitted, boarding until an inpatient bed opens. ESI 3-5 patients
who have not seen a physician within \`\`patience\`\` minutes of arrival leave
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
  API only (no private \`\`_capacity\`\` changes).
- **Observation window.** Arrivals stop after \`\`days\`\`; the model keeps running
  \`\`drain_days\`\` so every observed patient finishes. Statistics cover patients
  who arrive between \`\`warmup_days\`\` and \`\`days\`\`.
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
        evening_physicians: Physicians on the evening shift, \`\`evening_start\`\`-23:00.
        night_physicians: Physicians on the night shift, 23:00-07:00.
        evening_start: Hour the evening shift starts. The problem statement
            says 15 (it overlaps the day shift at the 15:00-19:00 peak); 19
            gives the non-overlapping reading used by the 2026 version.
        treatment_mean: Mean in-room treatment time by ESI level (lognormal).
        treatment_sd: Standard deviation of the treatment time by ESI level.
        physician_share: Share of the treatment time the physician spends with
            the patient (the assessment, at the start). Not in the data: an
            assumption, varied in the sensitivity analysis.
        service_family: \`\`"lognormal"\`\` (the data) or \`\`"exponential"\`\` with
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
            leaving without being seen. \`\`math.inf\`\` turns LWBS off.
        patience_family: \`\`"fixed"\`\` (everyone waits exactly \`\`patience\`\`) or
            \`\`"exponential"\`\` (mean \`\`patience\`\`).
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
        """Physicians on duty during clock hour \`\`hour\`\` (0-23)."""
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
        """Arrival rate (patients per hour) at simulated time \`\`t\`\` (minutes)."""
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

    NumPy's \`\`lognormal(mu, sigma)\`\` takes the normal's parameters, not the
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
        """Wait for \`\`request\`\` until \`\`deadline\`\`. True if it was granted in time."""
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

    Each interval \`\`[start, end)\`\` adds one to the level while it is open;
    intervals with a NaN start never opened, a NaN end means still open at
    \`\`hi\`\`. \`\`lo\`\` and \`\`hi\`\` must fall on whole hours.

    Returns:
        (mean level for each clock hour 0-23, mean level over \`\`[lo, hi)\`\`).
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
`,_=`"""Confidence intervals that also run in the browser.

The web app's static mode runs this package in Pyodide, where SciPy would add
a large download. So the Student t quantile is computed here from the
regularized incomplete beta function (NumPy and the standard library only).
\`\`tests/test_stats.py\`\` checks it against SciPy and against
\`\`simdes.analysis.ci.confidence_interval\`\`, which the experiment scripts use.
"""

from __future__ import annotations

import math
from collections.abc import Iterable


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    """Cumulative distribution function of Student's t with \`\`df\`\` degrees of freedom."""
    x = df / (df + t * t)
    tail = 0.5 * _betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """Quantile of Student's t (inverse of :func:\`t_cdf\`), by bisection."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    if p == 0.5:
        return 0.0
    if p < 0.5:
        return -t_quantile(1.0 - p, df)
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12:
            break
    return 0.5 * (lo + hi)


def mean_ci(values: Iterable[float], alpha: float = 0.05) -> dict[str, float | int | None]:
    """Mean and two-sided t confidence interval of independent replication results.

    NaN values are dropped. With fewer than two values the interval is None.

    Returns:
        \`\`{"mean", "low", "high", "half_width", "sd", "n"}\`\`.
    """
    data = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    n = len(data)
    if n == 0:
        return {"mean": None, "low": None, "high": None, "half_width": None, "sd": None, "n": 0}
    mean = sum(data) / n
    if n < 2:
        return {"mean": mean, "low": None, "high": None, "half_width": None, "sd": None, "n": 1}
    sd = math.sqrt(sum((v - mean) ** 2 for v in data) / (n - 1))
    half = t_quantile(1.0 - alpha / 2.0, n - 1) * sd / math.sqrt(n)
    return {
        "mean": mean, "low": mean - half, "high": mean + half, "half_width": half, "sd": sd,
        "n": n,
    }


def paired_ci(
    a: Iterable[float], b: Iterable[float], alpha: float = 0.05
) -> dict[str, float | int | None]:
    """Confidence interval for the mean of \`\`b - a\`\` over paired replications (CRN).

    Pairs where either value is NaN are dropped.
    """
    diffs = [
        float(y) - float(x)
        for x, y in zip(a, b, strict=True)
        if x is not None and y is not None and not math.isnan(float(x)) and not math.isnan(float(y))
    ]
    return mean_ci(diffs, alpha)
`,y=`"""Queueing theory used to check the model.

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
        \`\`(P(wait), Wq)\`\` in the time unit of the rates; \`\`(1, inf)\`\` if unstable.
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

    All classes share the exponential service rate \`\`mu\`\` (Cobham's formula):
    \`\`Wq_k = C(c, a) / (c mu (1 - s_{k-1}) (1 - s_k))\`\`, with \`\`s_k\`\` the
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
    """M/M/c+M (Erlang A): exponential patience with rate \`\`theta\`\`.

    Solved as a birth-death chain truncated at \`\`c + max_queue\`\` customers.

    Returns:
        \`\`p_abandon\`\` (share who leave), \`\`p_wait\`\` (share who find all servers
        busy), \`\`wq\`\` (mean time in queue over all arrivals).
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
    utilization \`\`rho = lambda E[S_md] / c\`\` and an Erlang C wait for that
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
    \`\`t\`\` is Poisson with mean \`\`m(t) = int lambda(t - u) P(T <= u < T + S) du\`\`,
    where \`\`T\`\` is the triage time and \`\`S\`\` the room time. The distribution of
    \`\`T + S\`\` is estimated from \`\`n_draws\`\` samples (fixed seed), the integral
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
`,g=`"""Named scenarios: the options the ED director is choosing between.

Each scenario changes a few inputs of the baseline (\`\`Params()\`\`). The
"decision" scenarios are the options on the table; the "stress" scenarios ask
how robust the answer is to things the director does not control.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from edflow.model import Params


@dataclass(frozen=True)
class Scenario:
    """One alternative: a label, why it is studied, and the inputs it changes."""

    id: str
    label: str
    description: str
    changes: dict[str, Any] = field(default_factory=dict)
    group: str = "decision"  # "decision" or "stress"

    def params(self, **overrides: Any) -> Params:
        """The baseline with this scenario's changes (and any overrides) applied."""
        return replace(Params(), **{**self.changes, **overrides})


SCENARIO_LIST: list[Scenario] = [
    Scenario("baseline", "Current operation", "Shifts and boarding as today."),
    Scenario(
        "evening_plus1", "+1 evening physician",
        "A fourth physician on the 15:00-23:00 shift.", {"evening_physicians": 4},
    ),
    Scenario(
        "night_plus1", "+1 night physician",
        "A third physician on the 23:00-07:00 shift.", {"night_physicians": 3},
    ),
    Scenario(
        "day_plus1", "+1 day physician",
        "A fifth physician on the 07:00-19:00 shift.", {"day_physicians": 5},
    ),
    Scenario(
        "boarding_60", "Boarding 90 -> 60 min",
        "The hospital's bed-management program cuts mean boarding time to 60 minutes.",
        {"boarding_mean": 60.0},
    ),
    Scenario(
        "evening_plus1_boarding_60", "+1 evening and boarding 60",
        "Both changes together.", {"evening_physicians": 4, "boarding_mean": 60.0},
    ),
    Scenario(
        "night_minus1", "-1 night physician",
        "The cost-cutting proposal: one physician at night.", {"night_physicians": 1},
    ),
    Scenario(
        "arrivals_plus10", "Arrivals +10%",
        "Demand grows 10% with today's staffing.", {"arrival_scale": 1.1}, "stress",
    ),
    Scenario(
        "boarding_120", "Boarding 120 min",
        "Inpatient units fill up and boarding gets longer.", {"boarding_mean": 120.0}, "stress",
    ),
    Scenario(
        "boarding_180", "Boarding 180 min",
        "A hospital-wide bed crisis.", {"boarding_mean": 180.0}, "stress",
    ),
]

SCENARIOS: dict[str, Scenario] = {s.id: s for s in SCENARIO_LIST}
`,v=`"""What the web app asks for, in plain JSON: one place for the API and the browser.

The FastAPI server (\`\`api.py\`\`) and the browser's static mode (Pyodide in a
Web Worker, \`\`web/src/engine/pyodide.worker.ts\`\`) both call these functions,
so the app gets the same answers from the same model code either way.

Inputs come as a dict of the controls in :data:\`CONTROLS\` (the levers the
web app shows); everything else stays at the baseline in \`\`Params\`\`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, replace
from typing import Any

from edflow import theory
from edflow.model import MIN_PER_DAY, EDModel, Params
from edflow.scenarios import SCENARIO_LIST
from edflow.stats import mean_ci, paired_ci

# name, label, unit, hard min, hard max, checked low, checked high, step, help
_CONTROL_ROWS: list[tuple[str, str, str, float, float, float, float, float, str]] = [
    ("day_physicians", "Day physicians (07-19)", "", 0, 10, 4, 5, 1,
     "Physicians on the 07:00-19:00 shift."),
    ("evening_physicians", "Evening physicians (15-23)", "", 0, 10, 3, 4, 1,
     "Physicians on the evening shift, which overlaps the day shift from 15:00."),
    ("night_physicians", "Night physicians (23-07)", "", 0, 10, 1, 3, 1,
     "Physicians on the 23:00-07:00 shift."),
    ("boarding_mean", "Mean boarding time", "min", 0, 600, 60, 180, 10,
     "Average wait of admitted patients for an inpatient bed, in a treatment room."),
    ("arrival_scale", "Demand (x today)", "x", 0.5, 1.5, 0.9, 1.1, 0.05,
     "Multiplies every hourly arrival rate."),
    ("rooms", "Treatment rooms", "", 10, 60, 25, 35, 1, "Rooms shared by all acuity levels."),
    ("triage_nurses", "Triage nurses", "", 1, 6, 2, 3, 1, "Nurses at triage, all day."),
    ("patience", "LWBS patience", "min", 15, 600, 60, 120, 5,
     "ESI 3-5 patients not seen by a physician this long after arrival leave."),
    ("physician_share", "Physician share of treatment", "", 0.05, 0.5, 0.15, 0.30, 0.01,
     "Assumed share of the in-room treatment time a physician spends with the patient."),
    ("evening_start", "Evening shift starts at", "h", 13, 19, 15, 19, 1,
     "15 is the problem statement (overlap with the day shift); 19 is the 2026 reading."),
]

CONTROLS: list[dict[str, Any]] = [
    {
        "name": name, "label": label, "unit": unit, "min": lo, "max": hi,
        "checked": [clo, chi], "step": step, "help": help_,
        "default": getattr(Params(), name),
        "integer": isinstance(getattr(Params(), name), int),
    }
    for name, label, unit, lo, hi, clo, chi, step, help_ in _CONTROL_ROWS
]
_BY_NAME = {c["name"]: c for c in CONTROLS}

# key, label, unit, scale for display, better
KPIS: list[dict[str, Any]] = [
    {"key": "lwbs_rate", "label": "Left without being seen", "unit": "%", "scale": 100,
     "better": "lower", "target": 2.0},
    {"key": "dtp_median", "label": "Door-to-physician, median", "unit": "min", "scale": 1,
     "better": "lower", "target": 30.0},
    {"key": "dtp_p90", "label": "Door-to-physician, 90th percentile", "unit": "min", "scale": 1,
     "better": "lower", "target": None},
    {"key": "seen_within_30", "label": "Seen within 30 min", "unit": "%", "scale": 100,
     "better": "higher", "target": None},
    {"key": "dtt_p90", "label": "Door-to-triage, 90th percentile", "unit": "min", "scale": 1,
     "better": "lower", "target": 10.0},
    {"key": "los_mean", "label": "Length of stay (treated)", "unit": "min", "scale": 1,
     "better": "lower", "target": None},
    {"key": "boarding_mean", "label": "Boarding time (admitted)", "unit": "min", "scale": 1,
     "better": "lower", "target": None},
    {"key": "room_occupancy", "label": "Room occupancy", "unit": "%", "scale": 100,
     "better": None, "target": None},
    {"key": "physician_utilization", "label": "Physician utilization", "unit": "%", "scale": 100,
     "better": None, "target": None},
    {"key": "room_wait_mean", "label": "Wait for a room after triage", "unit": "min", "scale": 1,
     "better": "lower", "target": None},
] + [
    {"key": f"los_esi{k}", "label": f"Length of stay, ESI {k}", "unit": "min", "scale": 1,
     "better": "lower", "target": None}
    for k in range(1, 6)
]

PROFILE_KEYS = ("arrivals", "lwbs_rate", "dtp_mean", "rooms_busy", "physicians_busy",
                "physicians_on_duty", "waiting_room")

ASSUMPTIONS: list[dict[str, str]] = [
    {"topic": "Arrivals", "source": "data",
     "text": "Poisson arrivals with the hourly weekday rates of the problem statement, +25% on "
             "weekends. Same rates every week (no seasons, no surges)."},
    {"topic": "Acuity", "source": "data",
     "text": "ESI 1-5 with shares 2/8/35/40/15%, independent of the time of day."},
    {"topic": "Shifts", "source": "interpretation",
     "text": "Day 07-19, evening 15-23 and night 23-07 add up, so 7 physicians are on duty "
             "15-19. A physician going off shift finishes the current patient first."},
    {"topic": "Physician time", "source": "assumption",
     "text": "The physician spends 20% of the in-room treatment time with the patient, at the "
             "start. The data give only the total treatment time; this share is the most "
             "uncertain input and changes the LWBS rate a lot."},
    {"topic": "Priorities", "source": "interpretation",
     "text": "Rooms and physicians serve the lowest ESI number first, without preempting a "
             "patient already in a room or with a physician."},
    {"topic": "Rooms", "source": "data",
     "text": "30 rooms shared by all levels. The room is held for treatment, lab or imaging "
             "results, and boarding."},
    {"topic": "Lab and imaging", "source": "assumption",
     "text": "A tested patient gets lab or imaging, half and half (the split is not in the "
             "data), after the treatment; never both."},
    {"topic": "LWBS", "source": "interpretation",
     "text": "ESI 3-5 patients leave if no physician has started within 90 minutes of arrival "
             "(fixed patience, counted from the door). ESI 1-2 never leave."},
    {"topic": "Boarding", "source": "data",
     "text": "Admitted patients board in their room for an exponential time (mean 90 min), "
             "independent of how full the hospital is."},
    {"topic": "Not modeled", "source": "simplification",
     "text": "Ambulance diversion, nurses in the rooms, fast track, re-triage, physician "
             "breaks and handover time, transfers, and returns."},
]


def catalog() -> dict[str, Any]:
    """Everything the web app needs to draw its controls before running anything."""
    return {
        "controls": CONTROLS,
        "kpis": KPIS,
        "assumptions": ASSUMPTIONS,
        "scenarios": [
            {"id": s.id, "label": s.label, "description": s.description, "group": s.group,
             "inputs": {**defaults(), **s.changes}}
            for s in SCENARIO_LIST
        ],
        "defaults": defaults(),
    }


def defaults() -> dict[str, Any]:
    """The baseline value of every control."""
    return {c["name"]: c["default"] for c in CONTROLS}


def params_from(inputs: dict[str, Any] | None, **run: Any) -> Params:
    """Baseline \`\`Params\`\` with the given controls (validated) and run settings.

    Raises:
        ValueError: For an unknown control or a value outside its hard limits.
    """
    changes: dict[str, Any] = {}
    for name, value in (inputs or {}).items():
        spec = _BY_NAME.get(name)
        if spec is None:
            raise ValueError(f"unknown input {name!r}")
        if value is None:
            continue
        value = float(value)
        if not spec["min"] <= value <= spec["max"]:
            raise ValueError(f"{name} must be between {spec['min']} and {spec['max']}")
        changes[name] = int(round(value)) if spec["integer"] else value
    return replace(Params(), **changes, **run)


def warnings(inputs: dict[str, Any] | None, reps: int | None = None,
             days: float | None = None) -> list[dict[str, str]]:
    """Plain-language warnings: inputs outside the checked range, overload, low precision."""
    out: list[dict[str, str]] = []
    values = {**defaults(), **(inputs or {})}
    for c in CONTROLS:
        v = float(values[c["name"]])
        lo, hi = c["checked"]
        if not lo <= v <= hi:
            out.append({
                "level": "caution",
                "message": f"{c['label']} = {v:g} is outside the range the model was checked "
                           f"for ({lo:g}-{hi:g}). The model still runs, but nobody has "
                           f"compared its behavior there with anything.",
            })
    p = params_from(inputs)
    over = _overloaded_hours(p)
    if over:
        by_hour: dict[int, list[str]] = {}
        for h, label in over:
            by_hour.setdefault(h, []).append(f"{label}s")
        hours = ", ".join(f"{h:02d}:00 ({' and '.join(days)})" for h, days in by_hour.items())
        new = [o for o in over if o not in _overloaded_hours(Params())]
        out.append({
            "level": "warning" if new else "info",
            "message": f"Physicians on duty cannot keep up with arrivals, even on average, at "
                       f"{hours}{' (as today)' if not new else ''}. Queues build there until "
                       f"the next shift change, so the LWBS rate depends strongly on patience.",
        })
    room_load = sum(p.arrival_rates) / 24 * p.arrival_scale * theory.mean_room_time(p) / 60
    if room_load > 0.85 * p.rooms:
        out.append({
            "level": "warning",
            "message": f"Rooms are needed {room_load:.0f} at a time on average out of {p.rooms}: "
                       f"expect long waits for a room at peak hours.",
        })
    if reps is not None and reps < 10:
        out.append({"level": "caution",
                    "message": f"Only {reps} replications: confidence intervals are wide."})
    if days is not None and days < 14:
        out.append({"level": "caution",
                    "message": f"Each run covers only {days:g} days: weekly variation adds noise."})
    return out


def _overloaded_hours(p: Params) -> list[tuple[int, str]]:
    """Clock hours where arrivals x mean physician time exceed the physicians on duty."""
    return sorted({
        (int(row["hour"]), label)  # type: ignore[call-overload]
        for row in theory.hourly_load(p)
        for label in ("weekday", "weekend")
        if row[f"rho_{label}"] is None or row[f"rho_{label}"] >= 1  # type: ignore[operator]
    })


# -- runs -----------------------------------------------------------------------


def trace_run(inputs: dict[str, Any] | None, seed: int = 1, days: float = 7.0) -> dict[str, Any]:
    """One run with its event trace, for the animation.

    Returns the simdes trace plus what the trace format has no room for: each
    patient's ESI level and outcome (indexed by entity id) and the physicians
    on duty over time.
    """
    p = params_from(inputs, days=days, warmup_days=min(2.0, days / 2))
    model = EDModel(p, seed=seed)
    results = model.run(trace=True)
    assert model.trace is not None
    patients = sorted(model.patients, key=lambda pt: pt.id)
    return {
        "results": _clean(results),
        "trace": model.trace.to_dict(),
        "esi": [pt.esi for pt in patients],
        "outcome": [pt.outcome for pt in patients],
        "staffing": [[t, n] for t, n in model.staffing],
        "warmup": p.warmup,
        "arrival_horizon": p.arrival_horizon,
        "profiles": model.profiles,
        "warnings": warnings(inputs, days=days),
    }


def replications(
    inputs: dict[str, Any] | None, reps: int = 10, seed: int = 1, days: float = 30.0,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Independent replications (seeds \`\`seed\`\`, \`\`seed + 1\`\`, ...) with 95% CIs.

    The same seeds for two input sets give common random numbers, so
    :func:\`compare\` can pair them.
    """
    p = params_from(inputs, days=days)
    runs, profiles = [], []
    for i in range(reps):
        model = EDModel(p, seed=seed + i)
        runs.append(_clean(model.run()))
        profiles.append(model.profiles)
        if progress is not None:
            progress(i + 1, reps)
    return {
        "reps": reps, "seed": seed, "days": days, "warmup_days": p.warmup_days,
        "kpis": summarize(runs),
        "profiles": {
            key: [mean_ci([pr[key][h] for pr in profiles]) for h in range(24)]
            for key in PROFILE_KEYS
        },
        "runs": runs,
        "warnings": warnings(inputs, reps=reps, days=days),
    }


def summarize(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Mean and 95% CI of every scalar result over replications."""
    keys = [k for k in runs[0] if isinstance(runs[0][k], int | float) or runs[0][k] is None]
    return {k: mean_ci([r[k] for r in runs]) for k in keys}


def compare(a: dict[str, Any] | None, b: dict[str, Any] | None, reps: int = 10, seed: int = 1,
            days: float = 30.0, progress: Callable[[int, int], None] | None = None,
            ) -> dict[str, Any]:
    """Run \`\`a\`\` and \`\`b\`\` with the same seeds and give CIs for the differences \`\`b - a\`\`."""

    def half(offset: int) -> Callable[[int, int], None] | None:
        if progress is None:
            return None
        return lambda done, total: progress(offset + done, 2 * total)

    ra = replications(a, reps, seed, days, half(0))
    rb = replications(b, reps, seed, days, half(reps))
    diff = {
        k: paired_ci([r[k] for r in ra["runs"]], [r[k] for r in rb["runs"]])
        for k in ra["kpis"]
    }
    return {"a": ra, "b": rb, "diff": diff, "reps": reps, "seed": seed, "days": days}


def theory_view(inputs: dict[str, Any] | None, n_draws: int = 100_000) -> dict[str, Any]:
    """Offered load by hour, a rough stationary (SIPP) wait, and the unlimited-rooms curve."""
    p = params_from(inputs)
    return {
        "mean_physician_time": theory.mean_physician_time(p),
        "mean_room_time": theory.mean_room_time(p),
        "hourly": theory.hourly_load(p),
        "rooms_unlimited": theory.rooms_infinite_server(p, n_draws=n_draws),
        "physicians_by_hour": p.physicians_by_hour(),
        "rooms": p.rooms,
    }


def baseline_params() -> dict[str, Any]:
    """Every baseline input (for the About page)."""
    return _clean(asdict(Params()))


def _clean(value: Any) -> Any:
    """Make a value JSON-safe: NaN and infinity become None, tuples lists."""
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


__all__ = [
    "CONTROLS", "KPIS", "ASSUMPTIONS", "MIN_PER_DAY", "catalog", "defaults", "params_from",
    "warnings", "trace_run", "replications", "summarize", "compare", "theory_view",
    "baseline_params",
]
`,b=`"""simdes — discrete-event simulation models and analysis tools."""

__version__ = "0.2.1"
__all__ = ["__version__"]
`,w=`"""Core abstractions: BaseModel and SimPy environment helpers."""

from simdes.core.model import BaseModel

__all__ = ["BaseModel"]
`,N=`"""BaseModel: common interface for all simdes simulation models."""

from __future__ import annotations

import abc
from typing import Any

import numpy as np
import pandas as pd
import simpy

from simdes.trace import Trace


class BaseModel(abc.ABC):
    """Abstract base class for all simdes simulation models.

    Subclasses must implement :meth:\`_build\` (populate the SimPy environment)
    and :meth:\`_collect\` (extract performance measures after the run).

    Subclasses that support tracing declare their stations with
    :meth:\`_trace_station\` in \`\`_build\`\` and record movements with
    :meth:\`_log\`. Both do nothing unless the run was started with
    \`\`run(trace=True)\`\`.

    Args:
        sim_time: Simulated time horizon for each run.
        seed: Base random seed.  Each replication increments this by one so
            that replications are independent but reproducible.
    """

    time_unit: str = "time units"
    """Unit of simulated time, used to label traces and displays."""

    def __init__(self, sim_time: float, seed: int | None = None) -> None:
        self.sim_time = sim_time
        self.seed = seed
        self._rng: np.random.Generator | None = None
        self._env: simpy.Environment | None = None
        self.trace: Trace | None = None
        self._tracing = False
        self._entity_count = 0

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        """Populate *env* with SimPy processes.  Called once per run."""

    @abc.abstractmethod
    def _collect(self) -> dict[str, Any]:
        """Return a dict of scalar performance measures after the run ends."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *, trace: bool = False) -> dict[str, Any]:
        """Execute one replication and return performance measures.

        Args:
            trace: Record an event trace of this run in :attr:\`trace\`
                (see :mod:\`simdes.trace\`). Tracing draws no random numbers,
                so results are identical with or without it.

        Returns:
            dict mapping metric names to scalar values.
        """
        seed = self.seed if self.seed is not None else 0
        self._rng = np.random.default_rng(seed)
        self._env = simpy.Environment()
        self._entity_count = 0
        self._tracing = trace
        self.trace = (
            Trace(
                model=type(self).__name__,
                params=self._trace_params(),
                seed=seed,
                horizon=float(self.sim_time),
                time_unit=self.time_unit,
            )
            if trace
            else None
        )
        self._build(self._env, self._rng)
        self._env.run(until=self.sim_time)
        results = self._collect()
        if self.trace is not None:
            self.trace.results = dict(results)
        self._tracing = False
        return results

    # ------------------------------------------------------------------
    # Tracing helpers for subclasses
    # ------------------------------------------------------------------

    def _trace_params(self) -> dict[str, Any]:
        """Model parameters to store in a trace.

        The default takes the public attributes that are plain numbers,
        strings or booleans. Override it to describe nested parameters.
        """
        skip = {"sim_time", "seed", "trace", "time_unit"}
        return {
            k: v
            for k, v in vars(self).items()
            if not k.startswith("_")
            and k not in skip
            and isinstance(v, int | float | str | bool)
        }

    def _new_entity(self) -> int:
        """Return the next entity identifier (0, 1, 2, ...) for this run."""
        n = self._entity_count
        self._entity_count += 1
        return n

    def _trace_station(
        self, id: str, label: str | None = None, capacity: int = 1
    ) -> None:
        """Declare a station in the trace (no-op when not tracing)."""
        if self.trace is not None:
            self.trace.add_station(id, label, capacity)

    def _log(self, entity: int, type: str, station: str | None = None) -> None:
        """Record an event at the current simulated time (no-op when not tracing)."""
        if self.trace is not None and self._tracing:
            assert self._env is not None
            self.trace.log(self._env.now, entity, type, station)

    def run_replications(self, n: int) -> pd.DataFrame:
        """Execute *n* independent replications.

        Each replication uses seed \`\`self.seed + i\`\` so results are
        reproducible but independent.

        Args:
            n: Number of replications.

        Returns:
            DataFrame with one row per replication and one column per metric.
        """
        original_seed = self.seed
        records = []
        for i in range(n):
            self.seed = (original_seed or 0) + i
            records.append(self.run())
        self.seed = original_seed
        return pd.DataFrame(records)
`,k=`"""Event traces: a record of what happened during one simulation run.

A trace lists every entity movement (arrive, queue, start service, finish
service, depart) with its simulated time. It is the data that animations,
dashboards and lecture widgets replay, so the picture on screen is exactly
what the model did.

Turn tracing on for one run with \`\`model.run(trace=True)\`\`; the trace is then
available as \`\`model.trace\`\`. Tracing never draws random numbers, so a traced
run returns the same results as an untraced run with the same seed.

Example:
    >>> from simdes.models.queues import MM1Queue
    >>> m = MM1Queue(arrival_rate=0.8, service_rate=1.0, sim_time=60, seed=1)
    >>> results = m.run(trace=True)
    >>> m.trace.events[0]["type"]
    'arrive'
    >>> m.trace.save("mm1_trace.json")  # doctest: +SKIP

JSON format (\`\`schema = "simdes-trace/1"\`\`)::

    {
      "schema": "simdes-trace/1",
      "model": "MM1Queue",
      "params": {"arrival_rate": 0.8, "service_rate": 1.0},
      "seed": 1,
      "horizon": 60,
      "time_unit": "time units",
      "stations": [{"id": "server", "label": "Server", "capacity": 1}],
      "events": [
        {"t": 0.42, "id": 0, "type": "arrive"},
        {"t": 0.42, "id": 0, "type": "queue", "station": "server"},
        {"t": 0.42, "id": 0, "type": "start", "station": "server", "slot": 0},
        {"t": 1.97, "id": 0, "type": "finish", "station": "server", "slot": 0},
        {"t": 1.97, "id": 0, "type": "depart"}
      ],
      "results": {"mean_wait_queue": 3.1, "...": "..."}
    }

Events are in time order (ties keep the order they happened in). \`\`slot\`\` is
the server position at the station (0 to capacity - 1), assigned by the trace
as the lowest free slot, so an animation can draw each server in a fixed place.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "simdes-trace/1"

EVENT_TYPES = ("arrive", "queue", "start", "finish", "depart", "leave")
"""Event vocabulary.

- \`\`arrive\`\`: the entity enters the system.
- \`\`queue\`\`: the entity joins the queue at a station.
- \`\`start\`\`: service starts at a station (the entity takes a server slot).
- \`\`finish\`\`: service ends at a station (the slot is freed).
- \`\`depart\`\`: the entity leaves the system after service.
- \`\`leave\`\`: the entity leaves without being served (balking, reneging).
"""


@dataclass
class Station:
    """A place where entities queue and are served.

    Args:
        id: Short identifier used in events, e.g. \`\`"triage"\`\`.
        label: Human-readable name for displays, e.g. \`\`"Triage nurse"\`\`.
        capacity: Number of servers (slots) at the station.
    """

    id: str
    label: str
    capacity: int = 1


@dataclass
class Trace:
    """Event log of one simulation run.

    Args:
        model: Model class name.
        params: Model parameters, as plain JSON-serialisable values.
        seed: Random seed of the run.
        horizon: Simulated time horizon.
        time_unit: Unit of simulated time, for labels (e.g. \`\`"min"\`\`).
    """

    model: str
    params: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    horizon: float = 0.0
    time_unit: str = "time units"
    stations: list[Station] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)
    _busy: dict[str, dict[int, int]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def add_station(self, id: str, label: str | None = None, capacity: int = 1) -> None:
        """Declare a station, in the order displays should draw it.

        Args:
            id: Station identifier used in events.
            label: Display name (defaults to \`\`id\`\`).
            capacity: Number of servers.

        Raises:
            ValueError: If the station was already declared.
        """
        if any(s.id == id for s in self.stations):
            raise ValueError(f"station {id!r} declared twice")
        self.stations.append(Station(id=id, label=label or id, capacity=capacity))
        self._busy[id] = {}

    def log(self, t: float, entity: int, type: str, station: str | None = None) -> None:
        """Record one event.

        \`\`start\`\` events take the lowest free slot at the station and
        \`\`finish\`\` events free the slot the entity holds.

        Args:
            t: Simulated time of the event.
            entity: Entity identifier (unique within the run).
            type: One of :data:\`EVENT_TYPES\`.
            station: Station identifier, required for \`\`queue\`\`, \`\`start\`\`
                and \`\`finish\`\`.

        Raises:
            ValueError: For an unknown event type or station, a missing
                station, or a station with no free slot.
        """
        if type not in EVENT_TYPES:
            raise ValueError(f"unknown event type {type!r}")
        event: dict[str, Any] = {"t": float(t), "id": int(entity), "type": type}
        if type in ("queue", "start", "finish"):
            if station is None:
                raise ValueError(f"{type!r} events need a station")
            if station not in self._busy:
                raise ValueError(f"unknown station {station!r}; call add_station first")
            event["station"] = station
            busy = self._busy[station]
            if type == "start":
                capacity = self._capacity(station)
                slot = next((k for k in range(capacity) if k not in busy), None)
                if slot is None:
                    raise ValueError(f"no free slot at {station!r} at t={t}")
                busy[slot] = int(entity)
                event["slot"] = slot
            elif type == "finish":
                slot = next((k for k, e in busy.items() if e == int(entity)), None)
                if slot is None:
                    raise ValueError(
                        f"entity {entity} finished at {station!r} without starting"
                    )
                del busy[slot]
                event["slot"] = slot
        elif station is not None:
            event["station"] = station
        self.events.append(event)

    def _capacity(self, station: str) -> int:
        return next(s.capacity for s in self.stations if s.id == station)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return the trace as a JSON-ready dict (see the module docstring)."""
        return {
            "schema": SCHEMA,
            "model": self.model,
            "params": _jsonable(self.params),
            "seed": self.seed,
            "horizon": self.horizon,
            "time_unit": self.time_unit,
            "stations": [asdict(s) for s in self.stations],
            "events": self.events,
            "results": _jsonable(self.results),
        }

    def to_json(self, indent: int | None = None) -> str:
        """Return the trace as a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, allow_nan=False)

    def save(self, path: str | Path, indent: int | None = None) -> Path:
        """Write the trace to a JSON file and return its path."""
        path = Path(path)
        path.write_text(self.to_json(indent=indent), encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trace:
        """Rebuild a trace from :meth:\`to_dict\` output.

        Raises:
            ValueError: If the schema is missing or not supported.
        """
        if data.get("schema") != SCHEMA:
            raise ValueError(f"expected schema {SCHEMA!r}, got {data.get('schema')!r}")
        trace = cls(
            model=data["model"],
            params=dict(data.get("params", {})),
            seed=data.get("seed"),
            horizon=float(data.get("horizon", 0.0)),
            time_unit=data.get("time_unit", "time units"),
            results=dict(data.get("results", {})),
        )
        trace.stations = [Station(**s) for s in data.get("stations", [])]
        trace.events = list(data.get("events", []))
        return trace

    @classmethod
    def load(cls, path: str | Path) -> Trace:
        """Read a trace from a JSON file written by :meth:\`save\`."""
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

    def waits(self, station: str) -> list[float]:
        """Time each entity spent queueing at *station* (\`\`start - queue\`\`)."""
        joined: dict[int, float] = {}
        waits: list[float] = []
        for e in self.events:
            if e.get("station") != station:
                continue
            if e["type"] == "queue":
                joined[e["id"]] = e["t"]
            elif e["type"] == "start" and e["id"] in joined:
                waits.append(e["t"] - joined.pop(e["id"]))
        return waits

    def number_in_system(self) -> list[tuple[float, int]]:
        """Step function of the number of entities in the system.

        Returns:
            \`\`(t, n)\`\` pairs: from time \`\`t\`\` until the next pair, \`\`n\`\`
            entities were in the system.
        """
        n = 0
        steps: list[tuple[float, int]] = [(0.0, 0)]
        for e in self.events:
            if e["type"] == "arrive":
                n += 1
            elif e["type"] in ("depart", "leave"):
                n -= 1
            else:
                continue
            if steps[-1][0] == e["t"]:
                steps[-1] = (e["t"], n)
            else:
                steps.append((e["t"], n))
        return steps

    def time_average_in_system(self) -> float:
        """Time-average number in system over \`\`[0, horizon]\`\` (L)."""
        steps = self.number_in_system()
        if self.horizon <= 0:
            return float("nan")
        area = 0.0
        for (t0, n), (t1, _) in zip(steps, steps[1:] + [(self.horizon, 0)]):
            area += n * (min(t1, self.horizon) - min(t0, self.horizon))
        return area / self.horizon


def _jsonable(value: Any) -> Any:
    """Convert numpy scalars, NaN and infinities to plain JSON values."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item") and callable(value.item):  # numpy scalar
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
`;const l="https://cdn.jsdelivr.net/pyodide/v0.28.3/full/",E="simpy==4.1.1",S={"edflow/__init__.py":h,"edflow/model.py":c,"edflow/stats.py":_,"edflow/theory.py":y,"edflow/scenarios.py":g,"edflow/service.py":v,"simdes/__init__.py":b,"simdes/core/__init__.py":w,"simdes/core/model.py":N,"simdes/trace.py":k},e=t=>self.postMessage(t);let r=null;async function d(){e({type:"status",phase:"Loading Python (Pyodide)…",pct:5});const{loadPyodide:t}=await import(`${l}pyodide.mjs`),n=await t({indexURL:l});e({type:"status",phase:"Loading NumPy and pandas…",pct:35}),await n.loadPackage(["numpy","pandas","micropip"]),e({type:"status",phase:"Installing SimPy…",pct:75}),await n.runPythonAsync(`import micropip
await micropip.install(${JSON.stringify(E)})`),e({type:"status",phase:"Loading the ED model…",pct:90});for(const[i,s]of Object.entries(S)){const o=`/home/pyodide/${i.slice(0,i.lastIndexOf("/"))}`;n.FS.mkdirTree(o),n.FS.writeFile(`/home/pyodide/${i}`,s)}n.runPython(`
import json, sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
from edflow import service

def _call(method, args_json, progress=None):
    args = json.loads(args_json)
    fn = getattr(service, method)
    if progress is not None and method in ("replications", "compare"):
        out = fn(*args, progress=lambda done, total: progress(done, total))
    else:
        out = fn(*args)
    return json.dumps(out, allow_nan=False)
`);const a=n.runPython("import sys; sys.version.split()[0]");return e({type:"status",phase:"Ready",pct:100}),e({type:"ready",python:a}),n}const P=new Set(["catalog","trace_run","replications","compare","theory_view","warnings"]);self.addEventListener("message",async t=>{const{id:n,method:a,args:i}=t.data;try{r||(r=d());const s=await r;if(!P.has(a))throw new Error(`unknown method ${a}`);const o=s.globals.get("_call"),m=(f,u)=>e({type:"progress",id:n,done:f,total:u}),p=o(a,JSON.stringify(i),m);e({type:"result",id:n,json:p})}catch(s){e({type:"error",id:n,message:String(s)})}});r=d();r.catch(t=>e({type:"error",id:null,message:String(t)}));
