"""Inventory control models: SSInventory ((s, S) policy).

Continuous review of the inventory position, with full backordering.  Demand
arrives as a Poisson process with exponential demand sizes, and replenishment
orders arrive after an exponential lead time (orders may cross).

Versions of simdes before 0.2.1 implemented this model incorrectly (they
ordered on on-hand stock, lost unmet demand and discarded ordered units), so
their results should not be used.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import simpy

from simdes.core.model import BaseModel


class SSInventory(BaseModel):
    """(s, S) continuous-review inventory model with backorders.

    The *inventory position* (on hand + on order - backorders) is reviewed
    after every demand.  When it is at or below the reorder point *s*, an
    order of size ``S - position`` is placed, which brings the position back
    to the order-up-to level *S*.  Any number of orders may be outstanding.

    Demand that cannot be met from stock is backordered, and each receipt
    fills backorders first; the rest goes on the shelf.  Every ordered unit is
    received.  A run starts with *S* units on hand and nothing on order.

    Demands and lead times use separate random streams, so two policies run
    with the same seed see the same demands (common random numbers).

    To use other distributions, subclass and override
    :meth:`_interarrival_time`, :meth:`_demand_size` or :meth:`_lead_time`.

    Args:
        reorder_point: Reorder point s (order when the position is at or
            below this).
        order_up_to: Order-up-to level S (> s).
        demand_rate: Mean demand arrival rate (Poisson process).
        demand_mean: Mean demand size per arrival (exponential).
        lead_time_mean: Mean replenishment lead time (exponential).
        holding_cost: Holding cost per unit on hand per unit time.
        backorder_cost: Backorder (shortage) cost per unit backordered per
            unit time.
        sim_time: Simulated time horizon.
        seed: Base random seed.

    Results of :meth:`run`:
        ``avg_inventory`` and ``avg_backorder`` are time averages of the units
        on hand and backordered over the whole horizon (no warm-up deletion).
        ``avg_holding_cost``, ``avg_backorder_cost`` and their sum
        ``avg_total_cost`` are costs per unit time; ordering cost is not
        included (for a cost K per order, add ``K * n_orders / sim_time``).
        ``n_orders`` and ``n_demand_events`` count orders placed and demands.
        ``fill_rate`` is the fraction of demanded units met immediately from
        stock (NaN if there was no demand).

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
        self._reset_state()

    # ------------------------------------------------------------------
    # Random inputs (override to change the distributions)
    # ------------------------------------------------------------------

    def _interarrival_time(self, rng: np.random.Generator) -> float:
        """Time to the next demand."""
        return float(rng.exponential(1.0 / self.demand_rate))

    def _demand_size(self, rng: np.random.Generator) -> float:
        """Units asked for by one demand."""
        return float(rng.exponential(self.demand_mean))

    def _lead_time(self, rng: np.random.Generator) -> float:
        """Lead time of one replenishment order."""
        return float(rng.exponential(self.lead_time_mean))

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        # Net inventory = on hand - backorders (at most one of the two is > 0).
        self._net: float = float(self.S)
        self._on_order: float = 0.0
        self._outstanding: int = 0
        self._inventory_area: float = 0.0
        self._backorder_area: float = 0.0
        self._last_time: float = 0.0
        self._n_orders: int = 0
        self._n_demand_events: int = 0
        self._units_demanded: float = 0.0
        self._units_filled: float = 0.0
        self._units_ordered: float = 0.0
        self._units_received: float = 0.0

    def _position(self) -> float:
        """Inventory position: on hand + on order - backorders."""
        return self._net + self._on_order

    def _accumulate(self, now: float) -> None:
        """Add the area since the last change.  Call before every state change."""
        dt = now - self._last_time
        self._inventory_area += max(self._net, 0.0) * dt
        self._backorder_area += max(-self._net, 0.0) * dt
        self._last_time = now

    # ------------------------------------------------------------------
    # Processes
    # ------------------------------------------------------------------

    def _build(self, env: simpy.Environment, rng: np.random.Generator) -> None:
        self._reset_state()
        demand_rng, lead_rng = rng.spawn(2)
        env.process(self._demand_process(env, demand_rng, lead_rng))

    def _demand_process(
        self,
        env: simpy.Environment,
        demand_rng: np.random.Generator,
        lead_rng: np.random.Generator,
    ) -> Any:
        """Generate demands; review the inventory position after each one."""
        while True:
            yield env.timeout(self._interarrival_time(demand_rng))
            size = self._demand_size(demand_rng)
            self._accumulate(env.now)
            self._units_filled += min(size, max(self._net, 0.0))
            self._units_demanded += size
            self._net -= size  # a shortfall becomes a backorder
            self._n_demand_events += 1
            self._review(env, lead_rng)

    def _review(self, env: simpy.Environment, lead_rng: np.random.Generator) -> None:
        """Order up to S if the inventory position is at or below s.

        Only a demand lowers the position (a receipt leaves it unchanged), so
        reviewing after each demand is continuous review.
        """
        position = self._position()
        if position > self.s:
            return
        quantity = self.S - position
        self._on_order += quantity
        self._outstanding += 1
        self._n_orders += 1
        self._units_ordered += quantity
        lead_time = self._lead_time(lead_rng)
        env.process(self._receive_order(env, quantity, lead_time))

    def _receive_order(
        self, env: simpy.Environment, quantity: float, lead_time: float
    ) -> Any:
        """Receive one order: backorders are filled first, the rest is stocked."""
        yield env.timeout(lead_time)
        self._accumulate(env.now)
        self._net += quantity
        self._units_received += quantity
        self._outstanding -= 1
        # Clear floating-point residue once nothing is in transit.
        self._on_order = self._on_order - quantity if self._outstanding else 0.0

    def _collect(self) -> dict[str, Any]:
        self._accumulate(self.sim_time)  # close the last interval
        avg_inv = self._inventory_area / self.sim_time
        avg_bo = self._backorder_area / self.sim_time
        fill_rate = (
            self._units_filled / self._units_demanded
            if self._units_demanded > 0
            else float("nan")
        )
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
            "fill_rate": fill_rate,
        }
