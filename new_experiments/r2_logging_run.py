"""R2.0 — Consolidated logging run.

Runs 100 simulations with trajectory + collision logging enabled:
  C1, C4 x w in {0.8, 1.0} x seeds 42-66 (25 seeds each)

Configuration matches the existing frozen results:
  w=0.8: BottleneckScenario(n_agents=100, exit_width=0.8), max_time=600.0
  w=1.0: BottleneckScenario(n_agents=50, exit_width=1.0), max_time=120.0

Output directories (never writes to results/):
  results_new/trajectories/<scenario>_<config>_w<width>_seed<seed>.parquet
  results_new/collisions/<scenario>_<config>_w<width>_seed<seed>.parquet

Interrupt-safe: skips any run whose output parquet already exists.
"""

import os
import sys
import time

# Ensure project root is on sys.path so 'sim' is importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sim.core.simulation import Simulation
from sim.scenarios.bottleneck import BottleneckScenario

CELLS = [
    {"config": "C1", "width": 0.8, "n_agents": 100, "max_time": 600.0},
    {"config": "C4", "width": 0.8, "n_agents": 100, "max_time": 600.0},
    {"config": "C1", "width": 1.0, "n_agents": 50, "max_time": 120.0},
    {"config": "C4", "width": 1.0, "n_agents": 50, "max_time": 120.0},
]
SEEDS = list(range(42, 67))  # 42-66 inclusive = 25 seeds

TRAJ_DIR = "results_new/trajectories"
COLL_DIR = "results_new/collisions"


def run_one(config: str, width: float, n_agents: int, max_time: float, seed: int):
    """Run a single simulation with logging and write parquet outputs."""
    tag = f"Bottleneck_{config}_w{width}_seed{seed}"
    traj_path = os.path.join(TRAJ_DIR, f"{tag}.parquet")
    coll_path = os.path.join(COLL_DIR, f"{tag}.parquet")

    # Skip if both outputs exist
    if os.path.exists(traj_path) and os.path.exists(coll_path):
        return "skip"

    scenario = BottleneckScenario(n_agents=n_agents, exit_width=width)
    sim = Simulation.from_scenario(scenario, config, seed=seed)
    sim.log_positions = True
    sim.log_collisions = True

    t0 = time.perf_counter()
    result = sim.run(max_steps=100000, max_time=max_time)
    wall = time.perf_counter() - t0

    sim.write_logs(trajectory_path=traj_path, collision_path=coll_path)

    evac = result["evacuation_time"]
    evac_str = f"{evac:.1f}s" if evac != float("inf") else "inf"
    return f"evac={evac_str} coll={result['collision_count']} wall={wall:.0f}s"


def main():
    os.makedirs(TRAJ_DIR, exist_ok=True)
    os.makedirs(COLL_DIR, exist_ok=True)

    total = len(CELLS) * len(SEEDS)
    done = 0
    skipped = 0
    t_start = time.time()

    print(f"R2.0 logging run: {total} simulations", flush=True)
    print(f"Output: {TRAJ_DIR}/ and {COLL_DIR}/", flush=True)
    print(flush=True)

    for cell in CELLS:
        cfg = cell["config"]
        w = cell["width"]
        print(f"[{time.strftime('%H:%M')}] {cfg} w={w} ({cell['n_agents']} agents, "
              f"max_time={cell['max_time']}s)", flush=True)

        for seed in SEEDS:
            done += 1
            status = run_one(cfg, w, cell["n_agents"], cell["max_time"], seed)
            if status == "skip":
                skipped += 1
                continue
            print(f"  [{done}/{total}] seed={seed} {status}", flush=True)

    elapsed_hr = (time.time() - t_start) / 3600
    print(f"\nComplete: {total} runs ({skipped} skipped), {elapsed_hr:.2f} hrs",
          flush=True)


if __name__ == "__main__":
    main()
