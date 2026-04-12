"""R3.2 — Force-magnitude diagnostic via built-in log_forces flag.

Runs C4 at w=1.0m with log_forces=True (every 10th step).
Records (t, agent_id, density, |F_des|, |F_SFM|, |F_TTC|, |F_ORCA|).

Configuration: BottleneckScenario(n_agents=50, exit_width=1.0), max_time=120s,
n=5 seeds (42-46).

Output: results_new/force_logging/force_C4_w1.0_seed{42..46}.parquet
"""

import os
import sys
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sim.core.simulation import Simulation
from sim.scenarios.bottleneck import BottleneckScenario

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "results_new", "force_logging")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEEDS = list(range(42, 47))  # n=5


def main():
    print(f"R3.2 Force-magnitude logging: {len(SEEDS)} seeds", flush=True)

    for i, seed in enumerate(SEEDS):
        tag = f"force_C4_w1.0_seed{seed}"
        path = os.path.join(OUTPUT_DIR, f"{tag}.parquet")

        if os.path.exists(path):
            print(f"  [{i+1}/{len(SEEDS)}] seed={seed} SKIP (exists)", flush=True)
            continue

        scenario = BottleneckScenario(n_agents=50, exit_width=1.0)
        sim = Simulation.from_scenario(scenario, "C4", seed=seed)
        sim.log_forces = True

        t0 = time.perf_counter()
        sim.run(max_steps=100000, max_time=120.0)
        wall = time.perf_counter() - t0

        sim.write_logs(force_path=path)
        n_rows = len(sim._force_log)
        print(f"  [{i+1}/{len(SEEDS)}] seed={seed} {n_rows} rows, {wall:.0f}s", flush=True)

    print("Done.", flush=True)


if __name__ == "__main__":
    main()
