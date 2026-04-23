"""Regenerate the zonal-decomposition artefacts on rejection-sampled data.

Runs C1 and C4 at w in {0.8, 1.0} m with rejection-sampled initial placement
and log_collisions=True, writing per-run collision parquets to
``results_new/collisions_rerun/``. Then runs the zonal decomposition (zone
tagging, summary stats, stacked-bar figure, LaTeX table) using the existing
helpers in ``analysis/zonal_decomposition.py``.

Outputs (all overwritten):
  results_new/collisions_rerun/Bottleneck_C{1,4}_w{0.8,1.0}_seed{42..66}.parquet
  results_analysis/zonal_collisions.csv
  results_analysis/zonal_collisions_summary.csv
  results_analysis/zonal_collisions_table.tex
  figures/zonal_collisions_w1m.pdf

Usage::

    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \\
        python scripts/regen_zonal.py --workers 10

Expected time: ~10 min on a 12-core i7 with 10 workers.
"""
from __future__ import annotations

import os

for _var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")

import argparse
import multiprocessing as mp
import sys
import time
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

WIDTHS = [0.8, 1.0]
CONFIGS = ["C1", "C4"]
SEEDS = list(range(42, 67))
N_AGENTS = 50
MAX_TIME = 300.0
MAX_STEPS = 100_000
SPAWN_AREA = (1.0, 8.0, 1.0, 9.0)

COLL_OUT_DIR = REPO / "results_new" / "collisions_rerun"


def sample_no_overlap(n, radii, spawn_area, rng, max_tries=20_000):
    import numpy as np
    x0, x1, y0, y1 = spawn_area
    positions = np.zeros((n, 2))
    lo = np.array([x0, y0])
    hi = np.array([x1, y1])
    for i in range(n):
        placed = False
        for _ in range(max_tries):
            cand = rng.uniform(lo, hi)
            if i == 0:
                positions[i] = cand
                placed = True
                break
            diffs = positions[:i] - cand
            d = np.sqrt((diffs ** 2).sum(axis=1))
            min_gap = radii[:i] + radii[i]
            if (d >= min_gap).all():
                positions[i] = cand
                placed = True
                break
        if not placed:
            raise RuntimeError(
                f"Rejection sampling failed at agent {i}/{n} after {max_tries} tries"
            )
    return positions


def run_one(cell):
    import time as _time

    import numpy as np
    import yaml

    from sim.core.integrator import EulerIntegrator
    from sim.core.simulation import Simulation
    from sim.experiments.configs import get_config, get_param_overrides
    from sim.scenarios.bottleneck import BottleneckScenario
    from sim.steering.hybrid import HybridSteeringModel

    width, config_name, seed = cell

    scenario = BottleneckScenario(n_agents=N_AGENTS, exit_width=width)
    world, agent_state = scenario.build(seed=seed)

    rng = np.random.Generator(np.random.PCG64(seed))
    agent_state.positions = sample_no_overlap(
        N_AGENTS, agent_state.radii, SPAWN_AREA, rng
    )

    with open(REPO / "config" / "params.yaml") as f:
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

    t0 = _time.perf_counter()
    _ = sim.run(max_steps=MAX_STEPS, max_time=MAX_TIME)
    wall = _time.perf_counter() - t0

    # Persist collision log in the naming convention analysis/zonal_decomposition.py expects
    out_path = (
        COLL_OUT_DIR / f"Bottleneck_{config_name}_w{width}_seed{seed}.parquet"
    )
    sim.write_logs(collision_path=str(out_path))

    return {
        "width": width,
        "config": config_name,
        "seed": seed,
        "wall_time_s": wall,
        "n_collisions": len(sim._collision_log),
    }


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=10)
    return p.parse_args()


def run_sims(workers: int) -> None:
    cells = list(product(WIDTHS, CONFIGS, SEEDS))
    COLL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Running {len(cells)} cells (C1,C4 x w in {WIDTHS} x {len(SEEDS)} seeds) "
          f"with log_collisions=True, {workers} workers")
    print(f"Output dir: {COLL_OUT_DIR}")

    t0 = time.perf_counter()
    completed = 0
    with mp.Pool(workers) as pool:
        for row in pool.imap_unordered(run_one, cells, chunksize=1):
            completed += 1
            if completed % 5 == 0 or completed == len(cells):
                elapsed = time.perf_counter() - t0
                rate = completed / max(elapsed, 1e-6)
                eta = (len(cells) - completed) / rate if rate > 0 else 0
                print(
                    f"  [{completed:>3}/{len(cells)}]  "
                    f"{elapsed/60:5.1f} min elapsed,  "
                    f"{eta/60:5.1f} min remaining"
                )
    total_min = (time.perf_counter() - t0) / 60
    print(f"Sims done in {total_min:.1f} min.")


def run_zonal_analysis() -> None:
    """Re-run analysis/zonal_decomposition.main() pointed at the rerun dir."""
    import analysis.zonal_decomposition as zd

    zd.COLL_DIR = COLL_OUT_DIR
    print("\nZonal decomposition using COLL_DIR =", zd.COLL_DIR)
    zd.main()


def main():
    args = parse_args()
    run_sims(args.workers)
    run_zonal_analysis()


if __name__ == "__main__":
    mp.freeze_support()
    main()
