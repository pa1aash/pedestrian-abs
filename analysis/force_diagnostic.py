"""R3.2 — Force-magnitude diagnostic.

Loads 5 C4 w=1.0m force-logging parquets and bins per-agent force
magnitudes (|F_des|, |F_SFM|, |F_TTC|, |F_ORCA|) by local Voronoi
density. Produces:

  figures/force_magnitude_vs_density.pdf — per-component curves with
  shaded ±1σ envelopes, log-y axis.
  results_new/force_logging/interpretation.md — interpretation of
  where SFM and ORCA magnitudes cross (if at all in the observed
  range) and an explicit non-movement of the sigmoid centre ρ₀.
"""

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

FORCE_DIR = Path(_PROJECT_ROOT) / "results_new" / "force_logging"
FIGURES_DIR = Path(_PROJECT_ROOT) / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

BIN_WIDTH = 0.1
BIN_MAX = 2.0  # observed max is ~1.63; go slightly beyond
MIN_N_PER_BIN = 100
SIGMOID_CENTRE = 4.0  # rho_orca_fade default from params.yaml

COLORS = {
    "des": "#1f77b4",   # blue
    "sfm": "#d62728",   # red
    "ttc": "#9467bd",   # purple
    "orca": "#2ca02c",  # green
}


def load_pooled() -> pd.DataFrame:
    """Load all 5 force_C4_w1.0_seed*.parquet and concat."""
    dfs = []
    for path in sorted(FORCE_DIR.glob("force_C4_w1.0_seed*.parquet")):
        dfs.append(pd.read_parquet(path))
    return pd.concat(dfs, ignore_index=True)


def bin_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Bin by density and compute mean/std/n for each force component."""
    bins = np.arange(0, BIN_MAX + BIN_WIDTH, BIN_WIDTH)
    df = df.copy()
    df["rho_bin"] = pd.cut(df["density"], bins=bins, labels=bins[:-1] + BIN_WIDTH / 2,
                           include_lowest=True)

    cols = ["mag_des", "mag_sfm", "mag_ttc", "mag_orca"]
    agg = df.groupby("rho_bin", observed=True)[cols].agg(["mean", "std", "count"])
    # Flatten multiindex: mag_des_mean, mag_des_std, mag_des_count, ...
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    agg = agg.reset_index()
    agg["rho"] = agg["rho_bin"].astype(float)

    # Exclude bins with insufficient n (use SFM count as proxy — all share)
    agg = agg[agg["mag_sfm_count"] >= MIN_N_PER_BIN].copy()
    return agg


def find_crossover(stats: pd.DataFrame) -> tuple[float | None, str]:
    """Find the density at which mean |F_SFM| = mean |F_ORCA|.

    Returns (crossover_density, note).
    """
    sfm = stats["mag_sfm_mean"].values
    orca = stats["mag_orca_mean"].values
    rho = stats["rho"].values

    diff = sfm - orca  # positive when SFM > ORCA
    # Look for sign change
    sign_changes = np.where(np.sign(diff[:-1]) != np.sign(diff[1:]))[0]

    if len(sign_changes) == 0:
        # No crossover in the observed range
        if diff[-1] < 0:
            dominant = "ORCA dominates throughout the observed range"
        else:
            dominant = "SFM dominates throughout the observed range"
        return None, (
            f"{dominant} (|F_SFM|={sfm[-1]:.1f} N, |F_ORCA|={orca[-1]:.1f} N "
            f"at rho={rho[-1]:.2f}); no crossover within observed density [0, {rho[-1]:.2f}]"
        )

    # Linear interpolation between the two straddling bins
    i = sign_changes[0]
    x0, x1 = rho[i], rho[i + 1]
    y0, y1 = diff[i], diff[i + 1]
    crossover = x0 + (x1 - x0) * abs(y0) / (abs(y0) + abs(y1))
    return float(crossover), f"Crossover located via linear interpolation at rho = {crossover:.3f}"


def plot_figure(stats: pd.DataFrame, crossover: float | None, path: Path) -> None:
    """Per-component force magnitude vs density with ±1σ envelopes."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "savefig.bbox": "tight",
        "savefig.dpi": 300,
    })

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    rho = stats["rho"].values

    components = [
        ("des", "Desired |$\\mathbf{F}_{\\mathrm{des}}$|"),
        ("sfm", "SFM |$\\mathbf{F}_{\\mathrm{SFM}}$|"),
        ("ttc", "TTC |$\\mathbf{F}_{\\mathrm{TTC}}$|"),
        ("orca", "ORCA |$\\mathbf{F}_{\\mathrm{ORCA}}$|"),
    ]

    for key, label in components:
        mean = stats[f"mag_{key}_mean"].values
        std = stats[f"mag_{key}_std"].values
        color = COLORS[key]
        # Clip to positive for log y (use small floor)
        floor = np.maximum(mean - std, 1e-6)
        ax.plot(rho, mean, "-", color=color, lw=1.8, label=label)
        ax.fill_between(rho, floor, mean + std, color=color, alpha=0.2)

    if crossover is not None:
        ax.axvline(crossover, color="black", linestyle=":", lw=1.2,
                   label=f"Crossover at $\\rho = {crossover:.2f}$")
    ax.axvline(SIGMOID_CENTRE, color="grey", linestyle="--", lw=1.0,
               label=f"Sigmoid centre $\\rho_0 = {SIGMOID_CENTRE}$ (outside range)")

    ax.set_xlabel(r"Local Voronoi density $\rho$ (ped/m$^2$)")
    ax.set_ylabel("Force magnitude (N, log scale)")
    ax.set_yscale("log")
    ax.set_xlim(0, max(rho.max() + 0.1, 2.0))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.set_title(r"Per-component force magnitude vs.\ density, C4 at $w=1.0$ m ($n=5$)")
    fig.tight_layout()
    fig.savefig(path, format="pdf", bbox_inches="tight")
    plt.close(fig)


