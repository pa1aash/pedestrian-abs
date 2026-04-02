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

    def run_fundamental_diagram(
        self,
        config_name: str,
        injection_rates: list[float] | None = None,
        n_replications: int = 5,
    ) -> pd.DataFrame:
        """Run continuous-injection corridor FD experiments.

        Args:
            config_name: Steering config (C1-C4).
            injection_rates: Agents/sec injection rates to test.
            n_replications: Reps per rate.

        Returns:
            DataFrame with config, injection_rate, rep, density, speed columns.
        """
        if injection_rates is None:
            injection_rates = [1, 2, 3, 5, 7, 10, 13, 16, 20]

        from sim.scenarios.corridor import CorridorFDScenario

        rows = []
        for rate in injection_rates:
            for rep in range(n_replications):
                seed = 42 + rep
                scenario = CorridorFDScenario(
                    injection_rate=rate, warmup_time=10.0, measure_time=15.0,
                )
                sim = Simulation.from_scenario(scenario, config_name, seed=seed)

                dt = sim.params.get("dt", 0.01)
                total_time = scenario.warmup_time + scenario.measure_time

                # Run with measurement
                fd_points = []
                while sim.time < total_time and sim.step_count < 100000:
                    sim.step()

                    # Deactivate past exit
                    past = np.where(
                        sim.state.active & (sim.state.positions[:, 0] > 24.5)
                    )[0]
                    sim.state.deactivate(past)

                    # Inject
                    inj_accum = getattr(sim, '_fd_inj_accum', 0.0)
                    inj_accum += rate * dt
                    if inj_accum >= 1.0:
                        n_inj = int(inj_accum)
                        inj_accum -= n_inj
                        sim.inject_agents(n_inj, seed=seed * 1000 + sim.step_count)
                    sim._fd_inj_accum = inj_accum

                    # Measure at x∈[20,24] (right at bottleneck queue)
                    if sim.time >= scenario.warmup_time:
                        active = sim.state.active_indices
                        pos = sim.state.positions[active]
                        vel = sim.state.velocities[active]
                        in_area = (pos[:, 0] >= 20.0) & (pos[:, 0] <= 24.0)
                        if np.sum(in_area) >= 2:
                            area_size = 4.0 * 3.6  # 4m x 3.6m
                            density = float(np.sum(in_area)) / area_size
                            speed = float(np.mean(np.linalg.norm(vel[in_area], axis=1)))
                            fd_points.append((density, speed))

                # Record per-frame measurements, subsample for manageable size
                step = max(1, len(fd_points) // 50)  # ~50 points per rep
                for idx in range(0, len(fd_points), step):
                    d, s = fd_points[idx]
                    rows.append({
                        "config": config_name,
                        "injection_rate": rate,
                        "rep": rep,
                        "density": d,
                        "speed": s,
                    })
                print(f"  FD {config_name} rate={rate} rep={rep}: "
                      f"rho={rows[-1]['density']:.2f} v={rows[-1]['speed']:.2f}" if rows else "  (no data)")

        df = pd.DataFrame(rows)
        fname = f"fd_{config_name}.csv"
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
