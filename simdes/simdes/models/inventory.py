"""Inventory control models: SSInventory ((s,S) policy).

The (s,S) model uses simpy.Container to track on-hand inventory.
Demand arrives as a Poisson process with random demand sizes.
Replenishment orders arrive after a stochastic lead time.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import simpy

from simdes.core.model import BaseModel


class SSInventory(BaseModel):
    """(s, S) continuous-review inventory model.

    When on-hand inventory falls to or below reorder point *s*, an order is
    placed to bring the inventory up to order-up-to level *S*.  Orders arrive
    after a random lead time drawn from an exponential distribution.

    Args:
        reorder_point: Reorder point s (trigger an order at or below this).
        order_up_to: Order-up-to level S (> s).
        demand_rate: Mean demand arrival rate (Poisson process).
        demand_mean: Mean demand size per arrival (exponential).
        lead_time_mean: Mean replenishment lead time (exponential).
        holding_cost: Holding cost per unit per time.
        backorder_cost: Backorder (shortage) cost per unit per time.
        sim_time: Simulated time horizon.
        seed: Base random seed.

    Example:
        >>> m = SSInventory(reorder_point=5, order_up_to=20, demand_rate=2.0,
        ...                 demand_mean=1.0, lead_time_mean=1.0, sim_time=5_000)
        >>> result = m.run()
        >>> "avg_inventory" in result
        True
    """

    def __init__(
        self,
        reorder_point: float,
        order_up_to: float,
        demand_rate: float = 1.0,
        demand_mean: float = 1.0,
        lead_time_mean: float = 1.0,
        holding_cost: float = 1.0,
        backorder_cost: float = 5.0,
        sim_time: float = 5_000,
        seed: int | None = None,
    ) -> None:
        super().__init__(sim_time=sim_time, seed=seed)
        if order_up_to <= reorder_point:
            raise ValueError("order_up_to must be strictly greater than reorder_point")
        self.s = reorder_point
        self.S = order_up_to
        self.demand_rate = demand_rate
        self.demand_mean = demand_mean
        self.lead_time_mean = lead_time_mean
        self.holding_cost = holding_cost
        self.backorder_cost = backorder_cost
        # Accumulators
        self._inventory_area: float = 0.0
        self._backorder_area: float = 0.0
        self._last_time: float = 0.0
        self._n_orders: int = 0
        self._n_demand_events: int = 0
        self._container: simpy.Container | None = None

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        self._inventory_area = 0.0
        self._backorder_area = 0.0
        self._last_time = 0.0
        self._n_orders = 0
        self._n_demand_events = 0
        self._container = simpy.Container(env, capacity=self.S, init=self.S)
        env.process(self._demand_process(env, rng))
        env.process(self._review_process(env, rng))

    def _accumulate(self, env: simpy.Environment) -> None:
        """Update area accumulators between events."""
        dt = env.now - self._last_time
        level = self._container.level if self._container else 0.0
        self._inventory_area += max(level, 0.0) * dt
        self._backorder_area += max(-level, 0.0) * dt
        self._last_time = env.now

    def _demand_process(
        self, env: simpy.Environment, rng: np.random.Generator
    ) -> Any:
        """Generate demand arrivals and reduce inventory."""
        assert self._container is not None
        while True:
            yield env.timeout(rng.exponential(1.0 / self.demand_rate))
            self._accumulate(env)
            demand = rng.exponential(self.demand_mean)
            qty = min(demand, self._container.level)
            if qty > 0:
                yield self._container.get(qty)
            self._n_demand_events += 1

    def _review_process(
        self, env: simpy.Environment, rng: np.random.Generator
    ) -> Any:
        """Check inventory level continuously; place orders when needed."""
        assert self._container is not None
        order_pending = False
        while True:
            yield env.timeout(0.01)  # near-continuous review
            self._accumulate(env)
            if self._container.level <= self.s and not order_pending:
                order_pending = True
                self._n_orders += 1
                order_qty = self.S - self._container.level
                lead_time = rng.exponential(self.lead_time_mean)
                env.process(self._receive_order(env, order_qty, lead_time))
                order_pending = False

    def _receive_order(
        self, env: simpy.Environment, qty: float, lead_time: float
    ) -> Any:
        assert self._container is not None
        yield env.timeout(lead_time)
        self._accumulate(env)
        space = self._container.capacity - self._container.level
        amount = min(qty, space)
        if amount > 0:
            yield self._container.put(amount)

    def _collect(self) -> dict[str, Any]:
        avg_inv = self._inventory_area / self.sim_time
        avg_bo = self._backorder_area / self.sim_time
        return {
            "avg_inventory": avg_inv,
            "avg_backorder": avg_bo,
            "avg_holding_cost": self.holding_cost * avg_inv,
            "avg_backorder_cost": self.backorder_cost * avg_bo,
            "avg_total_cost": (
                self.holding_cost * avg_inv + self.backorder_cost * avg_bo
            ),
            "n_orders": self._n_orders,
            "n_demand_events": self._n_demand_events,
        }
