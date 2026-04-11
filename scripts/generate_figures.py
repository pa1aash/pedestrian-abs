#!/usr/bin/env python
"""Generate all 8 publication figures + LaTeX tables from experiment results."""

import json
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        edf = edf[edf["mean_density"] <= 6.0]  # truncate to match sim range
        empirical = (edf["mean_density"].values, edf["mean_speed"].values)

    if data:
        path = plot_fundamental_diagram(data, empirical=empirical, output_dir=output_dir)
        print(f"Fig 1: {path}")
    else:
        print("Fig 1: skipped (no fd_*.csv files)")


def fig2_ablation(input_dir, output_dir):
    """Ablation grouped bars for C1/C4 across scenarios.

    Bottleneck row uses Bottleneck_w1.2m (50 agents, fully evacuating)
    to match the canonical ablation comparison rather than the legacy
    BottleneckScenario_C*.csv files which contain w=0.8m deadlock data.
    """
    dfs = []
    # Bidirectional + Crossing from default scenario CSVs
    for scen in ["BidirectionalScenario", "CrossingScenario"]:
        for cfg in ["C1", "C2", "C3", "C4"]:
            f = os.path.join(input_dir, f"{scen}_{cfg}.csv")
            if os.path.exists(f):
                dfs.append(pd.read_csv(f))
    # Bottleneck from canonical w=1.2m runs (50 agents, fully evacuating)
    for cfg in ["C1", "C2", "C3", "C4"]:
        f = os.path.join(input_dir, f"Bottleneck_w1.2_{cfg}.csv")
        if os.path.exists(f):
            df = pd.read_csv(f)
            df = df.copy()
            df["scenario"] = "BottleneckScenario"
            dfs.append(df)
    if not dfs:
        print("Fig 2: skipped (no data)")
        return
    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[combined["config"].str.startswith("C")]

    from sim.viz.ablation_bars import plot_ablation_bars
    for metric in ["mean_speed", "max_density", "collision_count"]:
        if metric in combined.columns:
            path = plot_ablation_bars(combined, metric=metric, output_dir=output_dir)
            print(f"Fig 2 ({metric}): {path}")


