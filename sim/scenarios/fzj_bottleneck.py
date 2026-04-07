"""FZJ-matched scenario for Digital Twin Level 2 calibration.

Replicates the FZJ Pedestrian Dynamics Data Archive unidirectional
corridor experiment geometry (Seyfried et al., 2005):
- Oval track approximated as periodic corridor (wrap-around x)
- Corridor width: 5.0m (matching FZJ y-range 0-5m)
- Measurement length: 10.0m (matching FZJ straight section)
- Agent counts matched to FZJ experimental runs (142-952 peds)

This scenario enables calibration of model parameters against
empirical FZJ fundamental diagram data, establishing the
physical-virtual pairing required for Digital Twin Level 2.
"""

import numpy as np

from sim.core.agent import AgentState
from sim.core.world import Wall, World
from sim.scenarios.base import Scenario


# FZJ experiment agent counts from uni_corr_500_01 through _09
FZJ_AGENT_COUNTS: list[int] = [142, 760, 916, 909, 933, 952, 936, 918, 440]


class FZJCorridorScenario(Scenario):
    """Periodic corridor matching FZJ unidirectional experiment geometry.

    The FZJ experiments use an oval track with a straight measurement
    section. We approximate this as a periodic (wrap-around) corridor
    with dimensions matching the FZJ setup.

    Args:
        n_agents: Number of agents (use FZJ_AGENT_COUNTS for exact match).
        corridor_length: Length of periodic corridor (m).
        corridor_width: Width matching FZJ corridor (m).
        warmup_steps: Steps before measurement starts.
        measure_steps: Steps of data collection.
    """

    def __init__(
        self,
        n_agents: int = 50,
        corridor_length: float = 18.0,
        corridor_width: float = 5.0,
        warmup_steps: int = 500,
        measure_steps: int = 1000,
    ):
        self.n_agents = n_agents
        self.length = corridor_length
        self.width = corridor_width
        self.warmup_steps = warmup_steps
        self.measure_steps = measure_steps
        self.periodic_length = corridor_length

    def build(self, seed: int = 42) -> tuple[World, AgentState]:
        """Build FZJ-matched periodic corridor.

        Top/bottom walls only (x is periodic, wraps around).
        """
        walls = [
            Wall(np.array([0.0, 0.0]), np.array([self.length, 0.0])),
            Wall(np.array([0.0, self.width]), np.array([self.length, self.width])),
        ]
        world = World(walls)

        state = AgentState.create(
            self.n_agents,
            spawn_area=(0.5, self.length - 0.5, 0.3, self.width - 0.3),
            goals=np.array([self.length + 10.0, self.width / 2]),
            seed=seed,
            heterogeneous=True,
        )
        return world, state

    def is_complete(self, agent_state: AgentState, time: float) -> bool:
        """Never completes on its own (run with step counts)."""
        return False
