#!/usr/bin/env python
"""Generate all 8 publication figures + LaTeX tables from experiment results."""

import json
import os
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sim.viz.style import COLORS, LABELS, set_style, save_figure
from sim.experiments.analysis import Stats


def main():
    input_dir = "results/"
    output_dir = "figures/"
    table_dir = "paper/tables/"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(table_dir, exist_ok=True)

    set_style()

    # ---- Figure 1: Fundamental Diagram (2x2) ----
    fig1_fd(input_dir, output_dir)

    # ---- Figure 2: Ablation bars ----
    fig2_ablation(input_dir, output_dir)

    # ---- Figure 3: Trajectories (bottleneck) ----
    fig3_trajectories(output_dir)

    # ---- Figure 4: Density heatmap (funnel at peak) ----
    fig4_density_heatmap(output_dir)

    # ---- Figure 5: Evacuation vs width ----
    fig5_evac_vs_width(input_dir, output_dir)

    # ---- Figure 6: Scaling ----
    fig6_scaling(input_dir, output_dir)

    # ---- Figure 7: Risk map ----
    fig7_risk_heatmap(output_dir)

    # ---- Figure 8: Optimizer convergence ----
    fig8_convergence(input_dir, output_dir)

    # ---- LaTeX tables ----
    table_parameters(table_dir)
    table_ablation(input_dir, table_dir)
    table_scaling(input_dir, table_dir)
    table_crush(input_dir, table_dir)

    pdfs = glob.glob(os.path.join(output_dir, "*.pdf"))
    texs = glob.glob(os.path.join(table_dir, "*.tex"))
    print(f"\nDone: {len(pdfs)} figures, {len(texs)} tables")
    for f in sorted(pdfs):
        print(f"  {f}")
    for f in sorted(texs):
        print(f"  {f}")


# ============================================================
# FIGURES
# ============================================================

def fig1_fd(input_dir, output_dir):
    """Fundamental diagram 2x2 from continuous-injection fd_*.csv files."""
    from sim.viz.fundamental_diagram import plot_fundamental_diagram, weidmann_speed

    data = {}
    for cfg in ["C1", "C2", "C3", "C4"]:
        f = os.path.join(input_dir, f"fd_{cfg}.csv")
        if os.path.exists(f):
            df = pd.read_csv(f)
            data[cfg] = (df["density"].values, df["speed"].values)

    # Empirical data
    empirical = None
    ef = os.path.join(input_dir, "empirical_fd.csv")
    if os.path.exists(ef):
        edf = pd.read_csv(ef)
        empirical = (edf["mean_density"].values, edf["mean_speed"].values)

    if data:
        path = plot_fundamental_diagram(data, empirical=empirical, output_dir=output_dir)
        print(f"Fig 1: {path}")
    else:
        print("Fig 1: skipped (no fd_*.csv files)")


def fig2_ablation(input_dir, output_dir):
    """Ablation grouped bars for C1/C4 across scenarios."""
    dfs = []
    for f in glob.glob(os.path.join(input_dir, "*Scenario_C*.csv")):
        if "Funnel" in f or "Bottleneck_w" in f:
            continue
        df = pd.read_csv(f)
        dfs.append(df)
    if not dfs:
        print("Fig 2: skipped (no data)")
        return
    combined = pd.concat(dfs, ignore_index=True)
    # Only keep C-configs
    combined = combined[combined["config"].str.startswith("C")]

    from sim.viz.ablation_bars import plot_ablation_bars
    for metric in ["mean_speed", "max_density", "collision_count"]:
        if metric in combined.columns:
            path = plot_ablation_bars(combined, metric=metric, output_dir=output_dir)
            print(f"Fig 2 ({metric}): {path}")


def fig3_trajectories(output_dir):
    """Run a short bottleneck sim and capture trajectories."""
    from sim.core.simulation import Simulation
    from sim.scenarios.bottleneck import BottleneckScenario

    scenario = BottleneckScenario(n_agents=30, exit_width=1.2)
    sim = Simulation.from_scenario(scenario, "C1", seed=42)
    world = sim.world

    positions_log = []
    for _ in range(500):
        sim.step()
        if sim.step_count % 5 == 0:  # sample every 5 steps
            positions_log.append(sim.state.positions.copy())

    from sim.viz.trajectories import plot_trajectories
    path = plot_trajectories(positions_log, walls=world.walls, output_dir=output_dir)
    print(f"Fig 3: {path}")


