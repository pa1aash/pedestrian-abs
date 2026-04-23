"""Option-3 gate-activation scenario: force local density past rho_0 = 4.0.

Purpose
-------
The paper currently admits (§4.4) that the density-adaptive ORCA fade-out
sigmoid is never exercised in its transition regime, because all observed
Voronoi densities in the reported scenarios stay below ~1.6 ped/m^2 (far
below rho_0 = 4.0). This script runs a supplementary high-density scenario
designed so that local density at the bottleneck throat crosses rho_0, and
compares:

  * C1          -- SFM only (baseline, no ORCA).
  * C4          -- full hybrid with the density gate active (rho_0 = 4.0).
  * C4_nogate   -- full hybrid with rho_0 = 1000 (gate permanently open;
                   ORCA never fades). This is the ablation that isolates
                   the gate's effect.

If the gate activates in the intended regime, C4 should differ from
C4_nogate in evacuation time and/or peak density; max local density
should exceed rho_0; and the w_o = 1 - sigma(rho; rho_0, k_slope) time
series should drop below 1 for a non-trivial fraction of agent-timesteps.

Geometry
--------
5 x 5 m room with a 0.4 m exit on the right wall, centred at y = 2.5.
60 agents (radius 0.25 m, heterogeneous speeds from N(1.34, 0.26)).
Average density = 60/25 = 2.4 ped/m^2. The exit is narrower than the
smoke-test setup (0.5 m) to force throat compression past rho > 5,
where w_o drops below 0.12 and C4 must differ from C4_nogate.

Rejection-sampled initial placement (matches the correction introduced
in the paper's §4.5 methodological note).

Usage
-----
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \\
        python scripts/gate_activation_test.py --workers 10

Add ``--quick`` for a single-seed smoke test (~2 min).

Outputs
-------
    results_new/gate_activation/Bottleneck_HD_{cfg}_seed{s}.csv         -- per-run summary
    results_new/gate_activation/trajectories/{cfg}_seed{s}.parquet       -- positions over time
    results_analysis/gate_activation_summary.csv                         -- aggregate stats
    figures/gate_activation.pdf                                          -- w_o time-series and density distributions
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
import csv
import multiprocessing as mp
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# ---------------------------------------------------------------------------
# Scenario constants
# ---------------------------------------------------------------------------
ROOM_W = 5.0                      # room width (x)
ROOM_H = 5.0                      # room height (y)
EXIT_WIDTH = 0.4                  # tightened from 0.5 to push throat rho > 5
EXIT_Y = 2.5                      # centre of the exit gap
N_AGENTS = 60
MAX_TIME = 60.0                   # 1 min sim time cap — queue forms in first ~15 s
MAX_STEPS = 200_000
SPAWN_AREA = (0.3, ROOM_W - 0.3, 0.3, ROOM_H - 0.3)  # keep 0.3 m wall margin
GOAL = (ROOM_W + 1.0, EXIT_Y)

# Gate regimes
RHO_ORCA_FADE_DEFAULT = 4.0       # C4 (paper default): gate centred on Fruin LoS-E
K_ORCA_FADE_DEFAULT = 2.0
RHO_ORCA_FADE_DISABLED = 1000.0   # C4_nogate: gate effectively off

DEFAULT_SEEDS = list(range(42, 67))    # 25 seeds, matching paper convention
CONFIGS = ["C1", "C4", "C4_nogate"]

OUT_DIR = REPO / "results_new" / "gate_activation"
TRAJ_DIR = OUT_DIR / "trajectories"
ANALYSIS_OUT = REPO / "results_analysis" / "gate_activation_summary.csv"
FIG_OUT = REPO / "figures" / "gate_activation.pdf"


# ---------------------------------------------------------------------------
# Custom scenario
# ---------------------------------------------------------------------------
def build_scenario(seed: int):
    """Build a small high-density bottleneck scenario with no-overlap spawn."""
    import numpy as np

    from sim.core.agent import AgentState
    from sim.core.world import Wall, World
    from sim.scenarios.base import Scenario

    class HighDensityBottleneck(Scenario):
        n_agents = N_AGENTS
        exit_width = EXIT_WIDTH

        def build(self, seed: int = 42):
            half = EXIT_WIDTH / 2.0
            walls = [
                Wall(np.array([0.0, 0.0]),        np.array([ROOM_W, 0.0])),           # bottom
                Wall(np.array([0.0, ROOM_H]),     np.array([0.0, 0.0])),              # left
                Wall(np.array([ROOM_W, ROOM_H]),  np.array([0.0, ROOM_H])),           # top
                Wall(np.array([ROOM_W, 0.0]),     np.array([ROOM_W, EXIT_Y - half])), # right below exit
                Wall(np.array([ROOM_W, EXIT_Y + half]), np.array([ROOM_W, ROOM_H])),  # right above exit
            ]
            state = AgentState.create(
                N_AGENTS,
                spawn_area=SPAWN_AREA,
                goals=np.array(GOAL),
                seed=seed,
            )
            return World(walls), state

        def is_complete(self, agent_state, time):
            return agent_state.n_active == 0

    return HighDensityBottleneck()


def sample_no_overlap(n, radii, spawn_area, rng, max_tries=50_000):
    """Reject-sample non-overlapping 2D positions."""
    import numpy as np

    x0, x1, y0, y1 = spawn_area
    lo = np.array([x0, y0])
    hi = np.array([x1, y1])
    positions = np.zeros((n, 2))
    for i in range(n):
        placed = False
        for _ in range(max_tries):
            cand = rng.uniform(lo, hi)
            if i == 0:
                positions[i] = cand
                placed = True
                break
            d = np.linalg.norm(positions[:i] - cand, axis=1)
            if (d >= radii[:i] + radii[i]).all():
                positions[i] = cand
                placed = True
                break
        if not placed:
            raise RuntimeError(
                f"Rejection sampling failed at agent {i}/{n}; "
                "the room/spawn area may be too small."
            )
    return positions


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
def run_one(cell):
    import time as _time

    import numpy as np
    import yaml

    from sim.core.integrator import EulerIntegrator
    from sim.core.simulation import Simulation
    from sim.experiments.configs import get_config, get_param_overrides
    from sim.steering.hybrid import HybridSteeringModel

    config_label, seed = cell

    # Resolve which real config to use and whether to disable the gate.
    if config_label == "C1":
        config_name = "C1"
        disable_gate = False
    elif config_label == "C4":
        config_name = "C4"
        disable_gate = False
    elif config_label == "C4_nogate":
        config_name = "C4"
        disable_gate = True
    else:
        raise ValueError(f"Unknown config {config_label}")

    scenario = build_scenario(seed)
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
    if disable_gate:
        flat["rho_orca_fade"] = RHO_ORCA_FADE_DISABLED
        flat["k_orca_fade"] = K_ORCA_FADE_DEFAULT
    else:
        flat.setdefault("rho_orca_fade", RHO_ORCA_FADE_DEFAULT)
        flat.setdefault("k_orca_fade", K_ORCA_FADE_DEFAULT)

    config = get_config(config_name)
    steering = HybridSteeringModel(config, flat)
    sim = Simulation(
        world, agent_state, steering, EulerIntegrator(), flat,
        log_positions=True, seed=seed,
    )
    sim._scenario = scenario

    t0 = _time.perf_counter()
    result = sim.run(max_steps=MAX_STEPS, max_time=MAX_TIME)
    wall = _time.perf_counter() - t0

    traj_path = TRAJ_DIR / f"{config_label}_seed{seed}.parquet"
    sim.write_logs(trajectory_path=str(traj_path))

    return {
        "config": config_label,
        "seed": seed,
        "wall_time_s": wall,
        "rho_orca_fade": flat["rho_orca_fade"],
        "n_steps": result.get("n_steps"),
        "evacuation_time": result.get("evacuation_time"),
        "mean_speed": result.get("mean_speed"),
        "max_density_gridstep": result.get("max_density"),
        "agents_exited": result.get("agents_exited"),
        "trajectory_path": str(traj_path.relative_to(REPO)),
    }


# ---------------------------------------------------------------------------
# Post-hoc density + gate analysis
# ---------------------------------------------------------------------------
def analyse(rows):
    """For each run, compute per-frame Voronoi density and gate values."""
    import numpy as np
    import pandas as pd
    from sim.density.voronoi import VoronoiDensityEstimator

    # Domain polygon for Voronoi clipping
    domain = np.array([
        [0.0, 0.0], [ROOM_W, 0.0], [ROOM_W, ROOM_H], [0.0, ROOM_H]
    ])
    estimator = VoronoiDensityEstimator(domain=domain)

    def sigmoid(x, x0, k):
        return 1.0 / (1.0 + np.exp(-k * (x - x0)))

    aggregates = []
    for row in rows:
        traj = pd.read_parquet(REPO / row["trajectory_path"])
        if len(traj) == 0:
            aggregates.append({**row,
                "max_rho_voronoi": float("nan"),
                "mean_rho_voronoi": float("nan"),
                "frac_rho_gt_rho0": 0.0,
                "min_w_o": 1.0,
                "mean_w_o": 1.0,
                "frac_w_o_lt_0.9": 0.0,
                "frac_w_o_lt_0.5": 0.0,
            })
            continue

        # Sample one frame every ~0.1 s (every 10 steps at dt=0.01) to keep cost down
        times = sorted(traj["t"].unique())
        sample_times = times[::10] or times[:1]

        max_rho = 0.0
        all_rhos: list[float] = []
        for t in sample_times:
            frame = traj[traj["t"] == t]
            pos = frame[["x", "y"]].values
            if len(pos) < 4:
                continue
            rho = estimator.estimate(pos)
            rho = rho[np.isfinite(rho)]
            if len(rho) == 0:
                continue
            all_rhos.extend(rho.tolist())
            if rho.max() > max_rho:
                max_rho = float(rho.max())

        if not all_rhos:
            aggregates.append({**row,
                "max_rho_voronoi": float("nan"),
                "mean_rho_voronoi": float("nan"),
                "frac_rho_gt_rho0": 0.0,
                "min_w_o": 1.0,
                "mean_w_o": 1.0,
                "frac_w_o_lt_0.9": 0.0,
                "frac_w_o_lt_0.5": 0.0,
            })
            continue

        rhos = np.asarray(all_rhos)
        w_o = 1.0 - sigmoid(rhos, RHO_ORCA_FADE_DEFAULT, K_ORCA_FADE_DEFAULT)
        aggregates.append({**row,
            "max_rho_voronoi": float(rhos.max()),
            "mean_rho_voronoi": float(rhos.mean()),
            "frac_rho_gt_rho0": float((rhos > RHO_ORCA_FADE_DEFAULT).mean()),
            "min_w_o": float(w_o.min()),
            "mean_w_o": float(w_o.mean()),
            "frac_w_o_lt_0.9": float((w_o < 0.9).mean()),
            "frac_w_o_lt_0.5": float((w_o < 0.5).mean()),
        })
    return aggregates


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
def make_figure(rows):
    """Two-panel figure: density distribution and w_o distribution."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from sim.density.voronoi import VoronoiDensityEstimator

    domain = np.array([
        [0.0, 0.0], [ROOM_W, 0.0], [ROOM_W, ROOM_H], [0.0, ROOM_H]
    ])
    estimator = VoronoiDensityEstimator(domain=domain)

    def sigmoid(x, x0, k):
        return 1.0 / (1.0 + np.exp(-k * (x - x0)))

    # Aggregate rho samples per config
    per_cfg: dict[str, list[float]] = {}
    for row in rows:
        traj = pd.read_parquet(REPO / row["trajectory_path"])
        if len(traj) == 0:
            continue
        times = sorted(traj["t"].unique())[::10]
        rhos = []
        for t in times:
            pos = traj[traj["t"] == t][["x", "y"]].values
            if len(pos) < 4:
                continue
            r = estimator.estimate(pos)
            rhos.extend(r[np.isfinite(r)].tolist())
        per_cfg.setdefault(row["config"], []).extend(rhos)

    plt.rcParams.update({
        "font.family": "serif", "font.size": 9,
        "axes.labelsize": 10, "savefig.bbox": "tight", "savefig.dpi": 300,
    })

    fig, (ax_rho, ax_gate) = plt.subplots(1, 2, figsize=(7.0, 3.0))

    # Panel 1: density histogram (pooled over agents and frames)
    bins = np.linspace(0, 10, 41)
    for cfg, values in per_cfg.items():
        arr = np.asarray(values)
        ax_rho.hist(arr, bins=bins, alpha=0.5, label=cfg, density=True)
    ax_rho.axvline(RHO_ORCA_FADE_DEFAULT, color="k", ls="--", lw=1.0,
                   label=r"$\rho_0 = 4.0$")
    ax_rho.set_xlabel(r"Voronoi density $\rho$ (ped/m$^2$)")
    ax_rho.set_ylabel("Density (normalised)")
    ax_rho.set_title("Local density distribution")
    ax_rho.legend(fontsize=8)
    ax_rho.grid(True, alpha=0.25)

    # Panel 2: w_o vs rho (the gate) with overlaid observed-rho rug
    rho_grid = np.linspace(0, 10, 400)
    w_grid = 1.0 - sigmoid(rho_grid, RHO_ORCA_FADE_DEFAULT, K_ORCA_FADE_DEFAULT)
    ax_gate.plot(rho_grid, w_grid, color="C0", lw=1.5, label=r"$w_o(\rho)$")
    ax_gate.axvline(RHO_ORCA_FADE_DEFAULT, color="k", ls="--", lw=1.0)
    # Rug of C4 observed densities
    if "C4" in per_cfg:
        rho_c4 = np.asarray(per_cfg["C4"])
        # subsample so the rug is readable
        idx = np.random.default_rng(0).choice(
            len(rho_c4), size=min(len(rho_c4), 2000), replace=False
        )
        ax_gate.plot(rho_c4[idx], np.full(len(idx), -0.04),
                     "|", ms=4, color="C3", alpha=0.3,
                     label=r"observed $\rho$ (C4)")
    ax_gate.set_xlabel(r"Voronoi density $\rho$ (ped/m$^2$)")
    ax_gate.set_ylabel(r"gate weight $w_o$")
    ax_gate.set_title("Gate activation under observed densities")
    ax_gate.set_ylim(-0.1, 1.1)
    ax_gate.legend(fontsize=8, loc="center right")
    ax_gate.grid(True, alpha=0.25)

    fig.tight_layout()
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_OUT, format="pdf")
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--quick", action="store_true",
                   help="Single-seed smoke test (one seed per config).")
    p.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    return p.parse_args()


