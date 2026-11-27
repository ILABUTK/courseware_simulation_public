"""Named scenarios: the options the ED director is choosing between.

Each scenario changes a few inputs of the baseline (``Params()``). The
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
