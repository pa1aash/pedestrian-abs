"""R3.1 — C1+epsilon symmetry-breaking control experiment.

Runs C1 (SFM only) at w=0.8m with a small Gaussian velocity perturbation
(sigma=0.05 m/s) added every timestep. This tests whether the mechanism
by which ORCA resolves arching deadlocks is geometric symmetry-breaking
(in which case C1+epsilon should also improve) or velocity-space
optimisation (in which case it should not).

Configuration: BottleneckScenario(n_agents=100, exit_width=0.8), max_time=600s,
seeds 42-66 (paired with existing C1 and C4 runs).

Output: results_new/c1_epsilon/C1eps_w0.8_seed{42..66}.csv
"""

import os
import sys
import time

import numpy as np
import pandas as pd

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sim.core.simulation import Simulation
from sim.scenarios.bottleneck import BottleneckScenario

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "results_new", "c1_epsilon")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEEDS = list(range(42, 67))
EPSILON_SIGMA = 0.05  # m/s velocity perturbation


def run_one(seed: int) -> dict:
    """Run C1 with epsilon perturbation at w=0.8m using velocity_noise_std flag."""
    scenario = BottleneckScenario(n_agents=100, exit_width=0.8)
    sim = Simulation.from_scenario(scenario, "C1", seed=seed)
    sim.velocity_noise_std = EPSILON_SIGMA

    t0 = time.perf_counter()
    result = sim.run(max_steps=100000, max_time=600.0)
    wall_time = time.perf_counter() - t0

    return {
        "scenario": "BottleneckScenario",
        "config": "C1+eps",
        "seed": seed,
        "epsilon_sigma": EPSILON_SIGMA,
        "wall_time_s": wall_time,
        **result,
    }


def main():
    print(f"R3.1 C1+epsilon control: {len(SEEDS)} seeds, sigma={EPSILON_SIGMA} m/s",
          flush=True)

    rows = []
    for i, seed in enumerate(SEEDS):
        tag = f"C1eps_w0.8_seed{seed}"
        csv_path = os.path.join(OUTPUT_DIR, f"{tag}.csv")

        # Skip if already done
        if os.path.exists(csv_path):
            print(f"  [{i+1}/{len(SEEDS)}] seed={seed} SKIP (exists)", flush=True)
            existing = pd.read_csv(csv_path)
            rows.append(existing.iloc[0].to_dict())
            continue

        result = run_one(seed)
        rows.append(result)

        # Write individual CSV
        pd.DataFrame([result]).to_csv(csv_path, index=False)

        evac = result["evacuation_time"]
        evac_str = f"{evac:.1f}s" if evac != float("inf") else "inf"
        print(f"  [{i+1}/{len(SEEDS)}] seed={seed} evac={evac_str} "
              f"coll={result['collision_count']} wall={result['wall_time_s']:.0f}s",
              flush=True)

    # Combined output
    combined = pd.DataFrame(rows)
    combined.to_csv(os.path.join(OUTPUT_DIR, "c1_epsilon_combined.csv"), index=False)

    n_complete = int((combined["evacuation_time"] != np.inf).sum())
    print(f"\nDone. {n_complete}/{len(SEEDS)} evacuations completed.", flush=True)
    print(f"Completion rate: {n_complete/len(SEEDS)*100:.0f}%", flush=True)


if __name__ == "__main__":
    main()
