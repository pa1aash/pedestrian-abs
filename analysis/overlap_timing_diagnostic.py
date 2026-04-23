"""Diagnose whether bottleneck contact-overlaps are spawn artefacts.

Runs 2 seeds x {w=1.0, w=3.6} x {C1, C4} with log_collisions=True, then reports
the fraction of overlap-step events occurring in t < 2 s (spawn window) vs later.

Output:
  results_analysis/overlap_timing_diagnostic.csv
  stdout summary
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from sim.core.integrator import EulerIntegrator
from sim.core.simulation import Simulation
from sim.experiments.configs import get_config, get_param_overrides
from sim.scenarios.bottleneck import BottleneckScenario
from sim.steering.hybrid import HybridSteeringModel


def build_sim(width: float, config_name: str, seed: int) -> Simulation:
    scenario = BottleneckScenario(n_agents=50, exit_width=width)
    world, agent_state = scenario.build(seed=seed)
    with open("config/params.yaml") as f:
        params = yaml.safe_load(f)
    flat: dict = {}
    for v in params.values():
        if isinstance(v, dict):
            flat.update(v)
    flat.update(get_param_overrides(config_name))
    config = get_config(config_name)
    steering = HybridSteeringModel(config, flat)
    sim = Simulation(
        world, agent_state, steering, EulerIntegrator(), flat,
        log_collisions=True, seed=seed,
    )
    sim._scenario = scenario
    return sim


def main() -> None:
    rows = []
    cells = [
        (w, c, s)
        for w in (1.0, 3.6)
        for c in ("C1", "C4")
        for s in (42, 43)
    ]
    for width, config, seed in cells:
        sim = build_sim(width, config, seed)
        t0 = time.perf_counter()
        result = sim.run(max_steps=20000, max_time=120.0)
        wall = time.perf_counter() - t0

        coll = pd.DataFrame(
            sim._collision_log,
            columns=["t", "i", "j", "xi", "yi", "xj", "yj"],
        )
        total = len(coll)
        in_spawn = int((coll["t"] < 2.0).sum()) if total else 0
        in_first_05 = int((coll["t"] < 0.5).sum()) if total else 0
        med_t = float(coll["t"].median()) if total else float("nan")

        rows.append({
            "width": width,
            "config": config,
            "seed": seed,
            "wall_s": wall,
            "evac_s": result.get("evacuation_time"),
            "n_overlap_steps": total,
            "n_t_lt_0.5": in_first_05,
            "n_t_lt_2.0": in_spawn,
            "frac_t_lt_0.5": in_first_05 / total if total else float("nan"),
            "frac_t_lt_2.0": in_spawn / total if total else float("nan"),
            "median_t": med_t,
        })
        print(
            f"  w={width} {config} seed={seed}: total={total}, "
            f"<0.5s={in_first_05} ({100 * (in_first_05/total if total else 0):.0f}%), "
            f"<2s={in_spawn} ({100 * (in_spawn/total if total else 0):.0f}%), "
            f"median_t={med_t:.2f}s, wall={wall:.1f}s"
        )

    df = pd.DataFrame(rows)
    out = Path("results_analysis/overlap_timing_diagnostic.csv")
    df.to_csv(out, index=False)
    print(f"\nWrote {out}")

    print("\n=== Summary by (width, config) ===")
    g = df.groupby(["width", "config"])[["frac_t_lt_0.5", "frac_t_lt_2.0"]].mean()
    print(g.to_string())


if __name__ == "__main__":
    main()
