"""Composite risk metric combining density, pressure, and density gradient.

R = (rho_hat / rho_ref) * [1 + P/P_ref + |grad_rho|/grad_rho_ref]
where rho_hat = max(rho_V, rho_KDE), P = rho_hat * sigma_v.

Risk levels: <1 normal, 1-2 elevated, 2-3 high, >=3 critical.
"""

import numpy as np


class CompositeRiskMetric:
    """Composite crowd-crush risk metric.

    Args:
        rho_ref: Reference density for normalization.
        P_ref: Reference pressure for normalization.
        grad_rho_ref: Reference density gradient for normalization.
    """

    def __init__(
        self,
        rho_ref: float = 6.0,
        P_ref: float = 3.0,
        grad_rho_ref: float = 4.0,
    ):
        self.rho_ref = rho_ref
        self.P_ref = P_ref
        self.grad_rho_ref = grad_rho_ref

    def compute(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        rho_V: np.ndarray,
        rho_KDE: np.ndarray,
        neighbor_lists: list[list[int]],
    ) -> np.ndarray:
        """Compute composite risk at each agent position.

        Args:
            positions: Agent positions, shape (N, 2).
            velocities: Agent velocities, shape (N, 2).
            rho_V: Voronoi density, shape (N,).
            rho_KDE: KDE density, shape (N,).
            neighbor_lists: Per-agent neighbor indices.

        Returns:
            Risk values, shape (N,). <1 normal, 1-2 elevated, >=3 critical.
        """
        n = len(positions)
        if n == 0:
            return np.array([])

        # Combined density
        rho_hat = np.maximum(rho_V, rho_KDE)

        # Speed variance per neighborhood
        speeds = np.linalg.norm(velocities, axis=1)
        sigma_v = np.zeros(n)
        for i in range(n):
            nbs = neighbor_lists[i]
            if len(nbs) > 1:
                sigma_v[i] = np.std(speeds[nbs])

        # Crowd pressure
        P = rho_hat * sigma_v

        # Density gradient (finite difference from neighbors)
        grad_rho = np.zeros(n)
        for i in range(n):
            nbs = [j for j in neighbor_lists[i] if j != i]
            if len(nbs) == 0:
                continue
            # Weighted gradient estimate
            dx = positions[nbs] - positions[i]
            dist = np.linalg.norm(dx, axis=1)
            safe_dist = np.maximum(dist, 1e-6)
            drho = rho_hat[nbs] - rho_hat[i]
            # Gradient magnitude: average |drho/dr|
            grad_rho[i] = np.mean(np.abs(drho) / safe_dist)

        # Composite risk
        R = (rho_hat / self.rho_ref) * (
            1.0 + P / self.P_ref + grad_rho / self.grad_rho_ref
        )
        return R
