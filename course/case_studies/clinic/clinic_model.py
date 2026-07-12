"""Clinic case study — convenience wrappers for teaching notebooks.

This module re-exports the canonical ``ClinicModel`` and ``ClinicParams``
from the ``simdes`` package and adds a convenience ``run_clinic`` function
that matches the API used throughout the case study notebooks.

Usage::

    from case_studies.clinic.clinic_model import run_clinic, ClinicParams

    results = run_clinic(ClinicParams(n_nurses=2, sim_time=480), n_reps=30)
    print(results[["mean_total_time", "mean_wait_triage"]].describe())
"""

from simdes.models.clinic import ClinicModel
from simdes.models.clinic import ClinicParams  # re-export for notebook convenience

__all__ = ["ClinicModel", "ClinicParams", "run_clinic"]


def run_clinic(params: ClinicParams, n_reps: int = 30, base_seed: int = 2024):
    """Run *n_reps* independent replications of the clinic model.

    Args:
        params: Clinic configuration (arrival rate, number of nurses, …).
        n_reps: Number of independent replications.
        base_seed: Base random seed; replication *i* uses ``base_seed + i``.

    Returns:
        :class:`pandas.DataFrame` with one row per replication and columns
        ``mean_total_time``, ``mean_wait_registration``, ``mean_wait_triage``,
        ``mean_wait_exam``, ``n_patients``.

    Example::

        >>> from case_studies.clinic.clinic_model import run_clinic, ClinicParams
        >>> df = run_clinic(ClinicParams(n_nurses=2, sim_time=480), n_reps=5)
        >>> "mean_total_time" in df.columns
        True
    """
    model = ClinicModel(params=params, seed=base_seed)
    return model.run_replications(n_reps)
