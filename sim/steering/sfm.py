"""Social Force Model: agent-agent repulsion, body compression, and friction.

Implements the Helbing-Molnar SFM with contact forces (Helbing et al. 2000).
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
        """Compute SFM agent-agent interaction forces.

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

                # Distance and normal (j -> i direction)
                diff = pos[i] - pos[j]
                d_ij = max(np.linalg.norm(diff), 1e-6)
                n_ij = diff / d_ij

                # Tangent: 90-degree rotation of normal
                t_ij = np.array([-n_ij[1], n_ij[0]])

                # Combined radii and overlap
                r_ij = radii[i] + radii[j]
                overlap = max(0.0, r_ij - d_ij)

                # Social repulsion (always active)
                f_social = self.A * np.exp((r_ij - d_ij) / self.B) * n_ij

                # Body compression (contact only)
                f_body = self.k * overlap * n_ij

                # Sliding friction (contact only)
                dv_ji = vel[j] - vel[i]
                f_friction = self.kappa * overlap * np.dot(dv_ji, t_ij) * t_ij

                forces[i] += f_social + f_body + f_friction

        return check_forces(forces, "SFM")
