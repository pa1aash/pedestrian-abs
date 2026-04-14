#!/usr/bin/env python
"""Phase B: minimal A/B sanity sweep at the existing (gamma*, rho_max*) optimum.

Holds (gamma=0.888, rho_max=5.36) fixed, sweeps:
  A ∈ {500, 2000, 4000}  with B=0.112
  B ∈ {0.01, 0.112, 0.3} with A=1920
1 seed per bin, 10 bins, parallel across bins.
Midpoints (A=2000, B≈1920)+(B=0.112, A=1920) serve as consistency checks vs RMSE≈0.091.
"""
import os, sys, time, csv, hashlib, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
from multiprocessing import Pool
from scripts.calibrate_dt import load_empirical_fd, simulate_fd_point

GAMMA_STAR = 0.888
RHO_MAX_STAR = 5.36
A_FIT = 1920.4
B_FIT = 0.112
CFG = "C1"
N_REPS = 1  # reduced vs original 3 for budget; midpoint RMSE may differ from 0.091 by seed variance


def _one_bin(args):
    rho, params = args
    return simulate_fd_point(params, CFG, float(rho), n_reps=N_REPS)


def evaluate(A: float, B: float, emp_rho, emp_speed, pool) -> tuple[float, float]:
    params = {
        "weidmann_gamma": GAMMA_STAR,
        "weidmann_rho_max": RHO_MAX_STAR,
        "A": float(A),
        "B": float(B),
    }
    t0 = time.time()
    sim_speeds = np.array(pool.map(_one_bin, [(r, params) for r in emp_rho]))
    wall = time.time() - t0
    rmse = float(np.sqrt(np.mean((sim_speeds - emp_speed) ** 2)))
    return rmse, wall


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


if __name__ == "__main__":
    emp_rho, emp_speed = load_empirical_fd()
    print(f"FD bins: {len(emp_rho)} {emp_rho.tolist()}")
    print(f"Fixed: gamma={GAMMA_STAR}, rho_max={RHO_MAX_STAR}; n_reps={N_REPS}")

    os.makedirs("results_new", exist_ok=True)
    with Pool(min(len(emp_rho), os.cpu_count() or 8)) as pool:
        # Midpoint consistency: A=1920, B=0.112 at the existing optimum
        print("\n[consistency] A=1920, B=0.112 (existing optimum midpoint)")
        rmse_mid, w_mid = evaluate(A_FIT, B_FIT, emp_rho, emp_speed, pool)
        print(f"  RMSE={rmse_mid:.4f} wall={w_mid:.1f}s  (target ~0.091)")
        if not (0.05 <= rmse_mid <= 0.15):
            print(f"[HALT] Midpoint RMSE {rmse_mid:.4f} outside [0.05, 0.15]. Sim-layer regression suspected.")
            with open("results_new/calibration_sanity_HALTED.json", "w") as f:
                json.dump({"reason": "midpoint RMSE out of range",
                           "rmse": rmse_mid, "expected": 0.091,
                           "bounds_checked": [0.05, 0.15]}, f, indent=2)
            sys.exit(2)

        # A sweep (B fixed at existing fit)
        a_rows = []
        for A in [500.0, 2000.0, 4000.0]:
            rmse, wall = evaluate(A, B_FIT, emp_rho, emp_speed, pool)
            a_rows.append({"param_value": A, "rmse": rmse, "wall_seconds": wall})
            print(f"  A={A:6.0f} B={B_FIT}: RMSE={rmse:.4f} wall={wall:.1f}s")

        # B sweep (A fixed at existing fit)
        b_rows = []
        for B in [0.01, 0.112, 0.3]:
            rmse, wall = evaluate(A_FIT, B, emp_rho, emp_speed, pool)
            b_rows.append({"param_value": B, "rmse": rmse, "wall_seconds": wall})
            print(f"  A={A_FIT} B={B:.3f}: RMSE={rmse:.4f} wall={wall:.1f}s")

    # Write CSVs
    for name, rows in [("A", a_rows), ("B", b_rows)]:
        path = f"results_new/calibration_sanity_{name}.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["param_value", "rmse", "wall_seconds"])
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {path}  sha256={sha256(path)}")

    # Identifiability verdict
    def verdict(rows, name):
        rmses = [r["rmse"] for r in rows]
        lo, hi = min(rmses), max(rmses)
        rng_pct = 100.0 * (hi - lo) / max(lo, 1e-9)
        consistent = rng_pct < 5.0
        return lo, hi, rng_pct, consistent

    for name, rows in [("A", a_rows), ("B", b_rows)]:
        lo, hi, pct, ok = verdict(rows, name)
        print(f"{name}: RMSE ∈ [{lo:.4f}, {hi:.4f}]  variation {pct:.2f}%  "
              f"{'CONSISTENT' if ok else 'NOT CONSISTENT'} with non-identifiability")

    # Midpoint record
    with open("results_new/calibration_sanity_midpoint.json", "w") as f:
        json.dump({"A": A_FIT, "B": B_FIT, "rmse": rmse_mid,
                   "expected_from_status_json": 0.0908, "wall_seconds": w_mid}, f, indent=2)

    print("\nPhase B complete.")
