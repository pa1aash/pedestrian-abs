"""Corridor scenario: 10x3.6m unidirectional flow."""

import numpy as np

from sim.core.agent import AgentState
from sim.core.world import Wall, World
from sim.scenarios.base import Scenario


class CorridorScenario(Scenario):
    """10x3.6m corridor with agents walking left to right.

    Args:
        n_agents: Number of agents.
        heterogeneous: Whether to use heterogeneous agent parameters.
    """

    def __init__(self, n_agents: int = 50, heterogeneous: bool = True):
        self.n_agents = n_agents
        self.heterogeneous = heterogeneous

    def build(self, seed: int = 42) -> tuple[World, AgentState]:
        """Build corridor world and agents.

        Walls: 10x3.6 rectangle.
        Spawn: x in [0.5, 2], y in [0.3, 3.3].
        Goal: (10.5, y_i) — each agent's own y-coordinate.
        """
        walls = [
            Wall(np.array([0.0, 0.0]), np.array([10.0, 0.0])),
            Wall(np.array([10.0, 0.0]), np.array([10.0, 3.6])),
            Wall(np.array([10.0, 3.6]), np.array([0.0, 3.6])),
            Wall(np.array([0.0, 3.6]), np.array([0.0, 0.0])),
        ]
        world = World(walls)

        state = AgentState.create(
            self.n_agents,
            spawn_area=(0.5, 2.0, 0.3, 3.3),
            goals=np.array([10.5, 1.8]),  # placeholder, overwritten below
            seed=seed,
            heterogeneous=self.heterogeneous,
        )
        # Set per-agent goals to maintain their y-coordinate
        state.goals[:, 0] = 10.5
        state.goals[:, 1] = state.positions[:, 1]

        return world, state

    def is_complete(self, agent_state: AgentState, time: float) -> bool:
        """Complete when all agents have exited."""
        return agent_state.n_active == 0