def main():
    args = parse_args()
    seeds = [args.seeds[0]] if args.quick else args.seeds
    cells = [(cfg, s) for cfg in CONFIGS for s in seeds]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TRAJ_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_OUT.parent.mkdir(parents=True, exist_ok=True)

    print(f"Running {len(cells)} cells  (configs={CONFIGS}, seeds={seeds})")
    print(f"Room {ROOM_W}x{ROOM_H} m, exit {EXIT_WIDTH} m, {N_AGENTS} agents, "
          f"avg density {N_AGENTS/(ROOM_W*ROOM_H):.2f} ped/m^2")
    print(f"Workers: {args.workers}   Out: {OUT_DIR}")

    t0 = time.perf_counter()
    rows: list[dict] = []
    with mp.Pool(args.workers) as pool:
        for row in pool.imap_unordered(run_one, cells, chunksize=1):
            rows.append(row)
            elapsed = time.perf_counter() - t0
            print(f"  {row['config']:<10} seed {row['seed']}  "
                  f"evac={row['evacuation_time']:>7.2f}s  "
                  f"max_rho(gridstep)={row['max_density_gridstep']:.2f}  "
                  f"wall={row['wall_time_s']:.1f}s  "
                  f"(elapsed {elapsed/60:.1f} min)", flush=True)

    rows.sort(key=lambda r: (r["config"], r["seed"]))
    summary_rows = analyse(rows)

    with open(ANALYSIS_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Wrote {ANALYSIS_OUT.relative_to(REPO)}")

    # Per-config summary to stdout
    print("\n=== Aggregate by config (mean +/- std over seeds) ===")
    print(f"{'config':<12} {'n':>3} {'max rho':>16} {'frac rho>rho0':>18} "
          f"{'min w_o':>16} {'frac w_o<0.9':>18} {'frac w_o<0.5':>18}")
    from statistics import mean, stdev
    import numpy as _np
    by_cfg: dict[str, list[dict]] = {}
    for r in summary_rows:
        by_cfg.setdefault(r["config"], []).append(r)

    def _ms(rs, key):
        vals = [float(x[key]) for x in rs if x[key] == x[key]]
        if not vals:
            return float("nan"), float("nan")
        m = mean(vals)
        s = stdev(vals) if len(vals) > 1 else 0.0
        return m, s

    for cfg, rs in by_cfg.items():
        mr, sr = _ms(rs, "max_rho_voronoi")
        fr, ss = _ms(rs, "frac_rho_gt_rho0")
        mn, sn = _ms(rs, "min_w_o")
        fw9, sw9 = _ms(rs, "frac_w_o_lt_0.9")
        fw5, sw5 = _ms(rs, "frac_w_o_lt_0.5")
        print(f"{cfg:<12} {len(rs):>3} "
              f"{mr:>8.2f}+/-{sr:<5.2f} "
              f"{fr:>10.3f}+/-{ss:<5.3f} "
              f"{mn:>8.3f}+/-{sn:<5.3f} "
              f"{fw9:>10.3f}+/-{sw9:<5.3f} "
              f"{fw5:>10.3f}+/-{sw5:<5.3f}")

    # Paired statistical tests: C4 vs C4_nogate (primary comparison) and C4 vs C1
    print("\n=== Paired Wilcoxon signed-rank tests (Holm-Sidak corrected) ===")
    try:
        from scipy import stats as _sstats

        def paired_test(metric, a_rows, b_rows):
            a_rows = sorted(a_rows, key=lambda r: r["seed"])
            b_rows = sorted(b_rows, key=lambda r: r["seed"])
            a = _np.array([float(r[metric]) for r in a_rows])
            b = _np.array([float(r[metric]) for r in b_rows])
            a = _np.nan_to_num(a, nan=0.0)
            b = _np.nan_to_num(b, nan=0.0)
            diffs = a - b
            if _np.all(diffs == 0):
                return (float("nan"), 1.0, "all ties")
            try:
                stat, p = _sstats.wilcoxon(a, b, zero_method="wilcox")
                return (stat, p, "")
            except Exception as e:
                return (float("nan"), float("nan"), str(e)[:30])

        metrics = ["max_rho_voronoi", "mean_rho_voronoi",
                   "frac_rho_gt_rho0", "min_w_o", "mean_w_o",
                   "frac_w_o_lt_0.9", "frac_w_o_lt_0.5"]
        comparisons = [("C4", "C4_nogate"), ("C4", "C1"), ("C4_nogate", "C1")]

        # Collect raw p-values for Holm-Sidak
        raw = []
        for a_cfg, b_cfg in comparisons:
            if a_cfg not in by_cfg or b_cfg not in by_cfg:
                continue
            for m in metrics:
                _, p, note = paired_test(m, by_cfg[a_cfg], by_cfg[b_cfg])
                raw.append((a_cfg, b_cfg, m, p, note))

        # Holm-Sidak: sort ascending, apply 1 - (1-p)^(n-i+1) with step-down
        valid = [(i, r) for i, r in enumerate(raw) if r[3] == r[3]]
        valid.sort(key=lambda x: x[1][3])
        corrected = [1.0] * len(raw)
        k = len(valid)
        max_so_far = 0.0
        for rank, (orig_idx, r) in enumerate(valid):
            p = r[3]
            p_adj = 1.0 - (1.0 - p) ** (k - rank)
            p_adj = max(p_adj, max_so_far)
            max_so_far = p_adj
            corrected[orig_idx] = p_adj

        print(f"{'comparison':<24} {'metric':<22} {'p_raw':>10} {'p_HS':>10}")
        for (a_cfg, b_cfg, m, p, note), p_hs in zip(raw, corrected):
            sig = "*" if p_hs < 0.05 else ""
            marker = f"({note})" if note else sig
            print(f"{a_cfg+' vs '+b_cfg:<24} {m:<22} {p:>10.4g} {p_hs:>10.4g} {marker}")
    except ImportError:
        print("  scipy not available — skipping paired tests")

    print("\nGenerating figure...")
    make_figure(rows)
    print(f"Wrote {FIG_OUT.relative_to(REPO)}")
    print(f"\nDone in {(time.perf_counter() - t0)/60:.1f} min.")


if __name__ == "__main__":
    mp.freeze_support()
    main()
