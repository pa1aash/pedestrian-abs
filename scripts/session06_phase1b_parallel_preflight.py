#!/usr/bin/env python
"""Phase 1b: parallel-pool preflight + reproducibility check + projection."""
import os, sys, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
from multiprocessing import Pool
from scripts.calibrate_dt import load_empirical_fd, simulate_fd_point


PARAMS = {"weidmann_gamma": 1.913, "weidmann_rho_max": 5.4, "A": 2000.0, "B": 0.08}
CFG = "C1"
NREPS = 3


def _one_bin(rho):
    return simulate_fd_point(PARAMS, CFG, float(rho), n_reps=NREPS)


if __name__ == "__main__":
    emp_rho, emp_speed = load_empirical_fd()
    print(f"FD bins: {len(emp_rho)} -> {emp_rho.tolist()}")

    # SERIAL baseline
    t0 = time.time()
    serial = np.array([_one_bin(r) for r in emp_rho])
    t_serial = time.time() - t0
    rmse_serial = float(np.sqrt(np.mean((serial - emp_speed) ** 2)))
    print(f"\nSERIAL: {t_serial:.1f} s  RMSE={rmse_serial:.6f}")

    # PARALLEL
    n_workers = min(len(emp_rho), os.cpu_count() or 8)
    t0 = time.time()
    with Pool(n_workers) as pool:
        par = np.array(pool.map(_one_bin, emp_rho.tolist()))
    t_par = time.time() - t0
    rmse_par = float(np.sqrt(np.mean((par - emp_speed) ** 2)))
    print(f"PARALLEL ({n_workers} workers): {t_par:.1f} s  RMSE={rmse_par:.6f}")

    diff = float(np.max(np.abs(serial - par)))
    bit_identical = diff == 0.0
    rmse_match = abs(rmse_serial - rmse_par) < 1e-12
    print(f"\nMax per-bin speed diff: {diff:.2e}")
    print(f"RMSE match (1e-12): {rmse_match}")
    print(f"Bit-identical: {bit_identical}")

    speedup = t_serial / t_par
    print(f"Speedup: {speedup:.2f}x ({n_workers} workers)")

    # Projection
    per_eval_s = t_par
    nm_per_restart = 25
    sanity = 10
    opt_b = (11 * nm_per_restart + sanity) * per_eval_s / 3600.0
    opt_c = (5 * nm_per_restart + sanity) * per_eval_s / 3600.0
    print(f"\nPer-eval (parallel): {per_eval_s:.1f} s = {per_eval_s/60:.2f} min")
    print(f"Option B (11 restarts × 25 + 10 sanity): {opt_b:.2f} wall-hours")
    print(f"Option C (5 restarts × 25 + 10 sanity):  {opt_c:.2f} wall-hours")
    if opt_b <= 12:
        sel = "B"
    elif opt_b <= 24:
        sel = "C"
    else:
        sel = "HALT"
    print(f"SELECTED: {sel}")