def fig3_trajectories(output_dir):
    """C1 vs C4 trajectory comparison at 0.8m exit (deadlock vs successful evac).

    Uses seed 46: a configuration where C1 (SFM only) deadlocks at the exit
    and C4 (full hybrid) evacuates successfully in ~134s.
    """
    from matplotlib.collections import LineCollection
    from sim.core.simulation import Simulation
    from sim.scenarios.bottleneck import BottleneckScenario

    seed = 46
    n_agents = 100
    n_steps_capture = 6000  # 60s of simulation

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    for ax, cfg, label in zip(axes, ["C1", "C4"], ["C1: SFM only (deadlock)", "C4: Full hybrid (evacuates)"]):
        scenario = BottleneckScenario(n_agents=n_agents, exit_width=0.8)
        sim = Simulation.from_scenario(scenario, cfg, seed=seed)

        positions_log = []
        for _ in range(n_steps_capture):
            sim.step()
            if sim.step_count % 20 == 0:  # capture every 0.2s
                positions_log.append(sim.state.positions.copy())
            if sim.state.n_active == 0:
                break

        # Plot trajectories
        n_frames = len(positions_log)
        for i in range(n_agents):
            xs = [positions_log[t][i, 0] for t in range(n_frames)]
            ys = [positions_log[t][i, 1] for t in range(n_frames)]
            points = np.array([xs, ys]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            colors = np.linspace(0, 1, len(segments))
            lc = LineCollection(segments, cmap="viridis", linewidth=0.4, alpha=0.6)
            lc.set_array(colors)
            ax.add_collection(lc)

        # Draw walls
        for w in sim.world.walls:
            ax.plot([w.start[0], w.end[0]], [w.start[1], w.end[1]], "k-", lw=1.5)

        ax.set_xlim(-0.5, 11)
        ax.set_ylim(-0.5, 10.5)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        if cfg == "C1":
            ax.set_ylabel("y (m)")
        ax.set_title(label, fontsize=10)

    # Shared colorbar
    fig.colorbar(axes[1].collections[0], ax=axes, label="Time (normalised)",
                 fraction=0.025, pad=0.02)
    path = save_figure(fig, "trajectories", output_dir)
    print(f"Fig 3: {path}")


def fig4_density_heatmap(output_dir):
    """Run narrow-exit funnel sim (0.8m exit, 250 agents), time-average density."""
    from sim.core.simulation import Simulation
    from sim.scenarios.funnel import FunnelScenario
    from scipy.ndimage import gaussian_filter

    scenario = FunnelScenario(n_agents=250, exit_width=0.8)
    sim = Simulation.from_scenario(scenario, "D1", seed=42,
                                    param_overrides={"neighbor_radius": 1.5})

    # Warmup to peak congestion (245+ agents still inside, packed at throat)
    for _ in range(800):
        sim.step()

    # Time-average density over 100 frames
    xlim, ylim = (0, 16), (0, 10)
    res = 0.25
    nx = int((xlim[1] - xlim[0]) / res)
    ny = int((ylim[1] - ylim[0]) / res)
    H_sum = np.zeros((nx, ny))

    for _ in range(100):
        sim.step()
        pos = sim.state.positions[sim.state.active]
        H, _, _ = np.histogram2d(
            pos[:, 0], pos[:, 1],
            bins=[nx, ny], range=[list(xlim), list(ylim)],
        )
        H_sum += H

    density = (H_sum / 100).T / (res * res)
    density = gaussian_filter(density, sigma=1.5)

    # Mask density outside funnel walls
    exit_width = 0.8
    half = exit_width / 2.0
    y_bot_exit = 5.0 - half   # 4.6
    y_top_exit = 5.0 + half   # 5.4
    mask = np.ones_like(density, dtype=bool)
    for iy in range(density.shape[0]):
        for ix in range(density.shape[1]):
            x = xlim[0] + (ix + 0.5) * res
            y = ylim[0] + (iy + 0.5) * res
            if x <= 15.0:
                # Bottom wall: y = x * (y_bot_exit / 15)
                y_bot = x * (y_bot_exit / 15.0)
                # Top wall: y = 10 - x * ((10 - y_top_exit) / 15)
                y_top = 10.0 - x * ((10.0 - y_top_exit) / 15.0)
                if y < y_bot or y > y_top:
                    mask[iy, ix] = False
            else:
                # Beyond exit: only allow within exit gap
                if y < y_bot_exit or y > y_top_exit:
                    mask[iy, ix] = False
    density[~mask] = np.nan

    set_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(
        density, origin="lower", cmap="YlOrRd",
        extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
        aspect="auto",
    )
    # Draw narrow funnel walls
    ax.plot([0, 15], [0, y_bot_exit], "k-", lw=1.5)   # bottom
    ax.plot([0, 15], [10, y_top_exit], "k-", lw=1.5)   # top
    ax.plot([0, 0], [0, 10], "k-", lw=1.5)              # left
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    fig.colorbar(im, ax=ax, label="Density (ped/m²)")
    fig.tight_layout()
    path = save_figure(fig, "density_heatmap", output_dir)
    print(f"Fig 4: {path}")


def fig5_evac_vs_width(input_dir, output_dir):
    """Evacuation time vs bottleneck width, lines for C1/C4."""
    set_style()
    fig, ax = plt.subplots(figsize=(5, 4))

    for cfg in ["C1", "C4"]:
        widths, evac_means, evac_lo, evac_hi = [], [], [], []
        for w in [0.8, 1.0, 1.2, 1.8, 2.4, 3.6]:
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
    ax.set_xlim(0.5, 4.0)
    ax.legend()
    fig.tight_layout()
    path = save_figure(fig, "evac_vs_width", output_dir)
    print(f"Fig 5: {path}")


def fig6_scaling(input_dir, output_dir):
    """Log-log scaling plot: C1 and C4."""
    f_c1 = os.path.join(input_dir, "scaling_C1.csv")
    if not os.path.exists(f_c1):
        print("Fig 6: skipped (no scaling_C1.csv)")
        return
    from sim.viz.scaling import plot_scaling
    df_c1 = pd.read_csv(f_c1)
    f_c4 = os.path.join(input_dir, "scaling_C4.csv")
    df_c4 = pd.read_csv(f_c4) if os.path.exists(f_c4) else None
    path = plot_scaling(df_c1, df_c4=df_c4, output_dir=output_dir)
    print(f"Fig 6: {path}")


def fig7_risk_heatmap(output_dir):
    """Compute composite risk from the time-averaged density grid.

    Uses the same simulation snapshot as fig4 (step 800, peak congestion).
    Risk is derived analytically from the density field using the simplified
    composite risk formula: R = (rho / rho_ref) * (1 + rho*sigma_v / P_ref).
    This produces a risk map that visually mirrors the density heatmap but
    on the composite risk scale (normal < 1, elevated 1-2, high 2-3, critical >= 3).
    """
    from sim.core.simulation import Simulation
    from sim.scenarios.funnel import FunnelScenario
    from scipy.ndimage import gaussian_filter

    scenario = FunnelScenario(n_agents=250, exit_width=0.8)
    sim = Simulation.from_scenario(scenario, "D1", seed=42,
                                    param_overrides={"neighbor_radius": 1.5})

    # Warmup to peak congestion
    for _ in range(800):
        sim.step()

    # Time-average density AND speed variance over 100 frames
    xlim, ylim = (0, 16), (0, 10)
    res = 0.25
    nx = int((xlim[1] - xlim[0]) / res)
    ny = int((ylim[1] - ylim[0]) / res)
    H_sum = np.zeros((nx, ny))
    speed_sum = np.zeros((nx, ny))
    speed_sq_sum = np.zeros((nx, ny))
    count_sum = np.zeros((nx, ny))

    for _ in range(100):
        sim.step()
        active = sim.state.active
        pos = sim.state.positions[active]
        vel = sim.state.velocities[active]
        speeds = np.linalg.norm(vel, axis=1)

        H, xedges, yedges = np.histogram2d(
            pos[:, 0], pos[:, 1],
            bins=[nx, ny], range=[list(xlim), list(ylim)],
        )
        H_sum += H

        # Accumulate speed stats per cell
        xi = np.clip(((pos[:, 0] - xlim[0]) / res).astype(int), 0, nx - 1)
        yi = np.clip(((pos[:, 1] - ylim[0]) / res).astype(int), 0, ny - 1)
        for k in range(len(pos)):
            speed_sum[xi[k], yi[k]] += speeds[k]
            speed_sq_sum[xi[k], yi[k]] += speeds[k] ** 2
            count_sum[xi[k], yi[k]] += 1

    density = (H_sum / 100).T / (res * res)
    density = gaussian_filter(density, sigma=1.5)

    # Speed variance per cell
    with np.errstate(divide='ignore', invalid='ignore'):
        mean_speed = np.where(count_sum > 0, speed_sum / count_sum, 0).T
        mean_sq = np.where(count_sum > 0, speed_sq_sum / count_sum, 0).T
        speed_var = np.maximum(0, mean_sq - mean_speed ** 2)
        sigma_v = np.sqrt(gaussian_filter(speed_var, sigma=1.5))

    # Composite risk: R = (rho/rho_ref) * (1 + P/P_ref)
    # where P = rho * sigma_v (crowd pressure)
    rho_ref, P_ref = 6.0, 3.0
    pressure = density * sigma_v
    risk = (density / rho_ref) * (1.0 + pressure / P_ref)

    # Mask outside funnel walls
    exit_width = 0.8
    half = exit_width / 2.0
    y_bot_exit = 5.0 - half
    y_top_exit = 5.0 + half
    for iy in range(risk.shape[0]):
        for ix in range(risk.shape[1]):
            x = xlim[0] + (ix + 0.5) * res
            y = ylim[0] + (iy + 0.5) * res
            if x <= 15.0:
                y_bot = x * (y_bot_exit / 15.0)
                y_top = 10.0 - x * ((10.0 - y_top_exit) / 15.0)
                if y < y_bot or y > y_top:
                    risk[iy, ix] = np.nan
            else:
                if y < y_bot_exit or y > y_top_exit:
                    risk[iy, ix] = np.nan

    set_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(
        risk, origin="lower", cmap="YlOrRd",
        extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
        aspect="auto",
    )
    # Draw narrow funnel walls
    ax.plot([0, 15], [0, y_bot_exit], "k-", lw=1.5)
    ax.plot([0, 15], [10, y_top_exit], "k-", lw=1.5)
    ax.plot([0, 0], [0, 10], "k-", lw=1.5)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    fig.colorbar(im, ax=ax, label="Composite Risk")
    fig.tight_layout()
    path = save_figure(fig, "risk_heatmap", output_dir)
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
    """Ablation table: scenario x config, reporting exits and collisions.

    Shows 'exits/N' and mean collision count per replication to support
    the paper's safety-throughput narrative.
    Bottleneck row uses the w=1.2m width (50 agents) -- the canonical
    bottleneck ablation scenario where evacuations complete normally.
    """
    dfs = []
    # Bidirectional + Crossing from default scenario CSVs
    for scen in ["BidirectionalScenario", "CrossingScenario"]:
        for cfg in ["C1", "C2", "C3", "C4"]:
            f = os.path.join(input_dir, f"{scen}_{cfg}.csv")
            if os.path.exists(f):
                dfs.append(pd.read_csv(f))
    # Bottleneck from canonical w=1.2m width runs (50 agents)
    for cfg in ["C1", "C2", "C3", "C4"]:
        f = os.path.join(input_dir, f"Bottleneck_w1.2_{cfg}.csv")
        if os.path.exists(f):
            dfs.append(pd.read_csv(f))
    if not dfs:
        return
    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[combined["config"].str.startswith("C")]

    # Agent counts per scenario (from current re-run scripts)
    totals = {
        "BottleneckScenario": 50,  # w=1.2m canonical ablation
        "BidirectionalScenario": 200,
        "CrossingScenario": 200,
    }

    scenarios = sorted(combined["scenario"].unique())
    configs = ["C1", "C2", "C3", "C4"]

    lines = [
        r"\begin{tabular}{l" + "c" * len(configs) + "}",
        r"\hline",
        r"\textbf{Scenario} & " + " & ".join([f"\\textbf{{{c}}}" for c in configs]) + r" \\",
        r"\hline",
        r"\multicolumn{5}{l}{\textit{Exits (mean)}} \\",
    ]
    for scen in scenarios:
        total = totals.get(scen, "")
        cells = [scen.replace("Scenario", "")]
        for cfg in configs:
            subset = combined[(combined["scenario"] == scen) & (combined["config"] == cfg)]
            if len(subset) > 0:
                exits = subset["agents_exited"].mean()
                cells.append(f"{exits:.0f}/{total}" if total else f"{exits:.0f}")
            else:
                cells.append("--")
        lines.append(" & ".join(cells) + r" \\")
    lines.append(r"\hline")
    lines.append(r"\multicolumn{5}{l}{\textit{Collisions (mean)}} \\")
    for scen in scenarios:
        cells = [scen.replace("Scenario", "")]
        for cfg in configs:
            subset = combined[(combined["scenario"] == scen) & (combined["config"] == cfg)]
            if len(subset) > 0:
                cells.append(f"{subset['collision_count'].mean():.0f}")
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
    """Crush threshold comparison table (D1-D4).

    Reads FunnelScenario_D*.csv (narrow-funnel) and/or CrushRoomScenario_D*.csv.
    Denominator is inferred from (exits + n_still_in_scene) is not stored, so
    we show raw exit counts against expected agent counts (250 funnel, 300 room).
    """
    thresholds = {"D1": "none", "D2": "5.0", "D3": "5.5", "D4": "7.0"}

    def emit_block(prefix: str, total_agents: int, label: str):
        rows = []
        for d in ["D1", "D2", "D3", "D4"]:
            f = os.path.join(input_dir, f"{prefix}_{d}.csv")
            if os.path.exists(f):
                df = pd.read_csv(f)
                rows.append(
                    f"{d} & {thresholds[d]} & {df['max_density'].mean():.2f} & "
                    f"{df['agents_exited'].mean():.0f}/{total_agents} & "
                    f"{df['collision_count'].mean():.0f} \\\\"
                )
        if rows:
            return [rf"\multicolumn{{5}}{{l}}{{\textit{{{label}}}}} \\"] + rows
        return []

    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\hline",
        r"\textbf{Config} & $\rho_\text{crit}$ & \textbf{Max Density} & \textbf{Exits} & \textbf{Collisions} \\",
        r"\hline",
    ]
    funnel_block = emit_block("FunnelScenario", 250, "Narrow funnel (250 agents)")
    room_block = emit_block("CrushRoomScenario", 300, "Crush room (300 agents)")
    if funnel_block:
        lines.extend(funnel_block)
    if room_block:
        if funnel_block:
            lines.append(r"\hline")
        lines.extend(room_block)
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")

    path = os.path.join(table_dir, "crush.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Table: {path}")


if __name__ == "__main__":
    main()
