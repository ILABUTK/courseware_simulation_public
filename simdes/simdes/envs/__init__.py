"""Gymnasium-compatible environments wrapping SimPy models (Module M12).

gymnasium is an optional dependency — import individual env classes directly
rather than relying on this package-level import.
"""

from typing import Any

__all__ = ["ClinicEnv", "SSInventoryEnv"]


def __getattr__(name: str) -> Any:
    if name == "ClinicEnv":
        from simdes.envs.clinic_env import ClinicEnv

        return ClinicEnv
    if name == "SSInventoryEnv":
        from simdes.envs.inventory_env import SSInventoryEnv

        return SSInventoryEnv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
