"""Optimizer convergence plot: evaluations vs objective."""

import matplotlib.pyplot as plt
import numpy as np

from sim.viz.style import set_style, save_figure


def plot_convergence(
    history: list[dict],
    output_dir: str = "figures/",
) -> str:
    """Plot optimizer convergence curve.

    Args:
        history: List of {params, cost} dicts from optimizer.
        output_dir: Output directory.

    Returns:
        Path to saved figure.
    """
    set_style()
    costs = [h["cost"] for h in history]
    best_so_far = np.minimum.accumulate(costs)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(range(1, len(costs) + 1), costs, "o", ms=3, alpha=0.4, color="gray", label="Evaluations")
    ax.plot(range(1, len(best_so_far) + 1), best_so_far, "-", color="#e7298a", lw=1.5, label="Best so far")
    ax.set_xlabel("Evaluation")
    ax.set_ylabel("Cost (evacuation time)")
    ax.legend()
    fig.tight_layout()
    return save_figure(fig, "convergence", output_dir)
