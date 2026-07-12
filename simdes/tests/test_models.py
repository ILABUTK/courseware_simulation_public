"""Unit tests for ClinicModel and TerminalModel.

Each test compares simulation output to a known analytical result or a
monotonicity property, following the project convention that every model
must have at least one test anchored to an analytical/theoretical value.
"""

import pytest
import numpy as np

from simdes.models.clinic import ClinicModel, ClinicParams
from simdes.models.terminal import TerminalModel, TerminalParams


# ── ClinicModel ───────────────────────────────────────────────────────────────


class TestClinicModel:
    def test_basic_run_returns_expected_keys(self):
        m = ClinicModel(seed=0)
        result = m.run()
        for key in ("mean_total_time", "mean_wait_triage", "n_patients"):
            assert key in result, f"Missing key: {key}"

    def test_patients_served_positive(self):
        p = ClinicParams(sim_time=480.0)
        m = ClinicModel(params=p, seed=1)
        result = m.run()
        assert result["n_patients"] > 0

    def test_more_nurses_reduces_triage_wait(self):
        """Doubling triage nurses should reduce mean triage wait time."""
        p1 = ClinicParams(n_nurses=1, sim_time=10_000)
        p2 = ClinicParams(n_nurses=2, sim_time=10_000)
        r1 = ClinicModel(params=p1, seed=42).run()
        r2 = ClinicModel(params=p2, seed=42).run()
        assert r2["mean_wait_triage"] < r1["mean_wait_triage"]

    def test_total_time_exceeds_service_time(self):
        """Mean total time must be at least the sum of mean service times."""
        p = ClinicParams(
            reg_mean=3.0, triage_mean=8.0, exam_mean=15.0, sim_time=20_000
        )
        m = ClinicModel(params=p, seed=5)
        result = m.run()
        min_service = p.reg_mean + p.triage_mean + p.exam_mean
        assert result["mean_total_time"] >= min_service

    def test_utilization_below_one_stable_system(self):
        """With arrival_rate=3/hr and ample staff the system should be stable."""
        p = ClinicParams(
            n_nurses=3,
            n_exam_rooms=4,
            arrival_rate=3.0 / 60.0,
            sim_time=20_000,
        )
        m = ClinicModel(params=p, seed=7)
        result = m.run()
        # In a stable system triage wait should be modest (< 30 min mean)
        assert result["mean_wait_triage"] < 30.0

    def test_replications_return_dataframe(self):
        p = ClinicParams(sim_time=2_000)
        m = ClinicModel(params=p, seed=0)
        df = m.run_replications(n=5)
        assert len(df) == 5
        assert "mean_total_time" in df.columns

    def test_replications_are_independent(self):
        p = ClinicParams(sim_time=2_000)
        m = ClinicModel(params=p, seed=0)
        df = m.run_replications(n=5)
        assert df["mean_total_time"].nunique() == 5


# ── TerminalModel ─────────────────────────────────────────────────────────────


class TestTerminalModel:
    def test_basic_run_returns_expected_keys(self):
        m = TerminalModel(seed=0)
        result = m.run()
        for key in ("mean_total_time", "mean_wait_gate", "mean_wait_crane", "n_trucks"):
            assert key in result, f"Missing key: {key}"

    def test_trucks_served_positive(self):
        p = TerminalParams(sim_time=8.0)
        m = TerminalModel(params=p, seed=1)
        result = m.run()
        assert result["n_trucks"] > 0

    def test_analytical_gate_wait_light_traffic(self):
        """M/M/1 gate wait ≈ rho*gate_mean/(1-rho) for λ=2/hr, μ=12/hr (rho≈0.167)."""
        lam_hr = 2.0
        gate_mean_min = 5.0
        mu_hr = 60.0 / gate_mean_min  # 12/hr
        rho = lam_hr / mu_hr          # ≈ 0.1667
        # Theoretical Wq for M/M/1: rho * (1/mu) / (1-rho) in minutes
        theoretical_wq = rho * gate_mean_min / (1 - rho)

        p = TerminalParams(
            n_gates=1, n_cranes=10,  # many cranes → crane wait negligible
            arrival_rate=lam_hr,
            gate_mean=gate_mean_min,
            crane_mean=0.01,         # near-zero crane service
            sim_time=1000.0,         # hours
        )
        m = TerminalModel(params=p, seed=0)
        result = m.run()
        assert abs(result["mean_wait_gate"] - theoretical_wq) / (theoretical_wq + 1e-9) < 0.20

    def test_more_gates_reduces_gate_wait(self):
        """Adding gates should reduce mean gate wait."""
        p1 = TerminalParams(n_gates=1, sim_time=100.0)
        p2 = TerminalParams(n_gates=3, sim_time=100.0)
        r1 = TerminalModel(params=p1, seed=99).run()
        r2 = TerminalModel(params=p2, seed=99).run()
        assert r2["mean_wait_gate"] <= r1["mean_wait_gate"]

    def test_total_time_exceeds_service_time(self):
        """Mean total time must be ≥ mean gate service + mean crane service."""
        p = TerminalParams(gate_mean=5.0, crane_mean=8.0, sim_time=100.0)
        m = TerminalModel(params=p, seed=3)
        result = m.run()
        assert result["mean_total_time"] >= p.gate_mean + p.crane_mean

    def test_replications_return_dataframe(self):
        p = TerminalParams(sim_time=10.0)
        m = TerminalModel(params=p, seed=0)
        df = m.run_replications(n=5)
        assert len(df) == 5
        assert "mean_total_time" in df.columns

    def test_replications_are_independent(self):
        p = TerminalParams(sim_time=10.0)
        m = TerminalModel(params=p, seed=0)
        df = m.run_replications(n=5)
        assert df["mean_total_time"].nunique() == 5