def fig4_density_heatmap(output_dir):
    """Run 200-agent funnel sim and capture peak-density snapshot."""
    from sim.core.simulation import Simulation
    from sim.scenarios.funnel import FunnelScenario

    scenario = FunnelScenario(n_agents=200)
    sim = Simulation.from_scenario(scenario, "C1", seed=42,
                                    param_overrides={"neighbor_radius": 1.5})

    # Run until congestion builds
    for _ in range(1500):
        sim.step()

    from sim.viz.heatmaps import plot_density_heatmap
    path = plot_density_heatmap(
        sim.state.positions[sim.state.active],
        xlim=(0, 16), ylim=(0, 10),
        resolution=0.5, output_dir=output_dir,
        name="density_heatmap",
    )
    print(f"Fig 4: {path}")


def fig5_evac_vs_width(input_dir, output_dir):
    """Evacuation time vs bottleneck width, lines for C1/C4."""
    set_style()
    fig, ax = plt.subplots(figsize=(5, 4))

    for cfg in ["C1", "C4"]:
        widths, evac_means, evac_lo, evac_hi = [], [], [], []
        for w in [1.2, 2.4, 3.6]:
            f = os.path.join(input_dir, f"Bottleneck_w{w}_{cfg}.csv")
            if os.path.exists(f):
                df = pd.read_csv(f)
                m, lo, hi = Stats.confidence_interval(df["evacuation_time"].values)
                widths.append(w)
                evac_means.append(m)
                evac_lo.append(m - lo)
                evac_hi.append(hi - m)
        if widths:
            ax.errorbar(widths, evac_means, yerr=[evac_lo, evac_hi],
                        fmt="o-", color=COLORS[cfg], label=LABELS[cfg],
                        capsize=4, lw=1.5)

    ax.set_xlabel("Exit width (m)")
    ax.set_ylabel("Evacuation time (s)")
    ax.legend()
    fig.tight_layout()
    path = save_figure(fig, "evac_vs_width", output_dir)
    print(f"Fig 5: {path}")


def fig6_scaling(input_dir, output_dir):
    """Log-log scaling plot."""
    f = os.path.join(input_dir, "scaling_C1.csv")
    if not os.path.exists(f):
        print("Fig 6: skipped (no scaling data)")
        return
    from sim.viz.scaling import plot_scaling
    df = pd.read_csv(f)
    path = plot_scaling(df, output_dir=output_dir)
    print(f"Fig 6: {path}")


def fig7_risk_heatmap(output_dir):
    """Run 200-agent funnel sim and compute composite risk."""
    from sim.core.simulation import Simulation
    from sim.scenarios.funnel import FunnelScenario
    from sim.density.grid import GridDensityEstimator
    from sim.density.kde import KDEDensityEstimator
    from sim.density.risk import CompositeRiskMetric
    from scipy.spatial import KDTree

    scenario = FunnelScenario(n_agents=200)
    sim = Simulation.from_scenario(scenario, "C1", seed=42,
                                    param_overrides={"neighbor_radius": 1.5})
    for _ in range(1500):
        sim.step()

    active = sim.state.active
    pos = sim.state.positions[active]
    vel = sim.state.velocities[active]

    grid = GridDensityEstimator(radius=1.5)
    kde = KDEDensityEstimator(bandwidth=1.0)
    rho_g = grid.estimate(pos)
    rho_k = kde.estimate(pos)

    tree = KDTree(pos)
    nbs = tree.query_ball_point(pos, r=1.5)

    risk = CompositeRiskMetric()
    R = risk.compute(pos, vel, rho_g, rho_k, nbs)

    from sim.viz.heatmaps import plot_risk_heatmap
    path = plot_risk_heatmap(pos, R, xlim=(0, 16), ylim=(0, 10),
                              resolution=0.5, output_dir=output_dir,
                              name="risk_heatmap")
    print(f"Fig 7: {path}")


def fig8_convergence(input_dir, output_dir):
    """Optimizer convergence from history JSON."""
    f = os.path.join(input_dir, "optimizer_history.json")
    if not os.path.exists(f):
        print("Fig 8: skipped (no optimizer history)")
        return
    with open(f) as fh:
        history = json.load(fh)
    from sim.viz.convergence import plot_convergence
    path = plot_convergence(history, output_dir=output_dir)
    print(f"Fig 8: {path}")


# ============================================================
# LATEX TABLES
# ============================================================

