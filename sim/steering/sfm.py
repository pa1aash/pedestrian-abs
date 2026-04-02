"""Social Force Model: agent-agent repulsion, body compression, and friction.

Implements the Helbing-Molnar SFM with contact forces (Helbing et al. 2000).
Fully vectorized using NumPy broadcasting (O(N^2) memory, fine for N<=1000).
Parameters: A=2000N, B=0.08m, k=120000 kg/s^2, kappa=240000 kg/(m*s).
"""

import numpy as np

from sim.core.agent import AgentState
from sim.core.helpers import check_forces


class SocialForceModel:
    """Social Force Model for agent-agent interaction.

    Forces:
        f_ij = A*exp((r_ij - d_ij)/B) * n_ij                   [social, always]
             + k * g(r_ij - d_ij) * n_ij                        [body, contact]
             + kappa * g(r_ij - d_ij) * dot(dv_ji, t_ij) * t_ij [friction, contact]

    Args:
        A: Social repulsion strength (N).
        B: Social repulsion range (m).
        k: Body compression coefficient (kg/s^2).
        kappa: Sliding friction coefficient (kg/(m*s)).
    """

    def __init__(
        self,
        A: float = 2000.0,
        B: float = 0.08,
        k: float = 120000.0,
        kappa: float = 240000.0,
    ):
        self.A = A
        self.B = B
        self.k = k
        self.kappa = kappa

    def compute_agent_forces(
        self,
        agent_state: AgentState,
        neighbor_lists: list[list[int]],
    ) -> np.ndarray:
        """Compute SFM agent-agent interaction forces (vectorized).

        Args:
            agent_state: Current state of all agents.
            neighbor_lists: Per-agent list of neighbor indices from KDTree.

        Returns:
            Forces array of shape (N, 2).
        """
        n = agent_state.n
        pos = agent_state.positions    # (N, 2)
        vel = agent_state.velocities   # (N, 2)
        radii = agent_state.radii      # (N,)
        active = agent_state.active    # (N,)

        # Pairwise differences: diff[i,j] = pos[i] - pos[j]  (j->i direction)
        diff = pos[:, None, :] - pos[None, :, :]          # (N, N, 2)
        dist = np.linalg.norm(diff, axis=2)                # (N, N)
        dist = np.maximum(dist, 1e-6)                      # avoid division by zero

        # Normal and tangent vectors
        n_ij = diff / dist[:, :, None]                     # (N, N, 2)
        t_ij = np.stack([-n_ij[:, :, 1], n_ij[:, :, 0]], axis=2)  # (N, N, 2)

        # Combined radii and overlap
        r_ij = radii[:, None] + radii[None, :]             # (N, N)
        overlap = np.maximum(0.0, r_ij - dist)             # (N, N)

        # Interaction mask: active pairs, not self, within neighbor radius
        mask = active[:, None] & active[None, :]           # (N, N)
        np.fill_diagonal(mask, False)

        # Build neighbor mask from neighbor_lists for sparsity
        nb_mask = np.zeros((n, n), dtype=bool)
        for i in range(n):
            if active[i] and neighbor_lists[i]:
                nbs = np.array(neighbor_lists[i])
                nb_mask[i, nbs] = True
        mask &= nb_mask

        # Social repulsion (always active for valid pairs)
        social_mag = self.A * np.exp((r_ij - dist) / self.B)  # (N, N)
        social_mag *= mask
        f_social = social_mag[:, :, None] * n_ij              # (N, N, 2)

        # Body compression (contact only)
        body_mag = self.k * overlap * mask                     # (N, N)
        f_body = body_mag[:, :, None] * n_ij                   # (N, N, 2)

        # Sliding friction: dv_ji = vel[j] - vel[i]
        dv = vel[None, :, :] - vel[:, None, :]                # (N, N, 2)
        dv_dot_t = np.sum(dv * t_ij, axis=2)                  # (N, N)
        friction_mag = self.kappa * overlap * dv_dot_t * mask  # (N, N)
        f_friction = friction_mag[:, :, None] * t_ij           # (N, N, 2)

        # Sum over j for each i
        forces = np.sum(f_social + f_body + f_friction, axis=1)  # (N, 2)

        return check_forces(forces, "SFM")
