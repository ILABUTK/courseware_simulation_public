"""Event traces: a record of what happened during one simulation run.

A trace lists every entity movement (arrive, queue, start service, finish
service, depart) with its simulated time. It is the data that animations,
dashboards and lecture widgets replay, so the picture on screen is exactly
what the model did.

Turn tracing on for one run with ``model.run(trace=True)``; the trace is then
available as ``model.trace``. Tracing never draws random numbers, so a traced
run returns the same results as an untraced run with the same seed.

Example:
    >>> from simdes.models.queues import MM1Queue
    >>> m = MM1Queue(arrival_rate=0.8, service_rate=1.0, sim_time=60, seed=1)
    >>> results = m.run(trace=True)
    >>> m.trace.events[0]["type"]
    'arrive'
    >>> m.trace.save("mm1_trace.json")  # doctest: +SKIP

JSON format (``schema = "simdes-trace/1"``)::

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

Events are in time order (ties keep the order they happened in). ``slot`` is
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

- ``arrive``: the entity enters the system.
- ``queue``: the entity joins the queue at a station.
- ``start``: service starts at a station (the entity takes a server slot).
- ``finish``: service ends at a station (the slot is freed).
- ``depart``: the entity leaves the system after service.
- ``leave``: the entity leaves without being served (balking, reneging).
"""


@dataclass
class Station:
    """A place where entities queue and are served.

    Args:
        id: Short identifier used in events, e.g. ``"triage"``.
        label: Human-readable name for displays, e.g. ``"Triage nurse"``.
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
        time_unit: Unit of simulated time, for labels (e.g. ``"min"``).
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
            label: Display name (defaults to ``id``).
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

        ``start`` events take the lowest free slot at the station and
        ``finish`` events free the slot the entity holds.

        Args:
            t: Simulated time of the event.
            entity: Entity identifier (unique within the run).
            type: One of :data:`EVENT_TYPES`.
            station: Station identifier, required for ``queue``, ``start``
                and ``finish``.

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
        """Rebuild a trace from :meth:`to_dict` output.

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
        """Read a trace from a JSON file written by :meth:`save`."""
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

    def waits(self, station: str) -> list[float]:
        """Time each entity spent queueing at *station* (``start - queue``)."""
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
            ``(t, n)`` pairs: from time ``t`` until the next pair, ``n``
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
        """Time-average number in system over ``[0, horizon]`` (L)."""
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
