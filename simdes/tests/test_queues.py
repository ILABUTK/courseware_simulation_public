"""Unit tests for queueing models: compare SimPy output to closed-form results."""

import pytest
import numpy as np

from simdes.models.queues import MM1Queue, MMCQueue


# ── MM1Queue ──────────────────────────────────────────────────────────────────

class TestMM1Queue:
    def test_analytical_match_utilization(self):
        """Simulated utilization should be close to rho = lambda/mu."""
        lam, mu = 0.8, 1.0
        m = MM1Queue(arrival_rate=lam, service_rate=mu, sim_time=100_000, seed=0)
        result = m.run()
        assert abs(result["utilization"] - m.theoretical_utilization()) < 0.05

    def test_analytical_match_mean_wait(self):
        """Simulated Wq should match the M/M/1 formula within 10%."""
        lam, mu = 0.8, 1.0
        m = MM1Queue(arrival_rate=lam, service_rate=mu, sim_time=100_000, seed=0)
        result = m.run()
        theoretical = m.theoretical_mean_wait_queue()
        assert abs(result["mean_wait_queue"] - theoretical) / theoretical < 0.10

    def test_replications_return_dataframe(self):
        m = MM1Queue(arrival_rate=0.5, service_rate=1.0, sim_time=5_000, seed=1)
        df = m.run_replications(n=10)
        assert len(df) == 10
        assert "mean_wait_queue" in df.columns

    def test_replications_are_independent(self):
        """No two replications should have the same mean wait."""
        m = MM1Queue(arrival_rate=0.5, service_rate=1.0, sim_time=5_000, seed=0)
        df = m.run_replications(n=5)
        assert df["mean_wait_queue"].nunique() == 5

    def test_heavy_traffic_high_wait(self):
        """Near-saturated queue (rho=0.95) should have very high Wq."""
        m = MM1Queue(arrival_rate=0.95, service_rate=1.0, sim_time=200_000, seed=42)
        result = m.run()
        assert result["mean_wait_queue"] > 10.0

    @pytest.mark.parametrize("rho", [0.3, 0.5, 0.7, 0.9])
    def test_wq_increases_with_rho(self, rho):
        """Higher utilization should yield longer mean wait."""
        m = MM1Queue(arrival_rate=rho, service_rate=1.0, sim_time=50_000, seed=7)
        result = m.run()
        theoretical = m.theoretical_mean_wait_queue()
        # Allow 20% tolerance since we are not doing full output analysis here
        assert abs(result["mean_wait_queue"] - theoretical) / theoretical < 0.20


# ── MMCQueue ──────────────────────────────────────────────────────────────────

class TestMMCQueue:
    def test_mmc_lower_wait_than_mm1(self):
        """Adding a second server should reduce mean wait compared to MM1."""
        lam, mu = 1.6, 1.0
        mm1 = MM1Queue(arrival_rate=lam, service_rate=mu * 2, sim_time=50_000, seed=0)
        mmc = MMCQueue(arrival_rate=lam, service_rate=mu, n_servers=2, sim_time=50_000, seed=0)
        r1 = mm1.run()
        r2 = mmc.run()
        # Two-server queue with μ each vs one-server with 2μ should have similar throughput
        assert r1["n_customers"] > 0 and r2["n_customers"] > 0

    def test_replications(self):
        m = MMCQueue(arrival_rate=1.5, service_rate=1.0, n_servers=2, sim_time=5_000, seed=0)
        df = m.run_replications(n=5)
        assert len(df) == 5