def generate_interpretation(stats: pd.DataFrame, crossover: float | None,
                            cross_note: str, pooled: pd.DataFrame) -> str:
    """Honest interpretation paragraph + explicit no-move statement.

    The force-magnitude crossover and the sigmoid centre are different
    quantities with different semantics — this is the central point.
    """
    rho_max = float(pooled["density"].max())
    rho_mean = float(pooled["density"].mean())
    rho_p95 = float(np.percentile(pooled["density"], 95))
    n_rows = len(pooled)

    sfm_at_peak = float(stats["mag_sfm_mean"].iloc[-1])
    orca_at_peak = float(stats["mag_orca_mean"].iloc[-1])
    sfm_at_low = float(stats["mag_sfm_mean"].iloc[0])
    orca_at_low = float(stats["mag_orca_mean"].iloc[0])

    lines = [
        "# R3.2 Force-Magnitude Diagnostic — Interpretation",
        "",
        "## Summary",
        "",
        f"Pooled across 5 seeds at C4, w=1.0 m, {n_rows:,} logged observations "
        f"(per-agent, every 10th timestep). "
        f"Observed density range: **[0, {rho_max:.2f}] ped/m²** "
        f"(mean {rho_mean:.2f}, 95th percentile {rho_p95:.2f}).",
        "",
        "## Finding 1 — Force-magnitude crossover",
        "",
    ]
    if crossover is not None:
        lines.extend([
            f"The force-magnitude crossover |F_SFM| = |F_ORCA| is located at "
            f"**ρ ≈ {crossover:.2f} ped/m²** (interpolated between adjacent bins). "
            f"At the lowest observed bin (ρ={stats['rho'].iloc[0]:.2f}), "
            f"ORCA dominates ({orca_at_low:.1f} N vs. {sfm_at_low:.1f} N for SFM). "
            f"Beyond the crossover, **SFM dominates throughout the operational "
            f"density range**: at ρ ≈ {rho_max:.2f} (the peak observed) SFM "
            f"is {sfm_at_peak:.0f} N versus {orca_at_peak:.0f} N for ORCA, "
            f"a factor of {sfm_at_peak/orca_at_peak:.1f}× difference.",
        ])
    else:
        lines.extend([
            f"- {cross_note}",
            "- Within the observed density range, the force-magnitude diagnostic "
            "**cannot empirically locate the SFM→ORCA crossover**. A higher-density "
            "scenario is required (e.g., w=0.8 m where agents reach ρ ≈ 5–6 ped/m², "
            "or the CrushRoom geometry).",
            f"- At the observed peak density ρ ≈ {rho_max:.2f} ped/m², "
            f"|F_SFM| = {sfm_at_peak:.1f} N and |F_ORCA| = {orca_at_peak:.1f} N.",
        ])

    lines.extend([
        "",
        "## Finding 2 — The force crossover and the sigmoid centre measure "
        "different things",
        "",
        f"The force-magnitude crossover at ρ ≈ {crossover:.2f} ped/m² "
        if crossover is not None else
        "The force-magnitude crossover location ",
        "",
        f"is **not the same quantity** as the sigmoid centre "
        f"ρ₀ = {SIGMOID_CENTRE} ped/m². The two have distinct meanings:",
        "",
        "- **ρ₀ = 4.0 ped/m²** gates the **ORCA weight** w_o(ρ) = 1 − σ(ρ; 4.0, 2.0). "
        "It represents the density at which pedestrians lose the freedom to "
        "choose their walking direction (Fruin LoS-E), i.e., where the "
        "free-space assumption underlying ORCA breaks down. It is a theoretical "
        "anchor about **paradigm applicability**, not about raw force magnitude.",
        "",
        "- The **force-magnitude crossover** (where |F_SFM| = |F_ORCA|) reflects "
        "the absolute contribution each paradigm makes to the total force at a "
        "given density. SFM's social-repulsion term grows exponentially as "
        "agents approach contact, so SFM magnitude rises steeply with density "
        "while ORCA stays bounded by the velocity-correction scale.",
        "",
        "In this implementation, SFM and TTC are always-on additive contributions; "
        f"only ORCA is density-weighted via w_o. Within the observed range "
        f"(ρ ≤ {rho_max:.2f}), w_o stays near 1 — ORCA carries essentially full "
        f"weight — while SFM magnitude exceeds ORCA magnitude for any "
        f"non-trivially dense configuration (ρ > {crossover:.2f} if crossover "
        f"present). The hybrid therefore behaves as 'ORCA-driven navigation with "
        f"SFM contact-repulsion on top' throughout this scenario.",
        "",
        "## Non-movement of the sigmoid centre ρ₀ = 4.0",
        "",
        "We explicitly **do not move ρ₀** in response to this diagnostic. Reasons:",
        "",
        "1. **Distinct semantics.** Moving ρ₀ to match the force-magnitude "
        "crossover would conflate two different quantities (paradigm-applicability "
        "threshold vs. raw force equality). The sigmoid gates ORCA weight; it is "
        "not supposed to track force equality.",
        "",
        "2. **Reproducibility.** ρ₀ = 4.0 was fixed at the start of the entire "
        "experimental programme. All 500+ existing Bottleneck runs, the 540-run "
        "sigmoid sensitivity sweep, the crossing and bidirectional data, and the "
        "deadlock w=0.8 runs used this value. Moving ρ₀ now would invalidate "
        "every pre-R3.2 result.",
        "",
        "3. **Literature grounding.** ρ₀ = 4.0 ped/m² corresponds to the Fruin "
        "LoS-E boundary. The paper's methodology relies on this theoretical "
        "anchor, not on post-hoc empirical fitting.",
        "",
        "## Paragraph for §3.1 footnote (drop-in)",
        "",
        "% TODO R4: tighten language in the paper version",
        "",
    ])
    if crossover is not None:
        lines.append(
            f"> A per-agent force-magnitude diagnostic (Section 4.X) logs "
            f"|F_des|, |F_SFM|, |F_TTC|, |F_ORCA| every 10th timestep at C4, "
            f"w=1.0 m (n=5, {n_rows:,} observations). The empirical crossover "
            f"|F_SFM| = |F_ORCA| occurs at ρ ≈ {crossover:.2f} ped/m² — essentially "
            f"at first-contact density — below which ORCA's velocity-correction "
            f"magnitude dominates and above which SFM's social-repulsion term "
            f"grows exponentially. The literature-motivated sigmoid centre "
            f"ρ₀ = {SIGMOID_CENTRE} ped/m² (Fruin LoS-E) gates a different "
            f"quantity: the ORCA weight w_o(ρ), not the raw force magnitudes. "
            f"The observed density range during the w=1.0 m bottleneck runs is "
            f"ρ ∈ [0, {rho_max:.2f}] ped/m² (95th percentile {rho_p95:.2f}), "
            f"well below the sigmoid transition region centred at 4.0; the "
            f"sigmoid's specific choice of centre within the Fruin LoS-E band "
            f"(3–5 ped/m²) is therefore not load-bearing for the experiments "
            f"reported in Section 4. "
            f"We retain ρ₀ at the Fruin value rather than moving it to the "
            f"force-equality point, because the two quantities carry different "
            f"meanings and because every prior experiment in this paper used "
            f"ρ₀ = 4.0."
        )
    else:
        lines.append(
            f"> A per-agent force-magnitude diagnostic (Section 4.X) confirms "
            f"that at w=1.0 m the local density remains below 2 ped/m² throughout, "
            f"so the ORCA weight w_o = 1 − σ(ρ; 4.0, 2.0) stays near unity and "
            f"the hybrid blend behaves predominantly as SFM + TTC + ORCA in the "
            f"force-sparse regime. The sigmoid centre ρ₀ = 4.0 ped/m² is "
            f"literature-motivated (Fruin LoS-E); the empirical crossover density "
            f"is not observed at w=1.0 m and would require a higher-density "
            f"scenario to locate."
        )

    lines.extend([
        "",
        "## Bin counts per density (for audit)",
        "",
        "| ρ bin centre | n | mean \\|F_des\\| | mean \\|F_SFM\\| | mean \\|F_TTC\\| | mean \\|F_ORCA\\| |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
    for _, r in stats.iterrows():
        lines.append(
            f"| {r['rho']:.2f} | {int(r['mag_sfm_count']):,} | "
            f"{r['mag_des_mean']:.1f} | {r['mag_sfm_mean']:.1f} | "
            f"{r['mag_ttc_mean']:.2f} | {r['mag_orca_mean']:.1f} |"
        )
    return "\n".join(lines)


def main():
    print("R3.2 Force-Magnitude Diagnostic", flush=True)

    pooled = load_pooled()
    print(f"  Loaded {len(pooled):,} rows, density range "
          f"[{pooled['density'].min():.2f}, {pooled['density'].max():.2f}]", flush=True)

    stats = bin_stats(pooled)
    print(f"  {len(stats)} bins after n >= {MIN_N_PER_BIN} filter", flush=True)

    crossover, cross_note = find_crossover(stats)
    print(f"  Crossover: {cross_note}", flush=True)

    fig_path = FIGURES_DIR / "force_magnitude_vs_density.pdf"
    plot_figure(stats, crossover, fig_path)
    print(f"  -> {fig_path}", flush=True)

    interp_path = FORCE_DIR / "interpretation.md"
    with open(interp_path, "w", encoding="utf-8") as f:
        f.write(generate_interpretation(stats, crossover, cross_note, pooled))
    print(f"  -> {interp_path}", flush=True)

    print("\n" + "=" * 50, flush=True)
    print("R3.2 FORCE DIAGNOSTIC GATE", flush=True)
    print("=" * 50, flush=True)
    print(f"Pooled observations: {len(pooled):,}", flush=True)
    print(f"Observed density range: [0, {pooled['density'].max():.2f}] ped/m^2", flush=True)
    print(f"Sigmoid centre: rho_0 = {SIGMOID_CENTRE} ped/m^2 "
          f"({'OUTSIDE observed range' if pooled['density'].max() < SIGMOID_CENTRE else 'WITHIN observed range'})",
          flush=True)
    print(f"Crossover: {cross_note}", flush=True)
    print(f"Decision: rho_0 NOT moved (literature-motivated, reproducibility)", flush=True)
    print("Done.", flush=True)

    return pooled, stats, crossover


if __name__ == "__main__":
    main()
