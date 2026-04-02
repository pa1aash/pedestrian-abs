#!/usr/bin/env python
"""CLI for generating publication figures from experiment results."""

import argparse
import os
import glob

import pandas as pd
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Generate CrowdTwin figures")
    parser.add_argument("--input", default="results/")
    parser.add_argument("--output", default="figures/")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Collect all CSVs
    csv_files = glob.glob(os.path.join(args.input, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {args.input}")
        return

    all_dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        all_dfs.append(df)
    combined = pd.concat(all_dfs, ignore_index=True)

    # Ablation bars
    if "config" in combined.columns and "scenario" in combined.columns:
        from sim.viz.ablation_bars import plot_ablation_bars
        for metric in ["evacuation_time", "mean_speed", "max_density"]:
            if metric in combined.columns:
                path = plot_ablation_bars(combined, metric=metric, output_dir=args.output)
                print(f"Saved: {path}")

    # Scaling
    scaling_files = [f for f in csv_files if "scaling" in os.path.basename(f)]
    if scaling_files:
        from sim.viz.scaling import plot_scaling
        for f in scaling_files:
            df = pd.read_csv(f)
            path = plot_scaling(df, output_dir=args.output)
            print(f"Saved: {path}")

    # Convergence (if optimizer results exist)
    # (Would need optimizer history saved as JSON — placeholder)

    print(f"Done. Figures in {args.output}")


if __name__ == "__main__":
    main()
