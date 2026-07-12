"""Terminal case study — convenience wrappers for teaching notebooks.

This module re-exports the canonical ``TerminalModel`` and ``TerminalParams``
from the ``simdes`` package and adds a convenience ``run_terminal`` function
that matches the API used throughout the case study notebooks.

Usage::

    from case_studies.terminal.terminal_model import run_terminal, TerminalParams

    results = run_terminal(TerminalParams(n_gates=3, n_cranes=2, sim_time=8), n_reps=30)
    print(results[["mean_total_time", "mean_wait_gate"]].describe())
"""

from simdes.models.terminal import TerminalModel
from simdes.models.terminal import TerminalParams  # re-export for notebook convenience

__all__ = ["TerminalModel", "TerminalParams", "run_terminal"]


def run_terminal(params: TerminalParams, n_reps: int = 30, base_seed: int = 2024):
    """Run *n_reps* independent replications of the terminal model.

    Args:
        params: Terminal configuration (gates, cranes, arrival rate, …).
        n_reps: Number of independent replications.
        base_seed: Base random seed; replication *i* uses ``base_seed + i``.

    Returns:
        :class:`pandas.DataFrame` with one row per replication and columns
        ``mean_total_time``, ``mean_wait_gate``, ``mean_wait_crane``,
        ``n_trucks``.

    Example::

        >>> from case_studies.terminal.terminal_model import run_terminal, TerminalParams
        >>> df = run_terminal(TerminalParams(n_gates=3, sim_time=8), n_reps=5)
        >>> "mean_total_time" in df.columns
        True
    """
    model = TerminalModel(params=params, seed=base_seed)
    return model.run_replications(n_reps)
