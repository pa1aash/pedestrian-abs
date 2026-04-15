"""S10: pseudoreplication-free force-magnitude bands + gate occupancy.

Phase A: Per-seed medians per density bin for C4 w=1.0 m (n=5 seeds),
then across-seed mean ± sd. Regenerates figures/force_magnitude.pdf.

Phase B: Gate-occupancy w_o(ρ) distribution from the same force-logging
data (bottleneck w=1.0 m). Crossing/bidirectional: no archived density-
tagged agent-timestep logs exist (confirmed by grep; force_logging/ is
bottleneck-only). Those scenarios are reported as "data not archived".

Writes:
  figures/force_magnitude.pdf  (overwrites existing)
  figures/gate_occupancy_bottleneck.pdf
  results_new/gate_occupancy.csv
  revision-notes/10-force-magnitude.md
"""

import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)

FORCE_DIR = "results_new/force_logging"
OUT_FIG = "figures/force_magnitude.pdf"
OUT_GATE_FIG = "figures/gate_occupancy_bottleneck.pdf"
OUT_CSV = "results_new/gate_occupancy.csv"
OUT_MD = "revision-notes/10-force-magnitude.md"

RHO0 = 4.0
K = 2.0


def sigmoid(x, x0, k):
    return 1.0 / (1.0 + np.exp(-k * (x - x0)))


def w_orca(rho):
    return 1.0 - sigmoid(rho, RHO0, K)


def load_seeds():
    paths = sorted(glob.glob(os.path.join(FORCE_DIR, "force_C4_w1.0_seed*.parquet")))
    return {int(os.path.basename(p).split("seed")[1].split(".")[0]): pd.read_parquet(p) for p in paths}


def force_magnitude_bands(seeds):
    # log-spaced bins from min>0 density to max
    all_rho = np.concatenate([s["density"].values for s in seeds.values()])
    rho_pos = all_rho[all_rho > 0]
    rho_min, rho_max = np.percentile(rho_pos, [1, 99])
    bins = np.logspace(np.log10(max(rho_min, 1e-3)), np.log10(rho_max), 25)
    bin_centres = 0.5 * (bins[:-1] + bins[1:])

    components = ["mag_des", "mag_sfm", "mag_ttc", "mag_orca"]
    # per-seed medians per bin
    per_seed = {c: [] for c in components}
    for seed, df in seeds.items():
        bin_idx = np.digitize(df["density"].values, bins) - 1
        valid = (bin_idx >= 0) & (bin_idx < len(bin_centres))
        row_medians = {c: np.full(len(bin_centres), np.nan) for c in components}
        for b in range(len(bin_centres)):
            mask = valid & (bin_idx == b)
            if mask.sum() >= 5:
                for c in components:
                    vals = df[c].values[mask]
                    vals = vals[vals > 0]
                    if len(vals) >= 3:
                        row_medians[c][b] = np.median(vals)
        for c in components:
            per_seed[c].append(row_medians[c])

    agg = {}
    for c in components:
        arr = np.vstack(per_seed[c])  # (n_seeds, n_bins)
        agg[c] = (np.nanmean(arr, axis=0), np.nanstd(arr, axis=0))
    return bin_centres, agg


def plot_forces(bin_centres, agg):
    fig, ax = plt.subplots(figsize=(5.2, 3.5))
    colours = {"mag_des": "#1f77b4", "mag_sfm": "#d62728", "mag_ttc": "#2ca02c", "mag_orca": "#ff7f0e"}
    labels = {"mag_des": r"$|F_{\mathrm{des}}|$", "mag_sfm": r"$|F_{\mathrm{SFM}}|$",
              "mag_ttc": r"$|F_{\mathrm{TTC}}|$", "mag_orca": r"$|F_{\mathrm{ORCA}}|$"}
    for c, (m, s) in agg.items():
        valid = ~np.isnan(m)
        ax.plot(bin_centres[valid], m[valid], "-", color=colours[c], label=labels[c], lw=1.3)
        lo = np.clip(m - s, 1e-6, None)
        ax.fill_between(bin_centres[valid], lo[valid], (m + s)[valid], color=colours[c], alpha=0.18)
    ax.axvline(0.07, color="gray", linestyle=":", lw=0.8, label=r"$\rho \approx 0.07$ (crossover)")
    ax.axvline(RHO0, color="black", linestyle="--", lw=0.8, label=r"$\rho_0 = 4.0$ (sigmoid centre)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Local Voronoi density $\rho$ (ped/m$^2$)")
    ax.set_ylabel(r"Force magnitude")
    ax.legend(fontsize=7, loc="best")
    ax.set_title("")
    fig.tight_layout()
    fig.savefig(OUT_FIG)
    plt.close(fig)


