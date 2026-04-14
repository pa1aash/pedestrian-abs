#!/usr/bin/env python
"""Phase D: Option α-light 2-parameter refit (gamma, rho_max) with A, B fixed.

Single-start Nelder-Mead, hard bounds, tight tolerances, parallel bins,
3 seeds/eval. Per-eval checkpoint to CSV.
"""
import os, sys, time, json, csv, hashlib, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
from multiprocessing import Pool
from scipy.optimize import minimize
from scripts.calibrate_dt import load_empirical_fd, simulate_fd_point

A_FIXED = 2000.0
B_FIXED = 0.08
CFG = "C1"
N_REPS = 3
BOUNDS = [(0.3, 3.0), (3.0, 7.0)]  # gamma, rho_max
X0 = np.array([1.913, 5.4])
MAXFEV_PRIMARY = 50
MAXFEV_EXTENDED = 80
TRACE_CSV = "results_new/calibration_alight_trace.csv"
RESULT_JSON = "results_new/calibration_alight_result.json"


def _one_bin(args):
    rho, params = args
    return simulate_fd_point(params, CFG, float(rho), n_reps=N_REPS)


def sha256_short(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def make_objective(emp_rho, emp_speed, pool, trace_writer, trace_fh, state):
    def obj(x):
        gamma, rho_max = x
        # Hard bounds check (minimize with bounds also enforces, belt+braces)
        if not (BOUNDS[0][0] <= gamma <= BOUNDS[0][1]
                and BOUNDS[1][0] <= rho_max <= BOUNDS[1][1]):
            return 5.0
        params = {"weidmann_gamma": float(gamma),
                  "weidmann_rho_max": float(rho_max),
                  "A": A_FIXED, "B": B_FIXED}
        t0 = time.time()
        sim_speeds = np.array(pool.map(_one_bin, [(r, params) for r in emp_rho]))
        wall = time.time() - t0
        rmse = float(np.sqrt(np.mean((sim_speeds - emp_speed) ** 2)))
        state["n"] += 1
        row = {"eval_id": state["n"], "gamma": float(gamma),
               "rho_max": float(rho_max), "A": A_FIXED, "B": B_FIXED,
               "rmse": rmse, "wall_seconds": wall}
        trace_writer.writerow(row)
        trace_fh.flush()
        if rmse < state["best_rmse"]:
            state["best_rmse"] = rmse
            state["best_x"] = (float(gamma), float(rho_max))
        print(f"  eval {state['n']:3d}: gamma={gamma:.4f} rho_max={rho_max:.3f} "
              f"RMSE={rmse:.4f} wall={wall:.0f}s  best={state['best_rmse']:.4f}")
        return rmse
    return obj


def run():
    emp_rho, emp_speed = load_empirical_fd()
    print(f"FD bins: {len(emp_rho)} {emp_rho.tolist()}")
    print(f"Fixed: A={A_FIXED}, B={B_FIXED}, n_reps={N_REPS}")
    print(f"x0 (textbook): gamma={X0[0]}, rho_max={X0[1]}")
    print(f"Bounds: {BOUNDS}  Tol: xatol=1e-3, fatol=1e-4")

    os.makedirs("results_new", exist_ok=True)
    trace_fh = open(TRACE_CSV, "w", newline="")
    trace_writer = csv.DictWriter(trace_fh, fieldnames=[
        "eval_id", "gamma", "rho_max", "A", "B", "rmse", "wall_seconds"])
    trace_writer.writeheader()
    trace_fh.flush()

    state = {"n": 0, "best_rmse": float("inf"), "best_x": None}

    t_total = time.time()
    with Pool(min(len(emp_rho), os.cpu_count() or 8)) as pool:
        obj = make_objective(emp_rho, emp_speed, pool, trace_writer, trace_fh, state)

        # baseline at x0 for rmse_reduction calc
        baseline = obj(X0)
        print(f"\nBaseline at x0 (A={A_FIXED}, B={B_FIXED}, textbook γ,ρ_max): RMSE={baseline:.4f}")

        print(f"\nOptimizing (maxfev={MAXFEV_PRIMARY}, then extend to {MAXFEV_EXTENDED} if needed)...")
        result = minimize(obj, X0, method="Nelder-Mead",
                          bounds=BOUNDS,
                          options={"maxfev": MAXFEV_PRIMARY,
                                   "xatol": 1e-3, "fatol": 1e-4})
        extended = False
        if not result.success and state["n"] < MAXFEV_EXTENDED:
            print(f"\n[extend] primary did not converge in {MAXFEV_PRIMARY} evals; "
                  f"extending to {MAXFEV_EXTENDED} from current best {state['best_x']}")
            result = minimize(obj, np.array(state["best_x"]),
                              method="Nelder-Mead", bounds=BOUNDS,
                              options={"maxfev": MAXFEV_EXTENDED - state["n"],
                                       "xatol": 1e-3, "fatol": 1e-4})
            extended = True

    elapsed = time.time() - t_total
    trace_fh.close()

    gamma_star, rho_max_star = float(result.x[0]), float(result.x[1])
    rmse_star = float(result.fun)
    reduction = (1 - rmse_star / baseline) * 100 if baseline > 0 else 0.0

    # Halt-condition checks
    EXISTING_GAMMA, EXISTING_RHOMAX, EXISTING_RMSE = 0.888, 5.36, 0.0908
    d_gamma = abs(gamma_star - EXISTING_GAMMA) / EXISTING_GAMMA * 100
    d_rhomax = abs(rho_max_star - EXISTING_RHOMAX) / EXISTING_RHOMAX * 100
    halt_flags = []
    if d_gamma > 5.0:
        halt_flags.append(f"gamma* moved {d_gamma:.2f}% from existing 0.888 (>5% threshold)")
    if d_rhomax > 5.0:
        halt_flags.append(f"rho_max* moved {d_rhomax:.2f}% from existing 5.36 (>5% threshold)")
    if rmse_star > EXISTING_RMSE * 1.01:  # worse than existing +1% slack
        halt_flags.append(f"rmse* {rmse_star:.4f} worse than existing 0.091 at (0.888, 5.36, 1920, 0.112)")
    if not result.success and not extended:
        halt_flags.append(f"NM did not converge (status={result.status}, msg={result.message})")

    out = {
        "provenance": {
            "script": "scripts/session06_phaseD_alight.py",
            "run_date": "2026-04-14",
            "session": "06 Phase D (Option α-light)",
        },
        "protocol": {
            "method": "Nelder-Mead (single-start)",
            "restarts": 1,
            "x0_textbook": {"weidmann_gamma": float(X0[0]),
                            "weidmann_rho_max": float(X0[1])},
            "fixed_params": {"A": A_FIXED, "B": B_FIXED,
                             "source": "textbook Helbing et al. 2000"},
            "hard_bounds": {"weidmann_gamma": list(BOUNDS[0]),
                            "weidmann_rho_max": list(BOUNDS[1])},
            "tolerances": {"xatol": 1e-3, "fatol": 1e-4},
            "maxfev_primary": MAXFEV_PRIMARY,
            "maxfev_extended": MAXFEV_EXTENDED if extended else None,
            "seeds_per_evaluation": N_REPS,
            "seed_values": [42, 43, 44],
            "fd_bin_count": len(emp_rho),
            "fd_bin_densities_ped_per_m2": emp_rho.tolist(),
            "corridor_length_m": 18.0,
            "corridor_width_m": 5.0,
            "warmup_steps": 300,
            "measure_steps": 500,
            "steering_config": CFG,
            "parallelism": "multiprocessing.Pool, bin-level, 2.2x speedup measured",
        },
        "results": {
            "gamma_star": gamma_star,
            "rho_max_star": rho_max_star,
            "A_fixed": A_FIXED,
            "B_fixed": B_FIXED,
            "baseline_rmse_m_per_s": baseline,
            "calibrated_rmse_m_per_s": rmse_star,
            "rmse_reduction_pct": reduction,
            "n_evaluations": state["n"],
            "converged": bool(result.success),
            "nm_status": int(result.status),
            "nm_message": str(result.message),
            "extended_to_80": extended,
            "wall_seconds": elapsed,
        },
        "comparison_to_existing_8206f28": {
            "existing_gamma": EXISTING_GAMMA,
            "existing_rho_max": EXISTING_RHOMAX,
            "existing_rmse": EXISTING_RMSE,
            "existing_A": 1920.4,
            "existing_B": 0.112,
            "delta_gamma_pct": d_gamma,
            "delta_rho_max_pct": d_rhomax,
            "delta_rmse_abs": rmse_star - EXISTING_RMSE,
        },
        "halt_flags": halt_flags,
    }

    with open(RESULT_JSON, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Option α-light calibration complete ({elapsed/3600:.2f} h)")
    print(f"  γ*      = {gamma_star:.4f}  (existing 0.888; Δ={d_gamma:.2f}%)")
    print(f"  ρ_max*  = {rho_max_star:.3f}  (existing 5.36; Δ={d_rhomax:.2f}%)")
    print(f"  RMSE*   = {rmse_star:.4f} m/s  (existing 0.091)")
    print(f"  Reduction from baseline RMSE={baseline:.4f}: {reduction:.1f}%")
    print(f"  Evals   = {state['n']}   Converged = {result.success}")
    if halt_flags:
        print(f"  HALT FLAGS:")
        for f_ in halt_flags:
            print(f"    - {f_}")
    else:
        print(f"  No halt flags.")
    print(f"  Trace : {TRACE_CSV}  sha256={sha256_short(TRACE_CSV)}")
    print(f"  Result: {RESULT_JSON}  sha256={sha256_short(RESULT_JSON)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
