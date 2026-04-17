"""Regenerate all 7 publication PDF figures for paper/main.tex.

Outputs under ``figures/``. Run from the repo root:
    python scripts/regenerate_all_figures.py

Design goals:
  - SciTePress column width 3.3"; publication-quality serif fonts.
  - Single consistent palette; no overlapping labels; legends placed
    outside data regions.
  - Fundamental diagram is a 2x2 per-config panel overlay (the form the
    paper reviewers preferred).
  - Force-magnitude figure is a clean single-panel log-log plot of the
    four force components vs density with the two marker densities
    annotated at the top axis rather than in the plot body.
  - Zonal figure is grouped bars (upstream / throat / downstream) per
    config with a secondary annotation of percent reduction.
  - Sigma sweep has inline CI band and one discreet legend — no
    arrow-style text annotation.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, NullFormatter
from scipy.optimize import curve_fit
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
RESN = REPO / "results_new"
RESA = REPO / "results_analysis"
FIG = REPO / "figures"
FIG.mkdir(exist_ok=True)

# Unified colorblind-safe palette (one colour per config, consistent
# across all figures).
CFG_COLOR = {
    "C1": "#1f77b4",  # blue
    "C2": "#ff7f0e",  # orange
    "C3": "#2ca02c",  # green
    "C4": "#d62728",  # red
}
CFG_MARKER = {"C1": "o", "C2": "s", "C3": "^", "C4": "D"}
ZONE_COLOR = {
    "upstream": "#4C72B0",
    "throat": "#DD8452",
    "downstream": "#55A868",
}
FORCE_COLOR = {
    "mag_des": "#4C72B0",
    "mag_sfm": "#C44E52",
    "mag_ttc": "#55A868",
    "mag_orca": "#DD8452",
}
FORCE_LABEL = {
    "mag_des": r"$|F_\mathrm{des}|$",
    "mag_sfm": r"$|F_\mathrm{SFM}|$",
    "mag_ttc": r"$|F_\mathrm{TTC}|$",
    "mag_orca": r"$|F_\mathrm{ORCA}|$",
}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4,
    "ytick.minor.width": 0.4,
    "lines.linewidth": 1.3,
    "lines.markersize": 4.0,
    "legend.frameon": False,
    "legend.handletextpad": 0.4,
    "legend.columnspacing": 1.0,
})

COL = 3.3           # SciTePress single column (inches)
COL_WIDE = 3.5      # a bit of extra breathing room when needed
TWO_COL = 6.8       # two-column span


# ---------- helpers ----------

def weidmann_curve(rho: np.ndarray, gamma: float = 1.913,
                    rho_max: float = 5.4, v0: float = 1.34) -> np.ndarray:
    safe = np.maximum(rho, 1e-3)
    v = v0 * (1.0 - np.exp(-gamma * (1.0 / safe - 1.0 / rho_max)))
    return np.clip(v, 0.0, v0)


def bin_mean_std(df: pd.DataFrame, bin_edges: np.ndarray):
    centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    m = np.full(len(centres), np.nan)
    s = np.full(len(centres), np.nan)
    for i, (lo, hi) in enumerate(zip(bin_edges[:-1], bin_edges[1:])):
        mask = (df.density >= lo) & (df.density < hi)
        if mask.sum() >= 2:
            m[i] = df.loc[mask, "speed"].mean()
            s[i] = df.loc[mask, "speed"].std()
    return centres, m, s


def wilson_ci(successes: np.ndarray, n: np.ndarray, z: float = 1.96):
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    halfw = (z / denom) * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    lo = np.clip(centre - halfw, 0.0, 1.0)
    hi = np.clip(centre + halfw, 0.0, 1.0)
    return p, np.maximum(p - lo, 0), np.maximum(hi - p, 0)


# ---------- Figure 1: 2x2 Fundamental Diagram ----------

def fig_fd():
    emp = pd.read_csv(RES / "empirical_fd.csv")
    emp = emp[(emp.mean_density >= 0) & (emp.mean_density <= 6)]
    fig, axes = plt.subplots(2, 2, figsize=(COL, 3.4), sharex=True, sharey=True)
    bin_edges = np.linspace(0.0, 5.5, 16)
    rho_line = np.linspace(0.1, 5.5, 300)

    # Compute empirical binned reference line (shared across panels)
    emp_centres, emp_mean, emp_std = bin_mean_std(
        emp.rename(columns={"mean_density": "density",
                            "mean_speed": "speed"}), bin_edges)
    emp_valid = ~np.isnan(emp_mean)

    for ax, cfg in zip(axes.flat, ["C1", "C2", "C3", "C4"]):
        # Empirical cloud: light hexbin-style density background
        ax.scatter(emp.mean_density, emp.mean_speed, s=1.5,
                    color="#BDC3C7", alpha=0.18, edgecolors="none",
                    rasterized=True, zorder=1)
        # Simulation data: line through bin means with shaded std band
        df = pd.read_csv(RES / f"fd_{cfg}.csv")
        centres, mean, std = bin_mean_std(df, bin_edges)
        valid = ~np.isnan(mean)
        c = CFG_COLOR[cfg]
        ax.fill_between(
            centres[valid], (mean - std)[valid], (mean + std)[valid],
            color=c, alpha=0.18, lw=0, zorder=2,
        )
        ax.plot(centres[valid], mean[valid], "-", color=c, lw=1.4,
                zorder=4)
        # Filled markers at bin centres with white outline for pop
        ax.plot(centres[valid], mean[valid], CFG_MARKER[cfg],
                 mfc=c, mec="white", mew=0.8, ms=4.5, ls="", zorder=5)
        # Weidmann reference curve (calibrated)
        ax.plot(rho_line, weidmann_curve(rho_line, gamma=0.833,
                                          rho_max=5.98),
                "--", color="#2C3E50", lw=0.9, alpha=0.85, zorder=3)
        # Empirical mean curve (thin, for direct comparison)
        ax.plot(emp_centres[emp_valid], emp_mean[emp_valid], ":",
                color="#555555", lw=0.7, zorder=3)
        ax.set_title(
            {"C1": "C1  (SFM only)",
             "C2": "C2  (SFM + TTC)",
             "C3": "C3  (SFM + ORCA)",
             "C4": "C4  (full hybrid)"}[cfg],
            fontsize=8.5, color=c, fontweight="bold", pad=3,
        )
        ax.set_xlim(0, 5.5)
        ax.set_ylim(0, 2.1)
        ax.tick_params(axis="both", which="major", length=2.5)
        ax.grid(True, which="major", ls="-", lw=0.25, color="#EAEAEA")
        ax.set_axisbelow(True)

    # Shared legend at top
    handles = [
        Line2D([0], [0], marker="o", mfc="#888", mec="white", mew=0.8,
                ms=4.5, ls="-", color="#888",
                label=r"simulation mean $\pm$ std"),
        Line2D([0], [0], marker="s", mfc="#BDC3C7", mec="none", ms=3,
                ls=":", color="#555555", label="FZJ empirical (n=4776)"),
        Line2D([0], [0], color="#2C3E50", ls="--", lw=1.0,
                label="Weidmann (calibrated)"),
    ]
    fig.legend(handles=handles, loc="upper center",
                bbox_to_anchor=(0.52, 1.06), ncol=3, fontsize=7,
                handletextpad=0.3, columnspacing=0.9)

    fig.supxlabel(r"Density $\rho$ (ped/m$^2$)", fontsize=9, y=-0.01)
    fig.supylabel(r"Speed $v$ (m/s)", fontsize=9, x=-0.01)
    fig.tight_layout(h_pad=0.5, w_pad=0.5)
    fig.savefig(FIG / "fundamental_diagram.pdf")
    plt.close(fig)


# ---------- Figure 2: Force magnitude vs density ----------

def fig_force_magnitude():
    seeds_paths = sorted((RESN / "force_logging").glob(
        "force_C4_w1.0_seed*.parquet"))
    dfs = [pq.read_table(p).to_pandas() for p in seeds_paths]

    # Log-spaced density bins covering the positive range observed.
    rho_all = np.concatenate([d.density.values for d in dfs])
    rho_pos = rho_all[rho_all > 0]
    rho_lo, rho_hi = np.percentile(rho_pos, [1, 99.5])
    bins = np.logspace(np.log10(max(rho_lo, 1e-3)),
                        np.log10(rho_hi), 22)
    centres = np.sqrt(bins[:-1] * bins[1:])

    components = ["mag_des", "mag_sfm", "mag_ttc", "mag_orca"]
    per_seed = {c: [] for c in components}
    for d in dfs:
        idx = np.digitize(d.density.values, bins) - 1
        ok = (idx >= 0) & (idx < len(centres))
        row = {c: np.full(len(centres), np.nan) for c in components}
        for b in range(len(centres)):
            mask = ok & (idx == b)
            if mask.sum() >= 5:
                for c in components:
                    vals = d[c].values[mask]
                    vals = vals[vals > 0]
                    if len(vals) >= 3:
                        row[c][b] = np.median(vals)
        for c in components:
            per_seed[c].append(row[c])

    agg = {c: (np.nanmean(np.vstack(per_seed[c]), axis=0),
               np.nanstd(np.vstack(per_seed[c]), axis=0))
           for c in components}

    fig, ax = plt.subplots(figsize=(COL, 2.6))
    for c in components:
        m, s = agg[c]
        valid = ~np.isnan(m) & (m > 0)
        ax.plot(centres[valid], m[valid], "-", color=FORCE_COLOR[c],
                 label=FORCE_LABEL[c], lw=1.3, zorder=3)
        lo = np.clip(m - s, 1e-6, None)
        ax.fill_between(centres[valid], lo[valid], (m + s)[valid],
                         color=FORCE_COLOR[c], alpha=0.16, lw=0, zorder=2)

    # Mark the SFM/ORCA force crossover and the Fruin LoS-E sigmoid centre
    ax.axvline(0.07, color="#555555", ls=":", lw=0.9, zorder=1)
    ax.axvline(4.0, color="#555555", ls="--", lw=0.9, zorder=1)
    ymin, ymax = ax.get_ylim()
    ax.text(0.07, ymax * 1.02, r"$\rho{\approx}0.07$",
             ha="center", va="bottom", fontsize=7, color="#555555")
    ax.text(4.0, ymax * 1.02, r"$\rho_0{=}4.0$",
             ha="center", va="bottom", fontsize=7, color="#555555")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Local Voronoi density $\rho$ (ped/m$^2$)")
    ax.set_ylabel(r"Force magnitude (N)")
    ax.legend(loc="lower right", ncol=2, fontsize=7.5,
              handletextpad=0.3, columnspacing=0.8)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", ls="-", lw=0.25, color="#DDDDDD")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "force_magnitude.pdf")
    plt.close(fig)


# ---------- Figure 3: Zonal contact-overlaps (grouped bars) ----------

def fig_zonal():
    df = pd.read_csv(RESA / "zonal_collisions.csv")
    df = df[df.width == 1.0]
    stats = df.groupby(["config", "zone"]).collision_count.agg(["mean", "std"])
    configs = ["C1", "C4"]
    zones = ["upstream", "throat", "downstream"]
    means = {z: [stats.loc[(c, z), "mean"] for c in configs] for z in zones}
    stds = {z: [stats.loc[(c, z), "std"] for c in configs] for z in zones}

    fig, ax = plt.subplots(figsize=(COL, 2.4))
    x = np.arange(len(configs))
    width = 0.26
    offsets = {"upstream": -width, "throat": 0.0, "downstream": width}
    for z in zones:
        bars = ax.bar(x + offsets[z], means[z], width,
                       yerr=stds[z], color=ZONE_COLOR[z],
                       edgecolor="white", linewidth=0.6,
                       error_kw=dict(elinewidth=0.7, capsize=2,
                                     ecolor="#333333"),
                       label=z)
        # value labels above bars
        for xi, m, s in zip(x, means[z], stds[z]):
            label = f"{m:.1f}" if m >= 1 else f"{m:.2f}"
            ax.text(xi + offsets[z], m + s + 1.8, label,
                     ha="center", va="bottom", fontsize=7,
                     color="#333333")

    # Reduction annotation
    red = 100 * (1 - stats.loc[("C4", "upstream"), "mean"]
                 / stats.loc[("C1", "upstream"), "mean"])
    ax.text(0.98, 0.98,
             fr"Upstream: C1$\to$C4 $-${red:.0f}%",
             transform=ax.transAxes, ha="right", va="top",
             fontsize=7.5,
             bbox=dict(boxstyle="round,pad=0.3", fc="#F4F4F4",
                       ec="#CCCCCC", lw=0.5))

    ax.set_xticks(x)
    ax.set_xticklabels(configs)
    ax.set_ylabel("Contact-overlaps per run")
    ax.set_ylim(0, max(means["upstream"]) * 1.35)
    ax.legend(loc="upper center", ncol=3, fontsize=7.5,
              bbox_to_anchor=(0.5, -0.18), frameon=False,
              handletextpad=0.3, columnspacing=0.8)
    fig.tight_layout()
    fig.savefig(FIG / "zonal_collisions_w1m.pdf")
    plt.close(fig)


# ---------- Figure 4: Sigma sweep logistic ----------

def fig_sigma_sweep():
    df = pd.read_csv(RESN / "sigma_sweep.csv")
    agg = df.groupby("sigma").completion.agg(["sum", "count"]).reset_index()
    sigmas = agg.sigma.values
    succ = agg["sum"].values
    n = agg["count"].values
    p, yerr_lo, yerr_hi = wilson_ci(succ, n)

    def logistic(s, k, s50):
        return 1.0 / (1.0 + np.exp(-k * (s - s50)))

    popt, _ = curve_fit(logistic, sigmas, p, p0=[80.0, 0.05],
                         bounds=([1, 0.0], [1e3, 0.5]))
    k_fit, _ = popt
    s50 = 0.049          # authoritative value from decision doc
    ci_lo, ci_hi = 0.044, 0.053
    xs = np.linspace(0, 0.22, 400)
    ys = logistic(xs, k_fit, s50)

    fig, ax = plt.subplots(figsize=(COL, 2.6))
    ax.axvspan(ci_lo, ci_hi, color="#F0A35C", alpha=0.25, lw=0,
                label=r"$\sigma_{50}$ 95% CI")
    ax.axhline(13 / 25, ls="--", color="#55A868", lw=0.9,
                label=r"C3 (SFM+ORCA): $13/25$")
    ax.plot(xs, ys, color="#1f77b4", lw=1.4, label="logistic fit")
    ax.axvline(s50, ls=":", color="#C44E52", lw=1.0)
    ax.errorbar(sigmas, p, yerr=[yerr_lo, yerr_hi], fmt="o",
                color="#333333", ecolor="#666666", elinewidth=0.7,
                capsize=2, ms=3.8, mfc="white", mew=0.9,
                label="observed (Wilson 95%)", zorder=5)

    # Label sigma_50 above the plot once (no arrow clutter)
    ax.text(s50, 1.06, r"$\sigma_{50}=0.049$", ha="center",
             va="bottom", fontsize=7.5, color="#C44E52",
             transform=ax.get_xaxis_transform())
    ax.set_xlabel(r"Velocity noise $\sigma$ (m/s)")
    ax.set_ylabel("Completion probability")
    ax.set_xlim(-0.008, 0.215)
    ax.set_ylim(-0.05, 1.08)
    ax.legend(loc="lower right", fontsize=7.5, ncol=1,
              handletextpad=0.4)
    fig.tight_layout()
    fig.savefig(FIG / "sigma_sweep_logistic.pdf")
    plt.close(fig)


# ---------- Figure 5: Evac vs exit width ----------

def fig_evac_vs_width():
    widths = [1.0, 1.2, 1.8, 2.4, 3.6]
    sig = {1.0: "**", 1.2: "**", 1.8: "*"}
    stats = {}
    for cfg in ("C1", "C4"):
        stats[cfg] = {}
        for w in widths:
            d = pd.read_csv(RES / f"Bottleneck_w{w}_{cfg}.csv")
            et = d.evacuation_time.replace([np.inf, -np.inf], np.nan).dropna()
            m = et.mean()
            se = 1.96 * et.std() / math.sqrt(len(et))
            stats[cfg][w] = (m, se)

    fig, ax = plt.subplots(figsize=(COL, 2.4))
    # Use a plotting index so narrow widths separate visually; label with
    # the real width at the tick.
    xs = np.arange(len(widths))
    for cfg, mk in zip(("C1", "C4"), ("o", "D")):
        m = [stats[cfg][w][0] for w in widths]
        e = [stats[cfg][w][1] for w in widths]
        ax.errorbar(xs, m, yerr=e, fmt=f"-{mk}",
                    color=CFG_COLOR[cfg], ecolor=CFG_COLOR[cfg],
                    elinewidth=0.8, capsize=2.5, lw=1.3, ms=4.5,
                    mfc="white", mew=1.0, label=cfg)

    for i, w in enumerate(widths):
        if w in sig:
            y = max(stats["C1"][w][0] + stats["C1"][w][1],
                    stats["C4"][w][0] + stats["C4"][w][1])
            ax.text(i, y + 2.2, sig[w], ha="center", fontsize=10,
                     color="#555555")

    ax.set_xlabel("Exit width $w$ (m)")
    ax.set_ylabel("Evacuation time (s)")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{w}" for w in widths])
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", ls="-", lw=0.25, color="#DDDDDD")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "evac_vs_width.pdf")
    plt.close(fig)


# ---------- Figure 6: Trajectories (keep visual design; tidy) ----------

def fig_trajectories():
    def load(cfg):
        return pq.read_table(
            RESN / "trajectories" / f"Bottleneck_{cfg}_w0.8_seed46.parquet"
        ).to_pandas()

    fig, axes = plt.subplots(1, 2, figsize=(TWO_COL, 3.0), sharey=True)
    for ax, cfg in zip(axes, ("C1", "C4")):
        df = load(cfg)
        t_max = df.t.max()
        steps = sorted(df.t.unique())[::50]
        sub = df[df.t.isin(steps)].copy()
        sub["nt"] = sub.t / t_max
        for aid, agent in sub.groupby("agent_id"):
            agent = agent.sort_values("t")
            pts = np.array([agent.x.values, agent.y.values]).T.reshape(-1, 1, 2)
            segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
            lc = LineCollection(segs, cmap="viridis",
                                 norm=plt.Normalize(0, 1), lw=0.4, alpha=0.7)
            lc.set_array(agent["nt"].values[:-1])
            ax.add_collection(lc)
        # 10x10 room, 0.8 m exit on right wall
        ax.plot([0, 0, 10, 10], [0, 10, 10, 0], color="black", lw=1.0)
        ax.plot([0, 10], [0, 0], color="black", lw=1.0)
        ax.plot([10, 10], [0, 5 - 0.4], color="black", lw=1.2)
        ax.plot([10, 10], [5 + 0.4, 10], color="black", lw=1.2)
        ax.set_xlim(-0.5, 11)
        ax.set_ylim(-0.5, 10.5)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_title(f"{cfg} — seed 46", fontsize=9)
    axes[0].set_ylabel("y (m)")
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(0, 1))
    cbar = fig.colorbar(sm, ax=axes, shrink=0.8, pad=0.02, fraction=0.035)
    cbar.set_label(r"normalised time $t/t_{\max}$", fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    fig.savefig(FIG / "trajectories.pdf")
    plt.close(fig)


# ---------- Figure 7: Scaling ----------

def fig_scaling():
    df1 = pd.read_csv(RESN / "scaling_C1.csv")
    df4 = pd.read_csv(RESN / "scaling_C4.csv")
    g1 = df1.groupby("n_agents").ms_per_step.agg(["mean", "std"]).reset_index()
    g4 = df4.groupby("n_agents").ms_per_step.agg(["mean", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(COL, 2.5))
    ax.errorbar(g1.n_agents, g1["mean"], yerr=g1["std"], fmt="-o",
                color=CFG_COLOR["C1"], ecolor=CFG_COLOR["C1"],
                elinewidth=0.7, capsize=2, ms=4.0, mfc="white", mew=1.0,
                label="C1 (SFM)")
    ax.errorbar(g4.n_agents, g4["mean"], yerr=g4["std"], fmt="-D",
                color=CFG_COLOR["C4"], ecolor=CFG_COLOR["C4"],
                elinewidth=0.7, capsize=2, ms=3.8, mfc="white", mew=1.0,
                label="C4 (full hybrid)")

    # Real-time threshold (33 ms at dt=0.01s)
    ax.axhline(33, ls=":", color="#555555", lw=0.8)
    ax.text(0.97, 0.40, "real-time threshold (33 ms)",
             transform=ax.transAxes, ha="right", va="bottom",
             fontsize=7, color="#555555")
    ax.text(0.97, 0.12, "ORCA overhead: 29\u201336$\\times$",
             transform=ax.transAxes, ha="right", va="bottom",
             fontsize=7.5, color="#333333",
             bbox=dict(boxstyle="round,pad=0.25", fc="#F4F4F4",
                       ec="#CCCCCC", lw=0.5))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Number of agents")
    ax.set_ylabel("ms / step")
    ax.set_xlim(40, 1400)
    ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=(1,)))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=(2, 5)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, which="major", ls="-", lw=0.25, color="#DDDDDD")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "scaling.pdf")
    plt.close(fig)


def main():
    print("Regenerating figures into", FIG)
    fig_fd()
    print("  [1/7] fundamental_diagram.pdf")
    fig_force_magnitude()
    print("  [2/7] force_magnitude.pdf")
    fig_zonal()
    print("  [3/7] zonal_collisions_w1m.pdf")
    fig_sigma_sweep()
    print("  [4/7] sigma_sweep_logistic.pdf")
    fig_evac_vs_width()
    print("  [5/7] evac_vs_width.pdf")
    fig_trajectories()
    print("  [6/7] trajectories.pdf")
    fig_scaling()
    print("  [7/7] scaling.pdf")
    print("Done.")


if __name__ == "__main__":
    main()
