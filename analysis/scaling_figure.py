"""S14: regenerate figures/scaling.pdf from results_new/scaling_C{1,4}.csv.

Per-step wall-time, log-log, C1 solid + C4 dashed.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)


def agg(path):
    df = pd.read_csv(path)
    g = df.groupby("n_agents")["ms_per_step"].agg(["mean", "std"]).reset_index()
    return g


def main():
    c1 = agg("results_new/scaling_C1.csv")
    c4 = agg("results_new/scaling_C4.csv")

    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ax.errorbar(c1["n_agents"], c1["mean"], yerr=c1["std"], fmt="o-",
                color="#1f77b4", label="C1 (SFM only)", capsize=2, lw=1.2)
    ax.errorbar(c4["n_agents"], c4["mean"], yerr=c4["std"], fmt="s--",
                color="#d62728", label="C4 (full hybrid)", capsize=2, lw=1.2)
    ax.axhline(33.0, color="gray", linestyle=":", lw=0.8)
    ax.text(55, 37, "real-time (33 ms/step)", fontsize=7, color="gray")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("agent count")
    ax.set_ylabel("per-step wall-time (ms)")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig("figures/scaling.pdf")
    plt.close(fig)

    # Also compute key numbers for the caption
    def at(g, n):
        row = g[g["n_agents"] == n]
        return float(row["mean"].iloc[0]) if len(row) else np.nan

    print(f"C1: 50 agents -> {at(c1, 50):.1f} ms; 1000 -> {at(c1, 1000):.1f} ms")
    print(f"C4: 50 agents -> {at(c4, 50):.1f} ms; 500 -> {at(c4, 500):.1f} ms")
    print("overhead ratios:")
    for n in [50, 100, 200, 500]:
        c1n = at(c1, n); c4n = at(c4, n)
        if not np.isnan(c4n):
            print(f"  n={n}: {c4n/c1n:.1f}x")


if __name__ == "__main__":
    main()
