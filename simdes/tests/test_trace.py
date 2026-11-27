"""Tests for simdes.trace: event traces of simulation runs."""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pytest

from simdes.models.clinic import ClinicModel, ClinicParams
from simdes.models.queues import MM1Queue, MMCQueue
from simdes.trace import SCHEMA, Trace


def _mm1(**kw: object) -> MM1Queue:
    args = {"arrival_rate": 0.8, "service_rate": 1.0, "sim_time": 2_000, "seed": 3}
    args.update(kw)
    return MM1Queue(**args)  # type: ignore[arg-type]


# ----------------------------------------------------------------------
# Tracing must not change the model
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "make",
    [
        lambda: _mm1(),
        lambda: MMCQueue(
            arrival_rate=2.5, service_rate=1.0, n_servers=3, sim_time=1_000, seed=5
        ),
        lambda: ClinicModel(ClinicParams(n_nurses=2), seed=7),
    ],
    ids=["mm1", "mmc", "clinic"],
)
def test_traced_run_gives_identical_results(make) -> None:
    plain = make().run()
    traced_model = make()
    traced = traced_model.run(trace=True)
    assert traced == plain
    assert traced_model.trace is not None
    assert traced_model.trace.results == traced


def test_untraced_run_has_no_trace() -> None:
    m = _mm1()
    m.run(trace=True)
    m.run()
    assert m.trace is None


def test_replications_unchanged_by_tracing_support() -> None:
    df = _mm1(sim_time=500).run_replications(3)
    assert list(df["n_customers"]) == [
        _mm1(sim_time=500, seed=3 + i).run()["n_customers"] for i in range(3)
    ]


# ----------------------------------------------------------------------
# The trace agrees with the model's own statistics
# ----------------------------------------------------------------------


def test_mm1_trace_matches_model_statistics() -> None:
    m = _mm1()
    results = m.run(trace=True)
    trace = m.trace
    assert trace is not None
    waits = trace.waits("server")
    assert len(waits) == results["n_customers"]
    assert np.mean(waits) == pytest.approx(results["mean_wait_queue"])


def test_clinic_trace_matches_model_statistics() -> None:
    m = ClinicModel(ClinicParams(n_nurses=1, n_exam_rooms=2), seed=11)
    results = m.run(trace=True)
    trace = m.trace
    assert trace is not None
    assert [s.id for s in trace.stations] == ["registration", "triage", "exam"]
    assert trace.time_unit == "min"
    assert trace.params["n_exam_rooms"] == 2
    assert np.mean(trace.waits("triage")) == pytest.approx(results["mean_wait_triage"])
    assert np.mean(trace.waits("exam")) == pytest.approx(results["mean_wait_exam"])
    departs = sum(e["type"] == "depart" for e in trace.events)
    assert departs == results["n_patients"]


def test_events_are_time_ordered_and_slots_respect_capacity() -> None:
    m = MMCQueue(arrival_rate=2.8, service_rate=1.0, n_servers=3, sim_time=500, seed=2)
    m.run(trace=True)
    trace = m.trace
    assert trace is not None
    times = [e["t"] for e in trace.events]
    assert times == sorted(times)
    busy: set[int] = set()
    for e in trace.events:
        if e["type"] == "start":
            assert 0 <= e["slot"] < 3
            assert e["slot"] not in busy
            busy.add(e["slot"])
        elif e["type"] == "finish":
            busy.remove(e["slot"])


def test_each_entity_follows_the_event_sequence() -> None:
    m = _mm1(sim_time=300)
    m.run(trace=True)
    assert m.trace is not None
    by_entity: dict[int, list[str]] = {}
    for e in m.trace.events:
        by_entity.setdefault(e["id"], []).append(e["type"])
    full = ["arrive", "queue", "start", "finish", "depart"]
    for seq in by_entity.values():
        assert seq == full[: len(seq)]  # entities still inside at the end are cut short


# ----------------------------------------------------------------------
# Analytical check: Little's law and M/M/1 theory, from the trace alone
# ----------------------------------------------------------------------


def test_trace_reproduces_mm1_theory() -> None:
    lam, mu = 0.8, 1.0
    m = MM1Queue(arrival_rate=lam, service_rate=mu, sim_time=50_000, seed=1)
    m.run(trace=True)
    trace = m.trace
    assert trace is not None
    # Time-average number in system L vs. closed form rho / (1 - rho) = 4.
    rho = lam / mu
    assert trace.time_average_in_system() == pytest.approx(rho / (1 - rho), rel=0.1)
    # Little's law: L = lambda * W, with W measured per entity from the trace.
    arrive = {e["id"]: e["t"] for e in trace.events if e["type"] == "arrive"}
    w = [e["t"] - arrive[e["id"]] for e in trace.events if e["type"] == "depart"]
    assert trace.time_average_in_system() == pytest.approx(lam * np.mean(w), rel=0.05)


# ----------------------------------------------------------------------
# Serialisation and validation
# ----------------------------------------------------------------------


def test_json_round_trip(tmp_path) -> None:
    m = ClinicModel(seed=4)
    m.run(trace=True)
    assert m.trace is not None
    path = m.trace.save(tmp_path / "clinic.json")
    data = json.loads(path.read_text())
    assert data["schema"] == SCHEMA
    assert data["model"] == "ClinicModel"
    loaded = Trace.load(path)
    assert loaded.events == m.trace.events
    assert loaded.stations == m.trace.stations
    assert loaded.results == m.trace.to_dict()["results"]


def test_nan_results_become_null() -> None:
    trace = Trace(model="X", results={"a": float("nan"), "b": np.float64(2.0)})
    data = json.loads(trace.to_json())
    assert data["results"] == {"a": None, "b": 2.0}


def test_wrong_schema_is_rejected() -> None:
    with pytest.raises(ValueError, match="schema"):
        Trace.from_dict({"schema": "other/1", "model": "X"})


@pytest.mark.parametrize(
    ("type_", "station", "message"),
    [
        ("teleport", None, "unknown event type"),
        ("queue", None, "need a station"),
        ("queue", "nowhere", "unknown station"),
        ("finish", "s", "without starting"),
    ],
)
def test_invalid_events_are_rejected(
    type_: str, station: str | None, message: str
) -> None:
    trace = Trace(model="X")
    trace.add_station("s", capacity=1)
    with pytest.raises(ValueError, match=message):
        trace.log(0.0, 1, type_, station)


def test_station_capacity_is_enforced() -> None:
    trace = Trace(model="X")
    trace.add_station("s", capacity=1)
    trace.log(0.0, 1, "start", "s")
    with pytest.raises(ValueError, match="no free slot"):
        trace.log(0.5, 2, "start", "s")
    with pytest.raises(ValueError, match="declared twice"):
        trace.add_station("s")


def test_number_in_system_steps() -> None:
    trace = Trace(model="X", horizon=10.0)
    trace.add_station("s", capacity=2)
    for t, i, kind in [
        (1, 0, "arrive"),
        (2, 1, "arrive"),
        (2, 2, "arrive"),
        (4, 0, "depart"),
        (6, 1, "leave"),
    ]:
        trace.log(t, i, kind)
    assert trace.number_in_system() == [
        (0.0, 0),
        (1.0, 1),
        (2.0, 3),
        (4.0, 2),
        (6.0, 1),
    ]
    # area = 1*1 + 3*2 + 2*2 + 1*4 = 15 over 10 time units
    assert trace.time_average_in_system() == pytest.approx(1.5)
    assert Counter(e["type"] for e in trace.events)["arrive"] == 3
