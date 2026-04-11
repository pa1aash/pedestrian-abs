"""Scaling plot: log-log agents vs ms/step."""

import matplotlib.pyplot as plt
import pandas as pd

from sim.viz.style import set_style, save_figure


def plot_scaling(
    df: pd.DataFrame,
    df_c4: pd.DataFrame | None = None,
    output_dir: str = "figures/",
) -> str:
    """Plot log-log scaling of agent count vs ms/step for C1 and optionally C4.

    Args:
        df: DataFrame with n_agents and ms_per_step columns (C1).
        df_c4: Optional DataFrame for C4.
        output_dir: Output directory.

    Returns:
        Path to saved figure.
    """
    set_style()
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.loglog(df["n_agents"], df["ms_per_step"], "o-", color="#1b9e77",
              lw=1.5, label="C1 (SFM only)")
    if df_c4 is not None:
        ax.loglog(df_c4["n_agents"], df_c4["ms_per_step"], "s--", color="#d95f02",
                  lw=1.5, label="C4 (full hybrid)")
        ax.legend(fontsize=9)
    ax.set_xlabel("Number of agents")
    ax.set_ylabel("ms / step")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    return save_figure(fig, "scaling", output_dir)
