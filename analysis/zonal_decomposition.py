"""R2.1 — Zonal decomposition of collision locations.

Loads the 100 collision parquets in results_new/collisions/ and classifies
each collision by its spatial zone relative to the bottleneck exit at x=10:

  upstream:   x_mid < 8.0         (queue formation)
  throat:     8.0 <= x_mid <= 10.5 (at the exit)
  downstream: x_mid > 10.5         (past the exit)

Produces per-(config, width, seed, zone) aggregates and a stacked-bar figure
at w=1.0m to reveal where the TTC/ORCA effects concentrate.
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

COLL_DIR = Path(_PROJECT_ROOT) / "results_new" / "collisions"
OUTPUT_DIR = Path(_PROJECT_ROOT) / "results_analysis"
FIGURES_DIR = Path(_PROJECT_ROOT) / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

EXIT_X = 10.0
UPSTREAM_MAX = 8.0
THROAT_MAX = 10.5

ZONE_COLORS = {
    "upstream": "#1f77b4",
    "throat": "#d62728",
    "downstream": "#2ca02c",
}


def classify_zone(x_mid: np.ndarray) -> np.ndarray:
    """Return array of zone labels: upstream / throat / downstream."""
    zones = np.where(
        x_mid < UPSTREAM_MAX, "upstream",
        np.where(x_mid <= THROAT_MAX, "throat", "downstream")
    )
    return zones


def parse_filename(name: str) -> tuple[str, float, int]:
    """Extract (config, width, seed) from parquet filename."""
    # Bottleneck_C1_w0.8_seed42.parquet
    stem = name.replace(".parquet", "")
    parts = stem.split("_")
    config = parts[1]
    width = float(parts[2].replace("w", ""))
    seed = int(parts[3].replace("seed", ""))
    return config, width, seed


def process_all() -> pd.DataFrame:
    """Load every collision parquet, classify, and return long-format DF."""
    rows = []
    for path in sorted(COLL_DIR.glob("*.parquet")):
        config, width, seed = parse_filename(path.name)
        df = pd.read_parquet(path)

        if len(df) == 0:
            # No collisions — emit zero-count rows for all zones
            for zone in ["upstream", "throat", "downstream"]:
                rows.append({
                    "config": config, "width": width, "seed": seed,
                    "zone": zone, "collision_count": 0,
                })
            continue

        df["x_mid"] = (df["x_i"] + df["x_j"]) / 2.0
        df["zone"] = classify_zone(df["x_mid"].values)
        counts = df.groupby("zone").size().to_dict()
        for zone in ["upstream", "throat", "downstream"]:
            rows.append({
                "config": config, "width": width, "seed": seed,
                "zone": zone, "collision_count": int(counts.get(zone, 0)),
            })

    return pd.DataFrame(rows)


def summarize(long_df: pd.DataFrame) -> pd.DataFrame:
    """Per (config, width, zone): mean, std, median, quartiles across seeds."""
    grouped = long_df.groupby(["config", "width", "zone"])["collision_count"]
    summary = grouped.agg(
        mean="mean",
        std="std",
        median="median",
        q25=lambda x: np.percentile(x, 25),
        q75=lambda x: np.percentile(x, 75),
        n="count",
    ).reset_index()
    return summary


def plot_stacked_bars(summary: pd.DataFrame, width: float, output_path: Path) -> None:
    """Stacked bar chart: configs on x-axis, zones stacked by colour."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "savefig.bbox": "tight",
        "savefig.dpi": 300,
    })

    sub = summary[summary.width == width].copy()
    configs = ["C1", "C4"]
    zones = ["upstream", "throat", "downstream"]

    fig, ax = plt.subplots(figsize=(5.0, 4.0))

    # Error bars and stacked bars
    bottoms = np.zeros(len(configs))
    for zone in zones:
        means = []
        stds = []
        for cfg in configs:
            row = sub[(sub.config == cfg) & (sub.zone == zone)]
            if len(row) > 0:
                means.append(float(row["mean"].iloc[0]))
                stds.append(float(row["std"].iloc[0]))
            else:
                means.append(0)
                stds.append(0)
        means = np.array(means)
        stds = np.array(stds)
        ax.bar(configs, means, bottom=bottoms,
               color=ZONE_COLORS[zone], edgecolor="black", linewidth=0.6,
               label=zone.capitalize(),
               yerr=stds if zone == "throat" else None,
               capsize=3, error_kw={"ecolor": "black", "lw": 0.8})
        # Annotate each segment with its mean
        for i, m in enumerate(means):
            if m > 0.5:
                ax.text(i, bottoms[i] + m / 2, f"{m:.0f}",
                        ha="center", va="center", fontsize=9,
                        color="white" if zone in ("upstream", "throat") else "black")
        bottoms += means

    ax.set_xlabel("Steering configuration")
    ax.set_ylabel("Mean collisions per run ($n=25$)")
    ax.set_title(f"Collision decomposition by spatial zone, $w={width}$\u0020m")
    ax.legend(loc="upper right", fontsize=9, title="Zone")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, format="pdf", bbox_inches="tight")
    plt.close(fig)


