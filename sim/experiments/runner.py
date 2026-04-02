"""Experiment runner: batch execution of scenario x config x seeds -> CSV."""

import os
import time

import numpy as np
import pandas as pd

from sim.core.simulation import Simulation


class ExperimentRunner:
    """Batch experiment runner producing CSV results.

    Args:
        output_dir: Directory for CSV output files.
    """

    def __init__(self, output_dir: str = "results/"):
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir

    def run(
        self,
        scenario_class,
        config_name: str,
        n_replications: int = 30,
        max_time: float = 120.0,
        max_steps: int = 100000,
        **scenario_kwargs,
    ) -> pd.DataFrame:
        """Run scenario x config x seeds and save to CSV.

        Args:
            scenario_class: Scenario class to instantiate.
            config_name: Configuration name (C1-C4).
            n_replications: Number of random seeds.
            max_time: Maximum simulation time per run (s).
            max_steps: Maximum steps per run.
            **scenario_kwargs: Passed to scenario constructor.

        Returns:
            DataFrame with one row per replication.
        """
        rows = []
        for rep in range(n_replications):
            seed = 42 + rep
            scenario = scenario_class(**scenario_kwargs)
            sim = Simulation.from_scenario(scenario, config_name, seed=seed)

            t0 = time.perf_counter()
            result = sim.run(max_steps=max_steps, max_time=max_time)
            wall_time = time.perf_counter() - t0

            row = {
                "scenario": scenario_class.__name__,
                "config": config_name,
                "seed": seed,
                "wall_time_s": wall_time,
                **result,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        fname = f"{scenario_class.__name__}_{config_name}.csv"
        df.to_csv(os.path.join(self.output_dir, fname), index=False)
        return df

    def run_scaling(
        self,
        config_name: str = "C4",
        agent_counts: list[int] | None = None,
        n_steps: int = 50,
    ) -> pd.DataFrame:
        """Measure ms/step at various agent counts.

        Args:
            config_name: Configuration to test.
            agent_counts: List of agent counts.
            n_steps: Steps per measurement.

        Returns:
            DataFrame with n_agents and ms_per_step columns.
        """
        if agent_counts is None:
            agent_counts = [50, 100, 200, 500, 1000]

        from sim.scenarios.corridor import CorridorScenario

        rows = []
        for n in agent_counts:
            scenario = CorridorScenario(n_agents=n)
            sim = Simulation.from_scenario(scenario, config_name)

            t0 = time.perf_counter()
            sim.run(max_steps=n_steps, max_time=1000.0)
            elapsed_ms = (time.perf_counter() - t0) / n_steps * 1000

            rows.append({"n_agents": n, "ms_per_step": elapsed_ms, "config": config_name})

        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(self.output_dir, f"scaling_{config_name}.csv"), index=False)
        return df
