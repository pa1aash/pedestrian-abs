#!/usr/bin/env python
"""Phase C figures: calibration sanity sweeps."""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)

def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    xs = [float(r["param_value"]) for r in rows]
    ys = [float(r["rmse"]) for r in rows]
    return xs, ys

for name, xlabel, bounds in [("A", "A (N)", (0, 4500)),
                             ("B", "B (m)", (0, 0.35))]:
    xs, ys = load(f"results_new/calibration_sanity_{name}.csv")
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(xs, ys, "o-", color="#2b6cb0", markersize=7, linewidth=1.5)
    ax.axhline(0.0908, color="gray", linestyle="--", linewidth=0.8,
               label="existing fit (0.091)")
    ymin = min(0.08, min(ys) * 0.9)
    ymax = max(ys) * 1.1
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(*bounds)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("FD speed-density RMSE (m/s)")
    ax.set_title(f"Parameter {name} sanity sweep")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out = f"figures/calibration_sanity_{name}.pdf"
    fig.savefig(out)
    print(f"wrote {out}")
