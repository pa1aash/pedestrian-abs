#!/usr/bin/env python
"""Extract empirical fundamental diagram from FZJ data."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sim.data.loader import load_fzj_all, weidmann_speed
from sim.data.fundamental_diagram import compute_empirical_fd


def main():
    data_dir = "data/fzj/unidirectional/"
    df = load_fzj_all(data_dir)  # auto-reads fps from file headers

    if df.empty:
        print(f"No FZJ data in {data_dir}.")
        print("Download from https://ped.fz-juelich.de/database")
        sys.exit(1)

    print(f"Loaded {len(df)} rows, {df['ped_id'].nunique()} pedestrians")
    print(f"Speed: mean={df['speed'].mean():.2f}, std={df['speed'].std():.2f}")

    # Measurement area (adjust per experiment geometry)
    # FZJ corridor: x ~[-15, 9], y ~[0, 3.6]. Measure central section.
    fd = compute_empirical_fd(df, measurement_area=(-4.0, 0.0, 4.0, 3.6))

    os.makedirs("results", exist_ok=True)
    fd.to_csv("results/empirical_fd.csv", index=False)
    print(f"FD: {len(fd)} frames, density [{fd['mean_density'].min():.2f}, {fd['mean_density'].max():.2f}]")

    # Plot
    os.makedirs("figures", exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.scatter(fd["mean_density"], fd["mean_speed"], s=2, alpha=0.3, label="FZJ empirical")
    rho = np.linspace(0.1, 5.0, 100)
    ax.plot(rho, weidmann_speed(rho), "r--", label="Weidmann (1993)")
    ax.set_xlabel("Density (ped/m²)")
    ax.set_ylabel("Speed (m/s)")
    ax.legend()
    ax.set_title("Empirical Fundamental Diagram")
    fig.savefig("figures/empirical_fd.pdf", bbox_inches="tight")
    plt.close()
    print("Saved results/empirical_fd.csv and figures/empirical_fd.pdf")


if __name__ == "__main__":
    main()
