"""Fundamental diagram: speed vs density scatter with empirical data."""

import numpy as np
import matplotlib.pyplot as plt

from sim.viz.style import COLORS, LABELS, set_style, save_figure


def weidmann_speed(density: np.ndarray) -> np.ndarray:
    """Weidmann (1993) speed-density relation: v = v0 * (1 - exp(-gamma*(1/rho - 1/rho_max)))."""
    v0 = 1.34
    rho_max = 5.4
    gamma = 1.913
    safe_rho = np.maximum(density, 0.01)
    v = v0 * (1.0 - np.exp(-gamma * (1.0 / safe_rho - 1.0 / rho_max)))
    return np.maximum(v, v0 * 0.05)  # 5% floor matches simulation desired.py


def plot_fundamental_diagram(
    data: dict[str, tuple[np.ndarray, np.ndarray]],
    empirical: tuple[np.ndarray, np.ndarray] | None = None,
    output_dir: str = "figures/",
) -> str:
    """Plot 2x2 fundamental diagram for C1-C4.

    Args:
        data: {config_name: (densities, speeds)} arrays.
        empirical: Optional (density, speed) from real data.
        output_dir: Output directory.

    Returns:
        Path to saved figure.
    """
    set_style()
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), sharex=True, sharey=True)
    configs = ["C1", "C2", "C3", "C4"]
    rho_line = np.linspace(0.1, 6.0, 100)

    for ax, cfg in zip(axes.flat, configs):
        if cfg in data:
            rho, spd = data[cfg]
            ax.scatter(rho, spd, s=3, alpha=0.3, color=COLORS[cfg], label="Simulated")
        if empirical is not None:
            ax.scatter(empirical[0], empirical[1], s=3, alpha=0.3, color="gray", label="Empirical")
        ax.plot(rho_line, weidmann_speed(rho_line), "k--", lw=1, label="Weidmann")
        ax.set_title(LABELS[cfg])
        ax.set_xlim(0, 6)
        ax.set_ylim(0, 2)
        ax.legend(fontsize=7, loc="upper right")

    fig.supxlabel("Density (ped/m²)")
    fig.supylabel("Speed (m/s)")
    fig.tight_layout()
    return save_figure(fig, "fundamental_diagram", output_dir)
