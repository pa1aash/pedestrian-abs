"""Time-to-Collision (TTC) anticipatory force model.

Computes the earliest collision time between agent pairs and applies
an exponentially-weighted repulsive force in the avoidance direction.
Parameters: k_ttc=1.5, tau_0=3.0, tau_max=8.0.
"""

import numpy as np

from sim.core.agent import AgentState
from sim.core.helpers import check_forces, safe_normalize


class TTCForceModel:
    """Time-to-Collision anticipatory steering force.

    For each pair (i, j), computes the time tau at which they would first
    collide assuming constant velocities, then applies:
        F_mag = k_ttc * exp(-tau / tau_0) / tau^2
    in the avoidance direction (separating their predicted future positions).

    Args:
        k_ttc: Force magnitude scaling.
        tau_0: Exponential decay time constant (s).
        tau_max: Maximum lookahead horizon (s).
    """

    def __init__(
        self,
        k_ttc: float = 1.5,
        tau_0: float = 3.0,
        tau_max: float = 8.0,
    ):
        self.k_ttc = k_ttc
        self.tau_0 = tau_0
        self.tau_max = tau_max

    def compute_ttc_forces(
        self,
        agent_state: AgentState,
        neighbor_lists: list[list[int]],
    ) -> np.ndarray:
        """Compute TTC anticipatory forces for all agents.

        Args:
            agent_state: Current state of all agents.
            neighbor_lists: Per-agent list of neighbor indices from KDTree.

        Returns:
            Forces array of shape (N, 2).
        """
        n = agent_state.n
        forces = np.zeros((n, 2))
        pos = agent_state.positions
        vel = agent_state.velocities
        radii = agent_state.radii
        active = agent_state.active

        for i in range(n):
            if not active[i]:
                continue
            for j in neighbor_lists[i]:
                if j == i or not active[j]:
                    continue

                dx = pos[j] - pos[i]          # relative position
                dv = vel[i] - vel[j]          # relative velocity (i approaching j)
                r = radii[i] + radii[j]

                a = np.dot(dv, dv)            # |dv|^2
                if a < 1e-8:
                    continue                  # no relative motion

                b = -np.dot(dx, dv)           # NOTE THE NEGATIVE
                c = np.dot(dx, dx) - r * r

                disc = b * b - a * c
                if disc < 0:
                    continue                  # no intersection

                sqrt_disc = np.sqrt(disc)
                tau = (-b - sqrt_disc) / a    # THIS EXACT FORMULA

                if tau <= 0 or tau > self.tau_max:
                    continue

                # Force magnitude
                F_mag = self.k_ttc * np.exp(-tau / self.tau_0) / (tau * tau)

                # Avoidance direction: separate predicted future positions
                xi_future = pos[i] + vel[i] * tau
                xj_future = pos[j] + vel[j] * tau
                n_avoid = safe_normalize(xi_future - xj_future)
                if np.linalg.norm(n_avoid) < 1e-8:
                    n_avoid = safe_normalize(pos[i] - pos[j])

                forces[i] += F_mag * n_avoid

        return check_forces(forces, "TTC")
