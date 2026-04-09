"""Ablation bar charts: grouped bars with 95% CI error bars."""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sim.viz.style import COLORS, LABELS, set_style, save_figure
from sim.experiments.analysis import Stats


def plot_ablation_bars(
    df: pd.DataFrame,
    metric: str = "evacuation_time",
    output_dir: str = "figures/",
) -> str:
    """Plot grouped bars for scenario x config ablation.

    Args:
        df: DataFrame with columns scenario, config, and metric.
        metric: Column name to plot.
        output_dir: Output directory.

    Returns:
        Path to saved figure.
    """
    set_style()
    scenarios = sorted(df["scenario"].unique())
    configs = ["C1", "C2", "C3", "C4"]  # force all 4 in order

    x = np.arange(len(scenarios))
    width = 0.8 / len(configs)

    fig, ax = plt.subplots(figsize=(8, 4))

    for i, cfg in enumerate(configs):
        means, lowers, uppers = [], [], []
        for scen in scenarios:
            subset = df[(df["scenario"] == scen) & (df["config"] == cfg)][metric]
            if len(subset) > 0:
                m, lo, hi = Stats.confidence_interval(subset.values)
                means.append(m)
                lowers.append(m - lo)
                uppers.append(hi - m)
            else:
                means.append(0)
                lowers.append(0)
                uppers.append(0)

        ax.bar(
            x + i * width - 0.4 + width / 2,
            means,
            width,
            yerr=[lowers, uppers],
            label=LABELS.get(cfg, cfg),
            color=COLORS.get(cfg, f"C{i}"),
            capsize=3,
        )

    # Strip "Scenario" suffix for cleaner labels
    pretty_labels = [s.replace("Scenario", "") for s in scenarios]
    ax.set_xticks(x)
    ax.set_xticklabels(pretty_labels, rotation=0, ha="center")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.legend()
    fig.tight_layout()
    return save_figure(fig, f"ablation_{metric}", output_dir)
