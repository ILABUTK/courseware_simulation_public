"""Tests for SSInventory against hand calculations and inventory theory."""

import math

import numpy as np
import pytest
import simpy
from scipy import stats

from simdes.models.inventory import SSInventory


class FixedInventory(SSInventory):
    """SSInventory with constant interarrival times, demand sizes and lead times.

    Also records the inventory position before and after every review.
    """

    def __init__(
        self, s, S, *, every=1.0, size=1.0, lead=1.0, sim_time=100.0, **kwargs
    ):
        super().__init__(s, S, sim_time=sim_time, **kwargs)
        self.every, self.size, self.lead = every, size, lead
        self.reviews: list[tuple[float, float, float, int]] = []

    def _interarrival_time(self, rng):
        return self.every

    def _demand_size(self, rng):
        return self.size

    def _lead_time(self, rng):
        return self.lead

    def _build(self, env, rng):
        self.reviews = []
        super()._build(env, rng)

    def _review(self, env: simpy.Environment, lead_rng: np.random.Generator) -> None:
        before, orders = self._position(), self._n_orders
        super()._review(env, lead_rng)
        self.reviews.append(
            (env.now, before, self._position(), self._n_orders - orders)
        )


class PoissonUnitDemand(SSInventory):
    """Poisson demand of one unit at a time (lead times stay exponential)."""

    def _demand_size(self, rng):
        return 1.0


class ConstantLeadTime(SSInventory):
    """The default demand with a fixed lead time."""

    def _lead_time(self, rng):
        return self.lead_time_mean


class RecordedRun(SSInventory):
    """The default model, recording demands, orders and the position."""

    def _build(self, env, rng):
        self.demands: list[tuple[float, float]] = []
        self.orders: list[tuple[float, float, float]] = []  # (time, position, qty)
        self.positions: list[float] = []
        super()._build(env, rng)

    def _demand_size(self, rng):
        size = super()._demand_size(rng)
        self.demands.append((self._env.now, size))
        return size

    def _review(self, env, lead_rng):
        before, ordered = self._position(), self._units_ordered
        super()._review(env, lead_rng)
        if self._units_ordered > ordered:
            self.orders.append((env.now, before, self._units_ordered - ordered))
        self.positions.append(self._position())


# ----------------------------------------------------------------------
# Basics
# ----------------------------------------------------------------------


class TestInterface:
    def test_result_keys(self):
        result = SSInventory(5, 20, demand_rate=2.0, sim_time=200, seed=0).run()
        assert set(result) == {
            "avg_inventory",
            "avg_backorder",
            "avg_holding_cost",
            "avg_backorder_cost",
            "avg_total_cost",
            "n_orders",
            "n_demand_events",
            "fill_rate",
        }

    def test_costs_are_rates_times_time_averages(self):
        r = SSInventory(
            2,
            6,
            demand_rate=4.0,
            lead_time_mean=2.0,
            holding_cost=0.7,
            backorder_cost=9.0,
            sim_time=500,
            seed=3,
        ).run()
        assert r["avg_holding_cost"] == pytest.approx(0.7 * r["avg_inventory"])
        assert r["avg_backorder_cost"] == pytest.approx(9.0 * r["avg_backorder"])
        assert r["avg_total_cost"] == pytest.approx(
            r["avg_holding_cost"] + r["avg_backorder_cost"]
        )

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            SSInventory(reorder_point=20, order_up_to=10)

    def test_same_seed_same_results_and_rerun(self):
        a = SSInventory(5, 20, demand_rate=3.0, sim_time=1_000, seed=11)
        b = SSInventory(5, 20, demand_rate=3.0, sim_time=1_000, seed=11)
        first = a.run()
        assert first == b.run()
        assert first == a.run()  # state is reset between runs
        assert (
            first != SSInventory(5, 20, demand_rate=3.0, sim_time=1_000, seed=12).run()
        )

    def test_replications(self):
        m = SSInventory(5, 20, demand_rate=2.0, sim_time=1_000, seed=0)
        df = m.run_replications(n=5)
        assert len(df) == 5
        assert df["avg_total_cost"].nunique() == 5

    def test_policies_share_the_demand_stream(self):
        """Common random numbers: the policy must not change the demands."""
        a = RecordedRun(
            5, 20, demand_rate=3.0, lead_time_mean=2.0, sim_time=300, seed=4
        )
        b = RecordedRun(
            30, 90, demand_rate=3.0, lead_time_mean=2.0, sim_time=300, seed=4
        )
        a.run(), b.run()
        assert a.demands == b.demands

    def test_no_demand_keeps_stock_at_S_to_the_horizon(self):
        r = FixedInventory(5, 20, every=1_000.0, sim_time=10.0).run()
        assert r["avg_inventory"] == 20.0
        assert r["avg_backorder"] == 0.0
        assert r["n_orders"] == 0
        assert math.isnan(r["fill_rate"])


# ----------------------------------------------------------------------
# Hand calculations (deterministic inputs)
# ----------------------------------------------------------------------