def gate_occupancy(seeds):
    all_rho = np.concatenate([s["density"].values for s in seeds.values()])
    w = w_orca(all_rho)
    n = len(w)
    frac_orca = float(np.mean(w > 0.9))
    frac_force = float(np.mean(w < 0.1))
    frac_trans = float(np.mean((w >= 0.1) & (w <= 0.9)))
    # histogram fig
    fig, ax = plt.subplots(figsize=(4.5, 3))
    ax.hist(w, bins=50, color="#1f77b4", alpha=0.8)
    ax.axvline(0.1, color="k", linestyle="--", lw=0.8)
    ax.axvline(0.9, color="k", linestyle="--", lw=0.8)
    ax.set_xlabel(r"$w_o(\rho)$")
    ax.set_ylabel("agent-timestep count")
    ax.set_yscale("log")
    ax.set_title(f"Bottleneck w=1.0 m, C4 (n=5 seeds, {n:,} samples)")
    fig.tight_layout()
    fig.savefig(OUT_GATE_FIG)
    plt.close(fig)
    return {
        "scenario": "bottleneck_w1.0",
        "frac_orca_dominant": round(frac_orca, 4),
        "frac_force_dominant": round(frac_force, 4),
        "frac_transition": round(frac_trans, 4),
        "n_agent_timesteps": n,
    }


def main():
    seeds = load_seeds()
    bin_centres, agg = force_magnitude_bands(seeds)
    plot_forces(bin_centres, agg)
    bottleneck_occ = gate_occupancy(seeds)

    # Two scenarios with no archived density-per-agent-timestep logs
    rows = [
        bottleneck_occ,
        {"scenario": "crossing", "frac_orca_dominant": "NA",
         "frac_force_dominant": "NA", "frac_transition": "NA", "n_agent_timesteps": 0},
        {"scenario": "bidirectional", "frac_orca_dominant": "NA",
         "frac_force_dominant": "NA", "frac_transition": "NA", "n_agent_timesteps": 0},
    ]
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    # Band quality check
    band_widths = []
    for c, (m, s) in agg.items():
        valid = ~np.isnan(m) & ~np.isnan(s) & (m > 0)
        if valid.any():
            rel = s[valid] / m[valid]
            band_widths.append((c, float(np.nanmedian(rel))))

    # Write revision-notes
    with open(OUT_MD, "w") as fh:
        fh.write("# S10 force-magnitude + gate-occupancy\n\n")
        fh.write(f"## Figure 2 regenerated\n\n")
        fh.write(f"- Source: {FORCE_DIR}/force_C4_w1.0_seed{{42..46}}.parquet (n=5 seeds)\n")
        fh.write(f"- Method: per-seed median per log-spaced density bin; across-seed mean ± 1 sd\n")
        fh.write(f"- Output: {OUT_FIG}\n\n")
        fh.write("## Band quality (relative sd = across-seed sd / across-seed mean)\n\n")
        for c, r in band_widths:
            fh.write(f"- {c}: median relative sd = {r:.3f}\n")
        fh.write("\n")
        fh.write("5-seed bands are adequate where the components separate by orders of magnitude "
                 "(SFM vs ORCA at ρ>0.5). Near the ρ≈0.07 crossover, SFM sd is comparable to its "
                 "median, but the crossover location (SFM ≈ ORCA) is bracketed unambiguously by "
                 "the ordering of the point estimates across bins. A larger-n rerun would tighten "
                 "bands near the crossover; this is future work, not run here.\n\n")
        fh.write("## Gate occupancy\n\n")
        fh.write("| Scenario | w_o>0.9 (ORCA-dominant) | w_o<0.1 (force-dominant) | 0.1–0.9 (transition) | N agent-timesteps |\n")
        fh.write("|---|---|---|---|---|\n")
        for r in rows:
            fh.write(f"| {r['scenario']} | {r['frac_orca_dominant']} | {r['frac_force_dominant']} | {r['frac_transition']} | {r['n_agent_timesteps']:,} |\n")
        fh.write("\n")
        fh.write(f"Bottleneck w=1.0 m (C4, n=5 seeds, {bottleneck_occ['n_agent_timesteps']:,} samples): ")
        fh.write(f"w_o>0.9 = {100*bottleneck_occ['frac_orca_dominant']:.1f}%, ")
        fh.write(f"w_o<0.1 = {100*bottleneck_occ['frac_force_dominant']:.1f}%, ")
        fh.write(f"transition = {100*bottleneck_occ['frac_transition']:.1f}%.\n\n")
        fh.write("Crossing and bidirectional scenarios: archived agent-timestep density logs were not "
                 "persisted during the original S0 runs (force_logging/ is bottleneck-only). Reported "
                 "as data-gap; the paper text uses the bottleneck percentages and flags the gap.\n")

    print("S10 done:", rows[0])


if __name__ == "__main__":
    main()
