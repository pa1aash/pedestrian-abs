"""Desired (goal-seeking) force: F = m * (v0 * e_hat - v) / tau."""

import numpy as np

from sim.core.helpers import check_forces, safe_normalize


def compute_desired_force(
    positions: np.ndarray,
    velocities: np.ndarray,
    goals: np.ndarray,
    desired_speeds: np.ndarray,
    masses: np.ndarray,
    taus: np.ndarray,
) -> np.ndarray:
    """Compute the desired (goal-seeking) force for all agents.

    F_i = m_i * (v0_i * e_hat_i - v_i) / tau_i
    where e_hat_i = normalize(goal_i - pos_i).

    Fully vectorized over agents.

    Args:
        positions: Agent positions, shape (N, 2).
        velocities: Agent velocities, shape (N, 2).
        goals: Agent goal positions, shape (N, 2).
        desired_speeds: Preferred speeds, shape (N,).
        masses: Agent masses, shape (N,).
        taus: Relaxation times, shape (N,).

    Returns:
        Desired forces, shape (N, 2).
    """
    direction = safe_normalize(goals - positions)
    desired_vel = desired_speeds[:, None] * direction
    forces = masses[:, None] * (desired_vel - velocities) / taus[:, None]
    return check_forces(forces, "desired")