class TestHandCalculations:
    def test_sawtooth_trace(self):
        """s=10, S=50, 10 units every 3 days, lead time 5 days, 41 days.

        Orders at t = 12, 24, 36 (position 10), receipts at 17 and 29.  Area
        on hand: 450 over [0, 17), then 220 per 12-day cycle.
        """
        m = FixedInventory(10, 50, every=3.0, size=10.0, lead=5.0, sim_time=41.0)
        r = m.run()
        assert [t for t, *_, n in m.reviews if n] == [12.0, 24.0, 36.0]
        assert r["n_orders"] == 3
        assert r["n_demand_events"] == 13
        assert r["avg_inventory"] == pytest.approx((450 + 2 * 220) / 41)
        assert r["avg_backorder"] == 0.0
        assert r["fill_rate"] == 1.0

    def test_backorders_are_kept_and_filled_first(self):
        """The same system with an 8-day lead time, 23 days.

        Demand at t=18 finds nothing: 10 units are backordered until the 40
        units arrive at t=20, of which 30 reach the shelf.
        """
        m = FixedInventory(10, 50, every=3.0, size=10.0, lead=8.0, sim_time=23.0)
        r = m.run()
        # [0,15): 3 x (50+40+30+20+10) = 450; [15,20): 0; [20,21): 30; [21,23): 20
        assert r["avg_inventory"] == pytest.approx((450 + 30 + 2 * 20) / 23)
        assert r["avg_backorder"] == pytest.approx(10 * 2 / 23)
        assert r["fill_rate"] == pytest.approx(6 / 7)  # 6 of 7 demands from stock
        assert r["n_orders"] == 1

    def test_backorder_area_is_closed_at_the_horizon(self):
        """Nothing arrives: net inventory is 3, 2, 1, 0, -1, ... each day."""
        r = FixedInventory(0, 3, lead=1_000.0, sim_time=6.5).run()
        assert r["avg_inventory"] == pytest.approx((3 + 2 + 1) / 6.5)
        assert r["avg_backorder"] == pytest.approx((1 + 2 + 3 * 0.5) / 6.5)
        assert r["n_orders"] == 2  # at t = 3 and 6, although nothing has arrived

    def test_several_orders_outstanding_and_none_while_position_above_s(self):
        """s=30, S=50, 10 units a day, lead 5: an order every 2 days."""
        m = FixedInventory(30, 50, size=10.0, lead=5.0, sim_time=12.5)
        r = m.run()
        assert [t for t, *_, n in m.reviews if n] == [2, 4, 6, 8, 10, 12]
        for _, before, after, n in m.reviews:
            assert n == (1 if before <= 30 else 0)
            assert after == (50 if n else before)
        # on hand 50, 40, 30, 20, 10 on [0,5); empty from t = 5 on
        assert r["avg_inventory"] == pytest.approx(150 / 12.5)
        assert r["n_orders"] == 6
        assert m._units_ordered == 120.0
        assert m._units_received == 60.0  # orders of t = 2, 4, 6 arrived
        assert m._net == pytest.approx(50 + 60 - 120)

    @pytest.mark.parametrize("periods", [1, 20])
    def test_eoq_average_inventory(self, periods):
        """Unit demand each day, lead time 4.5, s=4, S=4+Q: the EOQ sawtooth.

        The first order is placed at t=Q.  Until the first receipt at Q+4.5 the
        area is S(S+1)/2; every later cycle of length Q has area Q^2/2.
        """
        q = 10
        S = 4 + q
        horizon = q + 4.5 + periods * q
        r = FixedInventory(4, S, lead=4.5, sim_time=horizon).run()
        assert r["avg_inventory"] == pytest.approx(
            (S * (S + 1) / 2 + periods * q**2 / 2) / horizon
        )
        assert r["avg_backorder"] == 0.0
        assert r["n_orders"] == periods + 1

    def test_eoq_is_the_cheapest_order_quantity(self):
        """K=50, h=1, D=1 per day: Q* = sqrt(2 K D / h) = 10, cost 10 a day."""
        K, h = 50.0, 1.0
        costs = {}
        for q in (5, 8, 10, 12, 20):
            horizon = 20_000.0
            r = FixedInventory(4, 4 + q, lead=4.5, sim_time=horizon).run()
            costs[q] = h * r["avg_inventory"] + K * r["n_orders"] / horizon
        assert min(costs, key=costs.get) == 10
        assert costs[10] == pytest.approx(math.sqrt(2 * K * h), rel=0.01)


# ----------------------------------------------------------------------
# Stochastic theory
# ----------------------------------------------------------------------