def table_parameters(table_dir):
    """Parameter table from params.yaml."""
    import yaml
    with open("config/params.yaml") as f:
        params = yaml.safe_load(f)

    lines = [
        r"\begin{tabular}{llr}",
        r"\hline",
        r"\textbf{Parameter} & \textbf{Symbol} & \textbf{Value} \\",
        r"\hline",
    ]
    param_rows = [
        ("Social repulsion", "$A$", f"{params['sfm']['A']:.0f} N"),
        ("Repulsion range", "$B$", f"{params['sfm']['B']:.2f} m"),
        ("Body compression", "$k$", f"{params['sfm']['k']:.0f} kg/s$^2$"),
        ("Friction", r"$\kappa$", f"{params['sfm']['kappa']:.0f} kg/(m$\\cdot$s)"),
        ("TTC gain", "$k_\\text{{ttc}}$", f"{params['ttc']['k_ttc']:.1f}"),
        ("TTC decay", r"$\tau_0$", f"{params['ttc']['tau_0']:.1f} s"),
        ("ORCA horizon", r"$\tau_h$", f"{params['orca']['time_horizon']:.1f} s"),
        ("Crush compression", "$k_\\text{{crush}}$", f"{params['crush']['k_crush']:.0f} kg/s$^2$"),
        ("Desired speed", "$v_0$", f"{params['agent']['desired_speed']:.2f} m/s"),
        ("Agent radius", "$r$", f"{params['agent']['radius']:.2f} m"),
        ("Timestep", "$\\Delta t$", f"{params['simulation']['dt']:.2f} s"),
    ]
    for name, sym, val in param_rows:
        lines.append(f"{name} & {sym} & {val} \\\\")
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")

    path = os.path.join(table_dir, "parameters.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Table: {path}")


def table_ablation(input_dir, table_dir):
    """Ablation results table: scenario x config."""
    dfs = []
    for f in glob.glob(os.path.join(input_dir, "*Scenario_C*.csv")):
        if "Funnel" in f or "Bottleneck_w" in f:
            continue
        dfs.append(pd.read_csv(f))
    if not dfs:
        return
    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[combined["config"].str.startswith("C")]

    scenarios = sorted(combined["scenario"].unique())
    configs = ["C1", "C4"]

    lines = [
        r"\begin{tabular}{l" + "r" * len(configs) + "}",
        r"\hline",
        r"\textbf{Scenario} & " + " & ".join([f"\\textbf{{{c}}}" for c in configs]) + r" \\",
        r"\hline",
    ]
    for scen in scenarios:
        cells = [scen.replace("Scenario", "")]
        for cfg in configs:
            subset = combined[(combined["scenario"] == scen) & (combined["config"] == cfg)]
            if len(subset) > 0:
                m, lo, hi = Stats.confidence_interval(subset["mean_speed"].values)
                cells.append(f"{m:.2f}")
            else:
                cells.append("--")
        lines.append(" & ".join(cells) + r" \\")
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")

    path = os.path.join(table_dir, "ablation.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Table: {path}")


def table_scaling(input_dir, table_dir):
    """Scaling table."""
    f = os.path.join(input_dir, "scaling_C1.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f)

    lines = [
        r"\begin{tabular}{rr}",
        r"\hline",
        r"\textbf{Agents} & \textbf{ms/step} \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(f"{int(row['n_agents'])} & {row['ms_per_step']:.1f} \\\\")
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")

    path = os.path.join(table_dir, "scaling.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Table: {path}")


def table_crush(input_dir, table_dir):
    """Crush threshold comparison table (D1-D4)."""
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\hline",
        r"\textbf{Config} & $\rho_\text{crit}$ & \textbf{Max Density} & \textbf{Exits} & \textbf{Collisions} \\",
        r"\hline",
    ]
    thresholds = {"D1": "none", "D2": "5.0", "D3": "5.5", "D4": "7.0"}
    for d in ["D1", "D2", "D3", "D4"]:
        f = os.path.join(input_dir, f"Crush_{d}.csv")
        if os.path.exists(f):
            df = pd.read_csv(f)
            lines.append(
                f"{d} & {thresholds[d]} & {df['max_density'].mean():.1f} & "
                f"{df['agents_exited'].mean():.0f}/200 & {df['collision_count'].mean():.0f} \\\\"
            )
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")

    path = os.path.join(table_dir, "crush.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Table: {path}")


if __name__ == "__main__":
    main()
