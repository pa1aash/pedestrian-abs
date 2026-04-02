"""Tests for desired (goal-seeking) force computation."""

import numpy as np
import pytest

from sim.steering.desired import compute_desired_force


def test_stationary_agent():
    """Agent at origin, goal (5,0), v=0 -> F points right, magnitude ~214.4N."""
    positions = np.array([[0.0, 0.0]])
    velocities = np.array([[0.0, 0.0]])
    goals = np.array([[5.0, 0.0]])
    desired_speeds = np.array([1.34])
    masses = np.array([80.0])
    taus = np.array([0.5])

    forces = compute_desired_force(positions, velocities, goals, desired_speeds, masses, taus)

    # F = m*(v0*e - v)/tau = 80*(1.34*[1,0] - [0,0])/0.5 = 80*2.68*[1,0] = [214.4, 0]
    expected_fx = 80.0 * 1.34 / 0.5
    np.testing.assert_allclose(forces[0, 0], expected_fx, atol=0.1)
    np.testing.assert_allclose(forces[0, 1], 0.0, atol=1e-10)


def test_at_desired_speed():
    """Agent already at desired speed toward goal -> F ~0."""
    positions = np.array([[0.0, 0.0]])
    velocities = np.array([[1.34, 0.0]])
    goals = np.array([[5.0, 0.0]])
    desired_speeds = np.array([1.34])
    masses = np.array([80.0])
    taus = np.array([0.5])

    forces = compute_desired_force(positions, velocities, goals, desired_speeds, masses, taus)

    np.testing.assert_allclose(forces[0], [0.0, 0.0], atol=1e-6)


def test_diagonal_goal():
    """Agent with diagonal goal gets force in both components."""
    positions = np.array([[0.0, 0.0]])
    velocities = np.array([[0.0, 0.0]])
    goals = np.array([[5.0, 5.0]])
    desired_speeds = np.array([1.34])
    masses = np.array([80.0])
    taus = np.array([0.5])

    forces = compute_desired_force(positions, velocities, goals, desired_speeds, masses, taus)

    # Direction is (1/sqrt(2), 1/sqrt(2))
    assert forces[0, 0] > 0
    assert forces[0, 1] > 0
    np.testing.assert_allclose(forces[0, 0], forces[0, 1], atol=1e-10)


def test_multiple_agents():
    """Vectorized computation across multiple agents."""
    n = 20
    rng = np.random.Generator(np.random.PCG64(42))
    positions = rng.uniform(0, 10, (n, 2))
    velocities = rng.uniform(-1, 1, (n, 2))
    goals = rng.uniform(8, 15, (n, 2))
    desired_speeds = np.full(n, 1.34)
    masses = np.full(n, 80.0)
    taus = np.full(n, 0.5)

    forces = compute_desired_force(positions, velocities, goals, desired_speeds, masses, taus)

    assert forces.shape == (n, 2)
    assert not np.any(np.isnan(forces))


def test_agent_at_goal():
    """Agent already at goal position -> direction is zero, force resists current velocity."""
    positions = np.array([[5.0, 5.0]])
    velocities = np.array([[1.0, 0.0]])
    goals = np.array([[5.0, 5.0]])
    desired_speeds = np.array([1.34])
    masses = np.array([80.0])
    taus = np.array([0.5])

    forces = compute_desired_force(positions, velocities, goals, desired_speeds, masses, taus)

    # e_hat = 0 (at goal), so F = m*(0 - v)/tau = -m*v/tau
    expected = -80.0 * np.array([1.0, 0.0]) / 0.5
    np.testing.assert_allclose(forces[0], expected, atol=1e-6)