class TestTheory:
    @pytest.mark.parametrize("S", [3, 6, 10])
    def test_base_stock_matches_palm(self, S):
        """Base stock (s = S-1), Poisson unit demand, any lead time.

        Palm: the number of outstanding orders N is Poisson(lambda E[L]).  So
        on hand = (S-N)+, backorders = (N-S)+ and, by PASTA, the fill rate is
        P(N < S).
        """
        lam, lead = 2.0, 2.5
        m = PoissonUnitDemand(
            S - 1, S, demand_rate=lam, lead_time_mean=lead, sim_time=100_000, seed=7
        )
        r = m.run()
        n = np.arange(0, 80)
        p = stats.poisson.pmf(n, lam * lead)
        on_hand = float(np.sum(np.maximum(S - n, 0) * p))
        backorders = float(np.sum(np.maximum(n - S, 0) * p))
        assert r["avg_inventory"] == pytest.approx(on_hand, rel=0.03, abs=0.01)
        assert r["avg_backorder"] == pytest.approx(backorders, rel=0.03, abs=0.01)
        assert r["fill_rate"] == pytest.approx(
            stats.poisson.cdf(S - 1, lam * lead), abs=0.005
        )
        assert r["n_orders"] == r["n_demand_events"]  # one order per unit demanded

    @pytest.mark.parametrize(
        "s, S, mean_size, tol",  # tol: about 3 standard errors of the net inventory
        [(5, 40, 2.0, 0.45), (10, 20, 1.0, 0.17), (2, 6, 1.0, 0.12)],
    )
    def test_order_frequency_and_net_inventory(self, s, S, mean_size, tol):
        """Renewal theory for exponential demand sizes, and Little's law.

        With D = S - s, an order cycle holds 1 + Poisson(D/m) demands, so orders
        come at rate lambda / (1 + D/m).  The position is S with probability
        1/(1 + D/m) and otherwise uniform on (s, S).  Units spend E[L] in the
        pipeline, so E[net] = E[position] - lambda m E[L], although orders cross.
        """
        lam, lead, T = 4.0, 2.0, 100_000.0
        r = SSInventory(
            s,
            S,
            demand_rate=lam,
            demand_mean=mean_size,
            lead_time_mean=lead,
            sim_time=T,
            seed=5,
        ).run()
        per_cycle = 1 + (S - s) / mean_size
        position = (S + (S - s) / mean_size * (s + S) / 2) / per_cycle
        assert r["n_orders"] / T == pytest.approx(lam / per_cycle, rel=0.01)
        net = r["avg_inventory"] - r["avg_backorder"]
        assert net == pytest.approx(position - lam * mean_size * lead, abs=tol)
        assert r["avg_backorder"] > 0.0

    def test_net_inventory_is_position_minus_lead_time_demand(self):
        """Constant lead time L: net(t + L) = position(t) - demand in (t, t + L].

        The two terms on the right are independent, so the whole distribution of
        net inventory follows; check on hand and backorders separately.
        """
        s, S, lam, L = 8, 20, 3.0, 2.0
        r = ConstantLeadTime(
            s, S, demand_rate=lam, lead_time_mean=L, sim_time=100_000, seed=2
        ).run()
        rng = np.random.default_rng(123)
        n = 2_000_000
        at_S = rng.random(n) < 1 / (1 + (S - s))
        position = np.where(at_S, S, rng.uniform(s, S, n))
        demand = rng.gamma(rng.poisson(lam * L, n), 1.0)
        net = position - demand
        assert r["avg_inventory"] == pytest.approx(np.maximum(net, 0).mean(), rel=0.02)
        assert r["avg_backorder"] == pytest.approx(np.maximum(-net, 0).mean(), rel=0.03)


# ----------------------------------------------------------------------
# Bookkeeping on a random run
# ----------------------------------------------------------------------


class TestBalances:
    @pytest.fixture(scope="class")
    def run(self):
        # lead-time demand (8) is far above s: shortages and crossing orders
        m = RecordedRun(
            2, 6, demand_rate=4.0, lead_time_mean=2.0, sim_time=2_000, seed=1
        )
        return m, m.run()

    def test_position_stays_above_s_and_at_most_S(self, run):
        m, _ = run
        assert min(m.positions) > 2
        assert max(m.positions) <= 6 + 1e-9

    def test_orders_only_at_or_below_s_and_up_to_S(self, run):
        m, r = run
        assert len(m.orders) == r["n_orders"]
        for _, before, quantity in m.orders:
            assert before <= 2
            assert before + quantity == pytest.approx(6)

    def test_no_demand_is_lost_and_no_receipt_is_clipped(self, run):
        m, r = run
        demanded = sum(size for _, size in m.demands)
        assert m._units_demanded == pytest.approx(demanded)
        assert m._net == pytest.approx(6 + m._units_received - demanded)
        assert m._units_received + m._on_order == pytest.approx(m._units_ordered)
        assert m._units_ordered == pytest.approx(sum(q for *_, q in m.orders))

    def test_shortages_are_backordered(self, run):
        _, r = run
        assert r["avg_backorder"] > 0.5
        assert 0.0 < r["fill_rate"] < 1.0
        # about one order per (1 + S - s) = 5 demands, never one per tick
        assert r["n_orders"] / r["n_demand_events"] == pytest.approx(0.2, abs=0.02)
