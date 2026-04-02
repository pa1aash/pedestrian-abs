"""Funnel scenario: 10m-wide entrance tapering to 3m exit over 15m."""

import numpy as np

from sim.core.agent import AgentState
from sim.core.world import Wall, World
from sim.scenarios.base import Scenario


class FunnelScenario(Scenario):
    """Funnel with angled walls tapering from 10m to 3m.

    Top wall: (0,10) -> (15, 6.5).
    Bottom wall: (0,0) -> (15, 3.5).
    Left wall: (0,0) -> (0, 10).

    Args:
        n_agents: Number of agents.
    """

    def __init__(self, n_agents: int = 400):
        self.n_agents = n_agents

    def build(self, seed: int = 42) -> tuple[World, AgentState]:
        """Build funnel world and agents.

        Spawn: x in [0.5, 5], y in [1, 9].
        Goal: (16, 5).
        """
        walls = [
            Wall(np.array([0.0, 0.0]), np.array([15.0, 3.5])),    # bottom (angled)
            Wall(np.array([0.0, 10.0]), np.array([15.0, 6.5])),   # top (angled)
            Wall(np.array([0.0, 0.0]), np.array([0.0, 10.0])),    # left
            # Exit walls (short vertical segments at x=15)
            Wall(np.array([15.0, 3.5]), np.array([15.0, 3.5])),   # degenerate (bottom endpoint)
            Wall(np.array([15.0, 6.5]), np.array([15.0, 6.5])),   # degenerate (top endpoint)
        ]
        world = World(walls)

        state = AgentState.create(
            self.n_agents,
            spawn_area=(0.5, 5.0, 1.0, 9.0),
            goals=np.array([16.0, 5.0]),
            seed=seed,
        )
        return world, state

    def is_complete(self, agent_state: AgentState, time: float) -> bool:
        """Complete when all agents have exited."""
        return agent_state.n_active == 0
