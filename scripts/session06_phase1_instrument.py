#!/usr/bin/env python
"""Phase 1: measure per-step wall-clock at three representative bin sizes."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
from sim.core.simulation import Simulation
from sim.scenarios.fzj_bottleneck import FZJCorridorScenario


def time_n(n_agents: int, warmup: int = 50, measure: int = 100) -> float:
    scenario = FZJCorridorScenario(
        n_agents=n_agents, corridor_length=18.0, corridor_width=5.0,
        warmup_steps=warmup, measure_steps=measure,
    )
    sim = Simulation.from_scenario(scenario, "C1", seed=42)
    for _ in range(warmup):
        sim.step()
    t0 = time.time()
    for _ in range(measure):
        sim.step()
    return (time.time() - t0) / measure


if __name__ == "__main__":
    # Empirical FD bins per load_empirical_fd: 0.5..5.5 step 0.5, area=90
    bins = [0.5, 2.5, 5.0]
    n_at = [max(3, int(r * 90.0)) for r in bins]
    print(f"Bin densities: {bins}")
    print(f"Agent counts:  {n_at}")
    per_step = {}
    for n in n_at:
        ms = time_n(n) * 1000.0
        per_step[n] = ms
        print(f"N={n:4d}: {ms:.2f} ms/step")

    # Empirical FD: 12 bins from 0.5..5.5
    fd_bins = np.arange(0.5, 5.51, 0.5)
    fd_n = [max(3, int(r * 90.0)) for r in fd_bins]
    # interpolate per-step ms over fd bins from measurements at n_at
    xs = np.array(sorted(per_step.keys()))
    ys = np.array([per_step[x] for x in xs])
    fd_ms = np.interp(fd_n, xs, ys)

    seeds = 3
    steps_per_seed = 800  # 300 warmup + 500 measure
    per_eval_s = sum(fd_ms) * seeds * steps_per_seed / 1000.0
    print(f"\nFD bins: {len(fd_bins)} ({fd_bins.tolist()})")
    print(f"Per-eval wall-clock (3 seeds, 800 steps/seed): {per_eval_s:.1f} s "
          f"= {per_eval_s/60:.2f} min")

    nm_evals_per_restart = 60
    profile_evals = 30
    opt_b = (11 * nm_evals_per_restart + profile_evals) * per_eval_s / 3600.0
    opt_c = (5 * nm_evals_per_restart + profile_evals) * per_eval_s / 3600.0
    print(f"Option B (11 restarts × 60 + 30 profile): {opt_b:.2f} wall-hours")
    print(f"Option C (5 restarts × 60 + 30 profile):  {opt_c:.2f} wall-hours")

    if opt_b <= 12:
        sel = "B"
    elif opt_b <= 24:
        sel = "C"
    else:
        sel = "C-capped"
    print(f"Decision rule: B≤12→B, 12<B≤24→C, B>24→C-capped")
    print(f"SELECTED: {sel}")
