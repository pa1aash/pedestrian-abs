"""Bidirectional scenario: 20x3.6m corridor with two opposing groups."""

import numpy as np

from sim.core.agent import AgentState
from sim.core.world import Wall, World
from sim.scenarios.base import Scenario


class BidirectionalScenario(Scenario):
    """20x3.6m corridor with agents walking in both directions.

    Args:
        n_per_direction: Number of agents per direction.
    """

    def __init__(self, n_per_direction: int = 150):
        self.n_per_direction = n_per_direction

    def build(self, seed: int = 42) -> tuple[World, AgentState]:
        """Build bidirectional corridor.

        Left group: spawn x in [0.5, 3], goal at (20.5, y_i).
        Right group: spawn x in [17, 19.5], goal at (-0.5, y_i).
        """
        walls = [
            Wall(np.array([0.0, 0.0]), np.array([20.0, 0.0])),
            Wall(np.array([20.0, 0.0]), np.array([20.0, 3.6])),
            Wall(np.array([20.0, 3.6]), np.array([0.0, 3.6])),
            Wall(np.array([0.0, 3.6]), np.array([0.0, 0.0])),
        ]
        world = World(walls)

        n_left = self.n_per_direction
        n_right = self.n_per_direction

        # Left group
        state_left = AgentState.create(
            n_left,
            spawn_area=(0.5, 3.0, 0.3, 3.3),
            goals=np.array([20.5, 1.8]),
            seed=seed,
        )
        state_left.goals[:, 1] = state_left.positions[:, 1]

        # Right group
        state_right = AgentState.create(
            n_right,
            spawn_area=(17.0, 19.5, 0.3, 3.3),
            goals=np.array([-0.5, 1.8]),
            seed=seed + 1000,
        )
        state_right.goals[:, 1] = state_right.positions[:, 1]

        # Merge
        state = AgentState(
            positions=np.vstack([state_left.positions, state_right.positions]),
            velocities=np.vstack([state_left.velocities, state_right.velocities]),
            goals=np.vstack([state_left.goals, state_right.goals]),
            radii=np.concatenate([state_left.radii, state_right.radii]),
            desired_speeds=np.concatenate([state_left.desired_speeds, state_right.desired_speeds]),
            masses=np.concatenate([state_left.masses, state_right.masses]),
            taus=np.concatenate([state_left.taus, state_right.taus]),
            active=np.concatenate([state_left.active, state_right.active]),
        )
        return world, state

    def is_complete(self, agent_state: AgentState, time: float) -> bool:
        """Complete when all agents have exited."""
        return agent_state.n_active == 0
