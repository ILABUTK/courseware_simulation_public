"""Thin helpers around SimPy resource types."""

from __future__ import annotations

import simpy


def make_resource(env: simpy.Environment, capacity: int = 1) -> simpy.Resource:
    """Create a FIFO resource with the given capacity."""
    return simpy.Resource(env, capacity=capacity)


def make_priority_resource(
    env: simpy.Environment, capacity: int = 1
) -> simpy.PriorityResource:
    """Create a priority resource (lower priority value = higher priority)."""
    return simpy.PriorityResource(env, capacity=capacity)


def make_store(
    env: simpy.Environment, capacity: float = float("inf")
) -> simpy.Store:
    """Create a FIFO store with optional finite capacity."""
    return simpy.Store(env, capacity=capacity)


def make_container(
    env: simpy.Environment, capacity: float, init: float = 0.0
) -> simpy.Container:
    """Create a container with given capacity and initial fill level."""
    return simpy.Container(env, capacity=capacity, init=init)