def generate_latex(summary: pd.DataFrame) -> str:
    """LaTeX fragment with per-(config, width, zone) means."""
    lines = [
        r"\begin{tabular}{@{}llrrr@{}}",
        r"\toprule",
        r"\textbf{Config} & \textbf{Width (m)} & \textbf{Upstream} & \textbf{Throat} & \textbf{Downstream} \\",
        r"\midrule",
    ]
    for cfg in ["C1", "C4"]:
        for w in [0.8, 1.0]:
            row_vals = []
            for zone in ["upstream", "throat", "downstream"]:
                r = summary[(summary.config == cfg) & (summary.width == w) & (summary.zone == zone)]
                if len(r) > 0:
                    m = float(r["mean"].iloc[0])
                    s = float(r["std"].iloc[0])
                    row_vals.append(f"${m:.1f} \\pm {s:.1f}$")
                else:
                    row_vals.append("---")
            lines.append(f"{cfg} & {w:.1f} & {row_vals[0]} & {row_vals[1]} & {row_vals[2]} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    return "\n".join(lines)


def classify_case(summary: pd.DataFrame) -> tuple[str, str]:
    """Time-boxed decision: where does the TTC/ORCA effect concentrate?

    Compare C1 vs C4 reduction in each zone at w=1.0m (where both complete).
    Returns (case_letter, rationale).
    """
    s10 = summary[summary.width == 1.0]

    def get_mean(cfg, zone):
        r = s10[(s10.config == cfg) & (s10.zone == zone)]
        return float(r["mean"].iloc[0]) if len(r) > 0 else 0.0

    upstream_c1 = get_mean("C1", "upstream")
    upstream_c4 = get_mean("C4", "upstream")
    throat_c1 = get_mean("C1", "throat")
    throat_c4 = get_mean("C4", "throat")
    downstream_c1 = get_mean("C1", "downstream")
    downstream_c4 = get_mean("C4", "downstream")

    total_c1 = upstream_c1 + throat_c1 + downstream_c1
    total_c4 = upstream_c4 + throat_c4 + downstream_c4

    def reduction(a, b):
        return (a - b) / a * 100 if a > 0 else 0.0

    ups_red = reduction(upstream_c1, upstream_c4)
    thr_red = reduction(throat_c1, throat_c4)
    dns_red = reduction(downstream_c1, downstream_c4)
    total_red = reduction(total_c1, total_c4)

    # Proportion of reduction coming from each zone
    total_abs_reduction = (upstream_c1 - upstream_c4) + (throat_c1 - throat_c4) + (downstream_c1 - downstream_c4)
    if total_abs_reduction > 0:
        thr_share = (throat_c1 - throat_c4) / total_abs_reduction * 100
        ups_share = (upstream_c1 - upstream_c4) / total_abs_reduction * 100
    else:
        thr_share = ups_share = 0.0

    detail = (
        f"at w=1.0: C1 zones upstream/throat/downstream = "
        f"{upstream_c1:.1f}/{throat_c1:.1f}/{downstream_c1:.1f}; "
        f"C4 = {upstream_c4:.1f}/{throat_c4:.1f}/{downstream_c4:.1f}; "
        f"reductions = {ups_red:+.0f}%/{thr_red:+.0f}%/{dns_red:+.0f}%; "
        f"total {total_red:+.0f}%; "
        f"throat share of reduction = {thr_share:.0f}%, upstream share = {ups_share:.0f}%"
    )

    # Case thresholds:
    # A — throat reduction >= 50% of total AND total reduction significant (>= 15%)
    # B — upstream reduction dominates (upstream_share > throat_share, both significant)
    # C — total reduction small (< 10%) OR heterogeneous (no zone dominates)
    if total_red >= 15 and thr_share >= 50 and thr_red >= 20:
        case = "A"
        rationale = (
            f"TTC effect concentrates in the throat zone ({thr_share:.0f}% of the "
            f"{total_red:.0f}% total reduction at w=1.0\u0020m, throat-specific reduction "
            f"{thr_red:.0f}%): original collision claim intact."
        )
    elif total_red >= 15 and ups_share > thr_share and ups_red >= 20:
        case = "B"
        rationale = (
            f"TTC effect concentrates upstream ({ups_share:.0f}% of the "
            f"{total_red:.0f}% total reduction at w=1.0\u0020m, upstream-specific reduction "
            f"{ups_red:.0f}%; throat share only {thr_share:.0f}%): reframe as "
            f"queue-formation collision reduction, not throat collision reduction."
        )
    elif total_red < 10:
        case = "C"
        rationale = (
            f"Total reduction is only {total_red:.0f}% at w=1.0\u0020m and no zone "
            f"shows a clean TTC effect: drop the throat-specific collision claim; "
            f"paper should rely on the deadlock and crossing results instead."
        )
    else:
        # Mixed / marginal — closer to Case C but not null
        case = "C"
        rationale = (
            f"TTC effect is diffuse across zones ({total_red:.0f}% total reduction, "
            f"upstream share {ups_share:.0f}%, throat share {thr_share:.0f}%, no "
            f"zone crosses the 50% threshold): cannot cleanly claim throat-specific "
            f"collision reduction; reframe or drop."
        )

    return case, rationale, detail


def main():
    print("R2.1 Zonal collision decomposition", flush=True)

    # 1. Process all 100 collision parquets
    long_df = process_all()
    print(f"  Processed {long_df[['config','width','seed']].drop_duplicates().shape[0]} runs, "
          f"{long_df.collision_count.sum()} total collisions", flush=True)

    long_path = OUTPUT_DIR / "zonal_collisions.csv"
    long_df.to_csv(long_path, index=False)
    print(f"  -> {long_path} ({len(long_df)} rows)", flush=True)

    # 2. Summary stats
    summary = summarize(long_df)
    sum_path = OUTPUT_DIR / "zonal_collisions_summary.csv"
    summary.to_csv(sum_path, index=False)
    print(f"  -> {sum_path} ({len(summary)} rows)", flush=True)

    # 3. Stacked bar chart at w=1.0
    fig_path = FIGURES_DIR / "zonal_collisions_w1m.pdf"
    plot_stacked_bars(summary, width=1.0, output_path=fig_path)
    print(f"  -> {fig_path}", flush=True)

    # 4. LaTeX table fragment
    tex_path = OUTPUT_DIR / "zonal_collisions_table.tex"
    with open(tex_path, "w") as f:
        f.write(generate_latex(summary))
    print(f"  -> {tex_path}", flush=True)

    # 5. Decision
    case, rationale, detail = classify_case(summary)
    print(f"\n  Detail: {detail}", flush=True)
    print(f"\n  Case: {case}", flush=True)
    print(f"  Rationale: {rationale}", flush=True)

    return long_df, summary, case, rationale


if __name__ == "__main__":
    main()
