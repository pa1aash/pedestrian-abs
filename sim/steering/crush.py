"""Crush regime: enhanced contact forces with no social repulsion.

Same structure as SFM contact forces but 3x body compression and 2x friction.
Activated at high densities via the hybrid model's sigmoid weighting.
Parameters: k_crush=360000, kappa_crush=480000.
"""

import numpy as np

from sim.core.agent import AgentState
from sim.core.helpers import check_forces


class CrushRegime:
    """Crush-regime contact forces (no social repulsion).

    f_crush_ij = k_crush * g(r_ij - d_ij) * n_ij
              + kappa_crush * g(r_ij - d_ij) * dot(dv_ji, t_ij) * t_ij

    Args:
        k_crush: Enhanced body compression coefficient (kg/s^2).
        kappa_crush: Enhanced sliding friction coefficient (kg/(m*s)).
    """

    def __init__(
        self,
        k_crush: float = 360000.0,
        kappa_crush: float = 480000.0,
    ):
        self.k_crush = k_crush
        self.kappa_crush = kappa_crush

    def compute_crush_forces(
        self,
        agent_state: AgentState,
        neighbor_lists: list[list[int]],
    ) -> np.ndarray:
        """Compute crush-regime contact forces for all agents.

        Args:
            agent_state: Current state of all agents.
            neighbor_lists: Per-agent list of neighbor indices.

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

                diff = pos[i] - pos[j]
                d_ij = max(np.linalg.norm(diff), 1e-6)
                n_ij = diff / d_ij
                t_ij = np.array([-n_ij[1], n_ij[0]])

                r_ij = radii[i] + radii[j]
                overlap = max(0.0, r_ij - d_ij)

                if overlap <= 0:
                    continue  # no contact, no crush force

                # Body compression (enhanced)
                f_body = self.k_crush * overlap * n_ij

                # Sliding friction (enhanced)
                dv_ji = vel[j] - vel[i]
                f_friction = self.kappa_crush * overlap * np.dot(dv_ji, t_ij) * t_ij

                forces[i] += f_body + f_friction

        return check_forces(forces, "crush")
