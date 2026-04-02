"""Crossing scenario: 90-degree intersection with two streams."""

import numpy as np

from sim.core.agent import AgentState
from sim.core.world import Wall, World
from sim.scenarios.base import Scenario


class CrossingScenario(Scenario):
    """T-intersection with two perpendicular pedestrian streams.

    10x10 central area with approach corridors from bottom and left.

    Args:
        n_per_stream: Number of agents per stream.
    """

    def __init__(self, n_per_stream: int = 100):
        self.n_per_stream = n_per_stream

    def build(self, seed: int = 42) -> tuple[World, AgentState]:
        """Build crossing world with two streams.

        Stream 1 (bottom): spawn y in [-5, -2], goal at (5, 15).
        Stream 2 (left): spawn x in [-5, -2], goal at (15, 5).
        """
        # Central 10x10 area from (0,0) to (10,10)
        # Bottom corridor: x in [3, 7], y in [-6, 0]
        # Left corridor: x in [-6, 0], y in [3, 7]
        walls = [
            # Central area outer walls (with gaps for corridors)
            Wall(np.array([0.0, 0.0]), np.array([3.0, 0.0])),     # bottom-left
            Wall(np.array([7.0, 0.0]), np.array([10.0, 0.0])),    # bottom-right
            Wall(np.array([10.0, 0.0]), np.array([10.0, 10.0])),  # right
            Wall(np.array([10.0, 10.0]), np.array([0.0, 10.0])),  # top
            Wall(np.array([0.0, 10.0]), np.array([0.0, 7.0])),    # left-top
            Wall(np.array([0.0, 3.0]), np.array([0.0, 0.0])),     # left-bottom
            # Bottom corridor walls
            Wall(np.array([3.0, 0.0]), np.array([3.0, -6.0])),
            Wall(np.array([7.0, -6.0]), np.array([7.0, 0.0])),
            Wall(np.array([3.0, -6.0]), np.array([7.0, -6.0])),   # bottom cap
            # Left corridor walls
            Wall(np.array([0.0, 3.0]), np.array([-6.0, 3.0])),
            Wall(np.array([-6.0, 7.0]), np.array([0.0, 7.0])),
            Wall(np.array([-6.0, 3.0]), np.array([-6.0, 7.0])),   # left cap
        ]
        world = World(walls)

        # Bottom stream: moving upward
        state_bottom = AgentState.create(
            self.n_per_stream,
            spawn_area=(3.5, 6.5, -5.0, -1.0),
            goals=np.array([5.0, 15.0]),
            seed=seed,
        )

        # Left stream: moving rightward
        state_left = AgentState.create(
            self.n_per_stream,
            spawn_area=(-5.0, -1.0, 3.5, 6.5),
            goals=np.array([15.0, 5.0]),
            seed=seed + 2000,
        )

        # Merge
        state = AgentState(
            positions=np.vstack([state_bottom.positions, state_left.positions]),
            velocities=np.vstack([state_bottom.velocities, state_left.velocities]),
            goals=np.vstack([state_bottom.goals, state_left.goals]),
            radii=np.concatenate([state_bottom.radii, state_left.radii]),
            desired_speeds=np.concatenate([state_bottom.desired_speeds, state_left.desired_speeds]),
            masses=np.concatenate([state_bottom.masses, state_left.masses]),
            taus=np.concatenate([state_bottom.taus, state_left.taus]),
            active=np.concatenate([state_bottom.active, state_left.active]),
        )
        return world, state

    def is_complete(self, agent_state: AgentState, time: float) -> bool:
        """Complete when all agents have exited."""
        return agent_state.n_active == 0
