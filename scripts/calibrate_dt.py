#!/usr/bin/env python
"""Digital Twin Level 2: calibrate model parameters against FZJ empirical data.

Fits Weidmann (gamma, rho_max) and SFM (A, B) parameters to minimize
the speed-density RMSE between simulation and empirical fundamental
diagram data from the FZJ Pedestrian Dynamics Data Archive.

This establishes the physical-virtual pairing required for DT Level 2:
the FZJ corridor is the physical counterpart, and the calibrated model
is the virtual replica tuned to match its measurements.

Usage:
    python scripts/calibrate_dt.py [--config C1] [--max-evals 40]
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from sim.core.simulation import Simulation
from sim.scenarios.fzj_bottleneck import FZJCorridorScenario


def load_empirical_fd(path: str = "results/empirical_fd.csv") -> tuple[np.ndarray, np.ndarray]:
    """Load and bin empirical FD data into density-speed pairs.

    Bins data into 0.5 ped/m^2 bins from 0.5 to 5.5, taking median
    speed per bin. Filters density range to 0.3-6.0 ped/m^2.

    Args:
        path: Path to empirical_fd.csv.

    Returns:
        Tuple of (density_bins, speed_bins) arrays.
    """
    df = pd.read_csv(path)
    df = df[(df["mean_density"] > 0.3) & (df["mean_density"] <= 6.0)]

    bin_edges = np.arange(0.25, 5.75, 0.5)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    df["bin"] = pd.cut(
        df["mean_density"], bins=bin_edges,
        labels=bin_centers[:len(bin_edges) - 1],
    )
    binned = df.groupby("bin", observed=True)["mean_speed"].median()

    densities = np.array(binned.index.astype(float))
    speeds = np.array(binned.values)
    mask = ~np.isnan(speeds)
    return densities[mask], speeds[mask]


def simulate_fd_point(
    params_dict: dict,
    config_name: str,
    rho_target: float,
    n_reps: int = 3,
) -> float:
    """Simulate one density point and return mean speed.

    Args:
        params_dict: Parameter overrides.
        config_name: Steering config.
        rho_target: Target density (ped/m^2).
        n_reps: Number of replications.

    Returns:
        Mean speed across replications (m/s).
    """
    corridor_length = 18.0
    corridor_width = 5.0
    area = corridor_length * corridor_width
    n_agents = max(3, int(rho_target * area))

    rep_speeds = []
    for rep in range(n_reps):
        scenario = FZJCorridorScenario(
            n_agents=n_agents,
            corridor_length=corridor_length,
            corridor_width=corridor_width,
            warmup_steps=300,
            measure_steps=500,
        )
        sim = Simulation.from_scenario(
            scenario, config_name, seed=42 + rep,
            param_overrides=params_dict,
        )

        for _ in range(scenario.warmup_steps):
            sim.step()

        step_speeds = []
        for _ in range(scenario.measure_steps):
            sim.step()
            active = sim.state.active_indices
            if len(active) > 0:
                v = np.linalg.norm(sim.state.velocities[active], axis=1)
                step_speeds.append(float(np.mean(v)))

        if step_speeds:
            rep_speeds.append(np.mean(step_speeds))

    return float(np.mean(rep_speeds)) if rep_speeds else 0.0


def calibration_objective(
    x: np.ndarray,
    emp_rho: np.ndarray,
    emp_speed: np.ndarray,
    config_name: str,
    n_reps: int,
    history: list,
) -> float:
    """RMSE between simulated and empirical FD.

    Args:
        x: [weidmann_gamma, weidmann_rho_max, A, B].
        emp_rho: Empirical density bins.
        emp_speed: Empirical median speeds.
        config_name: Steering config.
        n_reps: Reps per point.
        history: Evaluation history list.

    Returns:
        RMSE in m/s.
    """
    gamma, rho_max, A, B = x

    # Soft bounds
    if not (0.1 < gamma < 10.0 and 3.0 < rho_max < 10.0
            and 500 < A < 10000 and 0.01 < B < 0.5):
        return 5.0

    params_dict = {
        "weidmann_gamma": float(gamma),
        "weidmann_rho_max": float(rho_max),
        "A": float(A),
        "B": float(B),
    }

    sim_speeds = np.array([
        simulate_fd_point(params_dict, config_name, rho, n_reps)
        for rho in emp_rho
    ])

    rmse = float(np.sqrt(np.mean((sim_speeds - emp_speed) ** 2)))

    history.append({
        "params": params_dict,
        "rmse": rmse,
        "sim_speeds": sim_speeds.tolist(),
    })
    print(f"  Eval {len(history):3d}: gamma={gamma:.3f} rho_max={rho_max:.2f} "
          f"A={A:.0f} B={B:.3f} -> RMSE={rmse:.4f} m/s")

    return rmse


def run_calibration(
    config_name: str = "C1",
    max_evals: int = 40,
    n_reps: int = 3,
    output_path: str = "results/calibration.json",
) -> dict:
    """Run calibration: Nelder-Mead on Weidmann + SFM params.

    Args:
        config_name: Steering config to calibrate.
        max_evals: Maximum function evaluations.
        n_reps: Replications per density point per evaluation.
        output_path: Output JSON path.

    Returns:
        Dict with baseline/calibrated RMSE, params, history.
    """
    print("Loading empirical FD data...")
    emp_rho, emp_speed = load_empirical_fd()
    print(f"  {len(emp_rho)} bins: rho={emp_rho.tolist()}")
    print(f"  speeds={[f'{s:.3f}' for s in emp_speed]}")

    x0 = np.array([1.913, 5.4, 2000.0, 0.08])
    history: list[dict] = []

    print("\nBaseline evaluation (default params)...")
    baseline_rmse = calibration_objective(
        x0, emp_rho, emp_speed, config_name, n_reps, history,
    )

    print(f"\nOptimizing (max {max_evals} evals)...")
    t0 = time.time()
    result = minimize(
        calibration_objective,
        x0,
        args=(emp_rho, emp_speed, config_name, n_reps, history),
        method="Nelder-Mead",
        options={"maxfev": max_evals, "xatol": 0.01, "fatol": 0.001},
    )
    elapsed = time.time() - t0

    calibrated = {
        "weidmann_gamma": float(result.x[0]),
        "weidmann_rho_max": float(result.x[1]),
        "A": float(result.x[2]),
        "B": float(result.x[3]),
    }

    improvement = (1 - result.fun / baseline_rmse) * 100 if baseline_rmse > 0 else 0

    output = {
        "config": config_name,
        "baseline_rmse": round(baseline_rmse, 4),
        "calibrated_rmse": round(float(result.fun), 4),
        "rmse_reduction_pct": round(improvement, 1),
        "calibrated_params": calibrated,
        "default_params": {
            "weidmann_gamma": 1.913, "weidmann_rho_max": 5.4,
            "A": 2000.0, "B": 0.08,
        },
        "n_evaluations": len(history),
        "elapsed_seconds": round(elapsed, 1),
        "empirical_densities": emp_rho.tolist(),
        "empirical_speeds": emp_speed.tolist(),
        "history": history,
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Calibration complete ({elapsed/60:.1f} min)")
    print(f"  Baseline RMSE:   {baseline_rmse:.4f} m/s")
    print(f"  Calibrated RMSE: {result.fun:.4f} m/s")
    print(f"  Improvement:     {improvement:.1f}%")
    print(f"  Params: gamma={calibrated['weidmann_gamma']:.3f}, "
          f"rho_max={calibrated['weidmann_rho_max']:.2f}, "
          f"A={calibrated['A']:.0f}, B={calibrated['B']:.3f}")
    print(f"  Saved: {output_path}")
    print(f"{'='*50}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DT Level 2: calibrate model to FZJ empirical data",
    )
    parser.add_argument("--config", default="C1", help="Steering config (default: C1)")
    parser.add_argument("--max-evals", type=int, default=40, help="Max evaluations (default: 40)")
    parser.add_argument("--n-reps", type=int, default=3, help="Reps per density point (default: 3)")
    parser.add_argument("--output", default="results/calibration.json", help="Output path")
    args = parser.parse_args()

    run_calibration(
        config_name=args.config,
        max_evals=args.max_evals,
        n_reps=args.n_reps,
        output_path=args.output,
    )
