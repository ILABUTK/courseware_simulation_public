"""Unit tests for SSInventory model."""

import pytest

from simdes.models.inventory import SSInventory


class TestSSInventory:
    def test_basic_run(self):
        m = SSInventory(
            reorder_point=5, order_up_to=20,
            demand_rate=2.0, demand_mean=1.0,
            lead_time_mean=1.0, sim_time=2_000, seed=0,
        )
        result = m.run()
        assert "avg_inventory" in result
        assert "avg_total_cost" in result
        assert result["avg_inventory"] >= 0.0
        assert result["avg_total_cost"] >= 0.0

    def test_replications(self):
        m = SSInventory(
            reorder_point=5, order_up_to=20,
            demand_rate=2.0, sim_time=1_000, seed=0,
        )
        df = m.run_replications(n=5)
        assert len(df) == 5
        assert "avg_total_cost" in df.columns

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            SSInventory(reorder_point=20, order_up_to=10)

    def test_higher_backorder_cost_increases_total_cost(self):
        """Increasing backorder cost should not decrease total cost."""
        m1 = SSInventory(reorder_point=5, order_up_to=20, demand_rate=3.0,
                         backorder_cost=5.0, sim_time=5_000, seed=0)
        m2 = SSInventory(reorder_point=5, order_up_to=20, demand_rate=3.0,
                         backorder_cost=20.0, sim_time=5_000, seed=0)
        r1 = m1.run()
        r2 = m2.run()
        # Higher backorder cost → higher or equal total cost
        assert r2["avg_total_cost"] >= r1["avg_total_cost"] - 0.5  # allow small noise
