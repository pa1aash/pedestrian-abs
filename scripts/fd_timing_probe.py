"""Quick timing probe for fresh FD sweep: 6 runs, 3 densities x 2 configs."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.calibrate_dt import simulate_fd_point

PARAMS = {"weidmann_gamma": 0.8327, "weidmann_rho_max": 5.977, "A": 2000.0, "B": 0.08}

for cfg in ["C1", "C4"]:
    for rho in [0.5, 2.5, 5.0]:
        t0 = time.perf_counter()
        v = simulate_fd_point(PARAMS, cfg, rho, n_reps=1)
        wall = time.perf_counter() - t0
        print(f"{cfg} rho={rho:.1f}  speed={v:.3f}  wall={wall:.1f}s", flush=True)
