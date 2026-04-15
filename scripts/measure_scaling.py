"""Scaling benchmark — Session 0.5 (resolves U3 + U4).

Measures mean ms/step at various agent counts for C1 and C4.
- C1: {50, 100, 200, 500, 1000}
- C4: {50, 100, 200, 500}  (capped at 500 per CLAUDE.md §0)

3 seeds per cell for variance bars.
Uses BottleneckScenario with exit_width=3.6 m (wide exit so agents exit
quickly and do not stall; we only care about step timing).

Timing window: first 50 steps (after setup). Reported as mean ± std over
n_seeds replications, where each replication's ms/step is the mean over
50 steps.

Output: results_new/scaling_C1.csv  and  results_new/scaling_C4.csv
NEVER writes to results/ or results_backup/.
"""

import os
import sys
import time
import csv

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
os.chdir(_PROJECT_ROOT)

from sim.core.simulation import Simulation
from sim.scenarios.bottleneck import BottleneckScenario

N_STEPS = 50          # steps per timing window
N_SEEDS = 3           # replications per cell
SEEDS = [42, 43, 44]  # fixed seeds for reproducibility

C1_COUNTS = [50, 100, 200, 500, 1000]
C4_COUNTS = [50, 100, 200, 500]   # cap at 500 per CLAUDE.md §0

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "results_new")
FIELDNAMES = ["config", "n_agents", "seed", "ms_per_step"]


def measure_one(config: str, n_agents: int, seed: int) -> float:
    """Return mean ms/step over N_STEPS steps for given config/n_agents/seed.

    Args:
        config: Steering config name.
        n_agents: Number of agents.
        seed: Random seed.

    Returns:
        Mean milliseconds per step.
    """
    scenario = BottleneckScenario(n_agents=n_agents, exit_width=3.6)
    sim = Simulation.from_scenario(scenario, config, seed=seed)

    step_times = []
    for _ in range(N_STEPS):
        if sim.state.n_active == 0:
            break
        t0 = time.perf_counter()
        sim.step()
        step_times.append((time.perf_counter() - t0) * 1000.0)

    return float(sum(step_times) / len(step_times)) if step_times else 0.0


def run_config(config: str, counts: list[int], out_path: str) -> None:
    """Benchmark a config across agent counts and write CSV.

    Args:
        config: Steering config name.
        counts: List of agent counts to benchmark.
        out_path: Output CSV path.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rows = []
    t_total_start = time.time()

    print(f"\n=== {config} scaling benchmark ===", flush=True)
    for n in counts:
        for seed in SEEDS:
            ms = measure_one(config, n, seed)
            row = {"config": config, "n_agents": n, "seed": seed, "ms_per_step": round(ms, 3)}
            rows.append(row)
            print(f"  {config} n={n} seed={seed}: {ms:.2f} ms/step", flush=True)

    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - t_total_start
    print(f"  Written {out_path} ({len(rows)} rows, {elapsed:.1f}s)", flush=True)


def main() -> None:
    t_start = time.time()
    print(f"Scaling benchmark start: {time.strftime('%H:%M:%S')}", flush=True)
    print(f"C1 counts: {C1_COUNTS}", flush=True)
    print(f"C4 counts: {C4_COUNTS} (capped at 500 per CLAUDE.md §0)", flush=True)

    run_config("C1", C1_COUNTS,
               os.path.join(OUTPUT_DIR, "scaling_C1.csv"))
    run_config("C4", C4_COUNTS,
               os.path.join(OUTPUT_DIR, "scaling_C4.csv"))

    total_min = (time.time() - t_start) / 60
    print(f"\nTotal elapsed: {total_min:.1f} min", flush=True)


if __name__ == "__main__":
    main()
