"""What the web app asks for, in plain JSON: one place for the API and the browser.

The FastAPI server (``api.py``) and the browser's static mode (Pyodide in a
Web Worker, ``web/src/engine/pyodide.worker.ts``) both call these functions,
so the app gets the same answers from the same model code either way.

Inputs come as a dict of the controls in :data:`CONTROLS` (the levers the
web app shows); everything else stays at the baseline in ``Params``.
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
    """Baseline ``Params`` with the given controls (validated) and run settings.

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
    """Independent replications (seeds ``seed``, ``seed + 1``, ...) with 95% CIs.

    The same seeds for two input sets give common random numbers, so
    :func:`compare` can pair them.
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
    """Run ``a`` and ``b`` with the same seeds and give CIs for the differences ``b - a``."""

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
