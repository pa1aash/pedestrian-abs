"""R2.4 — Oracle baseline: per-scenario best single-paradigm vs C4.

For each scenario, the oracle picks the best-performing single paradigm
(C1/C2/C3) on the metric that matters. C4 is then compared against this
oracle using paired Wilcoxon signed-rank (seeds match).
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from analysis.inventory import RESULTS_DIR

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "results_analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CONFIGS_SINGLE = ["C1", "C2", "C3"]


def _load_cfg(pattern_template, configs=None):
    """Load CSVs for given configs into a dict {config: DataFrame}."""
    if configs is None:
        configs = CONFIGS_SINGLE + ["C4"]
    out = {}
    for cfg in configs:
        path = os.path.join(RESULTS_DIR, pattern_template.format(cfg=cfg))
        if os.path.exists(path):
            out[cfg] = pd.read_csv(path)
    return out


def bottleneck_normal():
    """Oracle = min median evac_time across C1/C2/C3 at each width."""
    rows = []
    for w in [1.0, 1.2, 1.8, 2.4, 3.6]:
        data = _load_cfg(f"Bottleneck_w{w}_{{cfg}}.csv")
        if "C4" not in data:
            continue

        # Find oracle: min median evac_time among single paradigms
        best_cfg = None
        best_median = np.inf
        for cfg in CONFIGS_SINGLE:
            if cfg in data:
                med = data[cfg]["evacuation_time"].median()
                if med < best_median:
                    best_median = med
                    best_cfg = cfg

        c4 = data["C4"]["evacuation_time"].values
        oracle_vals = data[best_cfg]["evacuation_time"].values

        # Paired Wilcoxon (seeds match: both use 42-66)
        stat, p = scipy_stats.wilcoxon(c4, oracle_vals)
        gap_abs = np.median(c4) - best_median
        gap_rel = gap_abs / best_median * 100

        rows.append({
            "scenario": f"bottleneck_w{w}",
            "metric": "evacuation_time",
            "oracle_config": best_cfg,
            "oracle_median": best_median,
            "c4_median": np.median(c4),
            "gap_abs": gap_abs,
            "gap_rel_pct": gap_rel,
            "wilcoxon_stat": stat,
            "wilcoxon_p": p,
            "n": len(c4),
        })
    return rows


def bottleneck_deadlock():
    """Oracle = max completion rate across C1/C2/C3 at w=0.8."""
    data = _load_cfg("Bottleneck_w0.8_600s_{cfg}.csv")
    if "C4" not in data:
        return []

    best_cfg = None
    best_rate = -1
    for cfg in CONFIGS_SINGLE:
        if cfg in data:
            rate = (data[cfg]["evacuation_time"] != np.inf).mean()
            if rate > best_rate:
                best_rate = rate
                best_cfg = cfg

    c4_rate = (data["C4"]["evacuation_time"] != np.inf).mean()
    # Fisher's exact for rate comparison
    n = len(data["C4"])
    c4_succ = int(c4_rate * n)
    oracle_succ = int(best_rate * n)
    _, p = scipy_stats.fisher_exact([[oracle_succ, n - oracle_succ],
                                      [c4_succ, n - c4_succ]])
    return [{
        "scenario": "bottleneck_deadlock",
        "metric": "completion_rate",
        "oracle_config": best_cfg,
        "oracle_median": best_rate,
        "c4_median": c4_rate,
        "gap_abs": c4_rate - best_rate,
        "gap_rel_pct": (c4_rate - best_rate) / max(best_rate, 0.01) * 100,
        "wilcoxon_stat": np.nan,
        "wilcoxon_p": p,
        "n": n,
    }]


def scenario_throughput(scenario_name, file_template):
    """Oracle = max mean agents_exited across C1/C2/C3."""
    data = _load_cfg(file_template)
    if "C4" not in data:
        return []

    best_cfg = None
    best_mean = -1
    for cfg in CONFIGS_SINGLE:
        if cfg in data:
            m = data[cfg]["agents_exited"].mean()
            if m > best_mean:
                best_mean = m
                best_cfg = cfg

    c4 = data["C4"]["agents_exited"].values
    oracle_vals = data[best_cfg]["agents_exited"].values

    stat, p = scipy_stats.wilcoxon(c4, oracle_vals)
    gap_abs = np.mean(c4) - best_mean
    gap_rel = gap_abs / max(best_mean, 0.01) * 100

    return [{
        "scenario": scenario_name,
        "metric": "agents_exited",
        "oracle_config": best_cfg,
        "oracle_median": best_mean,
        "c4_median": np.mean(c4),
        "gap_abs": gap_abs,
        "gap_rel_pct": gap_rel,
        "wilcoxon_stat": stat,
        "wilcoxon_p": p,
        "n": len(c4),
    }]


def generate_markdown(df):
    """Generate results_analysis/oracle_baseline.md."""
    lines = ["# R2.4 Oracle Baseline\n"]
    lines.append("Per-scenario best single paradigm (C1/C2/C3) vs C4 (full blend).\n")
    lines.append("| Scenario | Metric | Oracle (best single) | Oracle value | C4 value | Gap | Wilcoxon p |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, r in df.iterrows():
        gap_str = f"{r.gap_rel_pct:+.1f}%"
        p_str = f"{r.wilcoxon_p:.4f}" if not np.isnan(r.wilcoxon_p) else "Fisher"
        lines.append(f"| {r.scenario} | {r.metric} | {r.oracle_config} | "
                      f"{r.oracle_median:.2f} | {r.c4_median:.2f} | {gap_str} | {p_str} |")

    lines.append("\n## Drop-in paragraph for Section 5\n")
    lines.append("To quantify the benefit of the full blend over naive paradigm selection, "
                  "we define an oracle baseline as the per-scenario best single paradigm "
                  "(C1, C2, or C3) on the primary metric. ")

    # Summarise
    wins = (df.gap_rel_pct > 0).sum()
    ties = (df.gap_rel_pct.abs() < 1.0).sum()
    losses = (df.gap_rel_pct < -1.0).sum()
    lines.append(f"Across {len(df)} scenario-metric pairs, C4 improves over the oracle "
                  f"in {wins} cases, matches within 1% in {ties}, and underperforms in {losses}. ")

    best_gap = df.loc[df.gap_rel_pct.abs().idxmax()]
    lines.append(f"The largest gap is {best_gap.gap_rel_pct:+.1f}% on {best_gap.scenario} "
                  f"({best_gap.metric}), where the oracle is {best_gap.oracle_config}.")

    return "\n".join(lines)


def main():
    print("R2.4 Oracle Baseline", flush=True)
    all_rows = []

    all_rows.extend(bottleneck_normal())
    all_rows.extend(bottleneck_deadlock())
    all_rows.extend(scenario_throughput("bidirectional", "BidirectionalScenario_{cfg}.csv"))
    all_rows.extend(scenario_throughput("crossing", "CrossingScenario_{cfg}.csv"))

    df = pd.DataFrame(all_rows)

    md_path = os.path.join(OUTPUT_DIR, "oracle_baseline.md")
    with open(md_path, "w") as f:
        f.write(generate_markdown(df))
    print(f"  -> {md_path} ({len(df)} rows)")
    print("Done.", flush=True)
    return df


if __name__ == "__main__":
    main()
