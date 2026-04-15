"""Redesigned Figure 2: sigmoid gate w_o(ρ) + observed density histogram.

Panel A: w_o(ρ) = 1 − σ(ρ; ρ0=4.0, k=2.0), ρ ∈ [0, 8], with transition
         region (0.1 < w_o < 0.9) shaded.
Panel B: agent-timestep density histogram for bottleneck w=1.0 m, C4
         (5 seeds, 55,727 samples). Crossing / bidirectional raw logs
         not archived.

Writes figures/force_magnitude.pdf.
"""

import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)

RHO0 = 4.0
K = 2.0
OUT = "figures/force_magnitude.pdf"


def sigmoid(x, x0, k):
    return 1.0 / (1.0 + np.exp(-k * (x - x0)))


def w_orca(rho):
    return 1.0 - sigmoid(rho, RHO0, K)


def transition_band():
    import math
    delta = math.log(9) / K
    return RHO0 - delta, RHO0 + delta


def load_densities():
    parquets = sorted(glob.glob("results_new/force_logging/force_C4_w1.0_seed*.parquet"))
    return np.concatenate([pd.read_parquet(p)["density"].values for p in parquets])


def panel_a(ax, observed_max):
    rho = np.linspace(0, 8, 400)
    ax.plot(rho, w_orca(rho), "-", color="#1f77b4", lw=1.8, label=r"$w_o(\rho)$")
    lo, hi = transition_band()
    ax.axvspan(lo, hi, alpha=0.18, color="#ffb142",
               label=f"transition ($0.1 < w_o < 0.9$)")
    ax.axvspan(0, observed_max, alpha=0.15, color="#2ca02c",
               label=f"observed ($\\rho \\leq {observed_max:.2f}$)")
    ax.axvline(RHO0, color="black", linestyle="--", lw=0.9)
    ax.text(RHO0 + 0.08, 0.05, r"$\rho_0=4.0$ (Fruin LoS-E)",
            fontsize=7.5, va="bottom", ha="left")
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel(r"density $\rho$ (ped/m$^2$)")
    ax.set_ylabel(r"ORCA weight $w_o(\rho)$")
    ax.set_title("(A) sigmoid gate", loc="left", fontsize=9)
    ax.legend(fontsize=7, loc="center right", frameon=False)


def panel_b(ax, dens, observed_max):
    n = len(dens)
    bins = np.linspace(0, 8, 161)
    ax.hist(dens, bins=bins, density=True, color="#2ca02c", alpha=0.8,
            label=f"bottleneck $w=1.0$ m, C4 ($n=5$, {n:,} samples)")

    lo, hi = transition_band()
    ax.axvspan(lo, hi, alpha=0.18, color="#ffb142",
               label="gate transition")
    ax.axvline(RHO0, color="black", linestyle="--", lw=0.9)

    # Data-gap annotation for crossing and bidirectional
    ylim = ax.get_ylim()
    ax.text(5.0, ylim[1] * 0.75,
            "crossing and bidirectional:\n"
            "per-agent-timestep density\n"
            "logs not archived",
            fontsize=7, color="#555", va="top",
            bbox=dict(facecolor="white", edgecolor="#aaa",
                      boxstyle="round,pad=0.35"))
    ax.set_xlim(0, 8)
    ax.set_xlabel(r"density $\rho$ (ped/m$^2$)")
    ax.set_ylabel("probability density")
    ax.set_title(f"(B) observed density", loc="left", fontsize=9)
    ax.legend(fontsize=7, loc="upper right", frameon=False)


def main():
    dens = load_densities()
    observed_max = float(np.quantile(dens, 0.999))

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.3))
    panel_a(axes[0], observed_max)
    panel_b(axes[1], dens, observed_max)
    fig.tight_layout()
    fig.savefig(OUT)
    plt.close(fig)
    print(f"saved: {OUT}")
    print(f"  observed max ρ (99.9th pctl) = {observed_max:.3f}")
    print(f"  n agent-timesteps = {len(dens):,}")
    print(f"  transition band = [{transition_band()[0]:.2f}, {transition_band()[1]:.2f}]")


if __name__ == "__main__":
    main()
