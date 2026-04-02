"""Crush regime: enhanced contact forces with no social repulsion.

Same structure as SFM contact forces but 3x body compression and 2x friction.
Fully vectorized using NumPy broadcasting.
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
        """Compute crush-regime contact forces (vectorized).

        Args:
            agent_state: Current state of all agents.
            neighbor_lists: Per-agent list of neighbor indices.

        Returns:
            Forces array of shape (N, 2).
        """
        n = agent_state.n
        pos = agent_state.positions
        vel = agent_state.velocities
        radii = agent_state.radii
        active = agent_state.active

        # Pairwise differences
        diff = pos[:, None, :] - pos[None, :, :]          # (N, N, 2)
        dist = np.linalg.norm(diff, axis=2)                # (N, N)
        dist = np.maximum(dist, 1e-6)

        n_ij = diff / dist[:, :, None]                     # (N, N, 2)
        t_ij = np.stack([-n_ij[:, :, 1], n_ij[:, :, 0]], axis=2)

        r_ij = radii[:, None] + radii[None, :]
        overlap = np.maximum(0.0, r_ij - dist)

        # Mask: active, not self, in neighbor list, and overlapping
        mask = active[:, None] & active[None, :]
        np.fill_diagonal(mask, False)

        nb_mask = np.zeros((n, n), dtype=bool)
        for i in range(n):
            if active[i] and neighbor_lists[i]:
                nbs = np.array(neighbor_lists[i])
                nb_mask[i, nbs] = True
        mask &= nb_mask
        mask &= (overlap > 0)  # crush only on contact

        # Body compression (enhanced)
        body_mag = self.k_crush * overlap * mask
        f_body = body_mag[:, :, None] * n_ij

        # Sliding friction (enhanced)
        dv = vel[None, :, :] - vel[:, None, :]
        dv_dot_t = np.sum(dv * t_ij, axis=2)
        friction_mag = self.kappa_crush * overlap * dv_dot_t * mask
        f_friction = friction_mag[:, :, None] * t_ij

        forces = np.sum(f_body + f_friction, axis=1)

        return check_forces(forces, "crush")
