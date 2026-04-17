"""Regenerate LaTeX table input files for paper/main.tex.

Outputs:
  results_analysis/zonal_collisions_table.tex  (\tabular only)
  results_analysis/ood_table.tex                 (\tabular only)
  results_analysis/external_comparison.tex       (full \begin{table})

See MASTER_PROMPT.md §8.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
RESN = REPO / "results_new"
RESA = REPO / "results_analysis"


def zonal_table():
    df = pd.read_csv(RESA / "zonal_collisions.csv")
    rows = []
    for cfg in ("C1", "C4"):
        for w in (0.8, 1.0):
            sub = df[(df.config == cfg) & (df.width == w)]
            u = sub[sub.zone == "upstream"].collision_count
            t = sub[sub.zone == "throat"].collision_count
            d = sub[sub.zone == "downstream"].collision_count
            rows.append(
                (cfg, w, (u.mean(), u.std()), (t.mean(), t.std()),
                 (d.mean(), d.std()))
            )
    lines = [
        r"\begin{tabular}{@{}llrrr@{}}",
        r"\toprule",
        r"\textbf{Config} & \textbf{Width (m)} & \textbf{Upstream} "
        r"& \textbf{Throat} & \textbf{Downstream} \\",
        r"\midrule",
    ]
    for cfg, w, (um, us), (tm, ts), (dm, ds) in rows:
        lines.append(
            f"{cfg} & {w:.1f} & ${um:.1f} \\pm {us:.1f}$ & ${tm:.1f} "
            f"\\pm {ts:.1f}$ & ${dm:.1f} \\pm {ds:.1f}$ \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    out = RESA / "zonal_collisions_table.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  zonal_collisions_table.tex")


def ood_table():
    df = pd.read_csv(RESA / "ood_validation.csv")
    lines = [
        r"\begin{tabular}{@{}rrrrrr@{}}",
        r"\toprule",
        r"$w$ (m) & $J_{\text{emp}}$ (ped/s) & $J_{\text{sim}}$ (ped/s) "
        r"& $\sigma_{\text{sim}}$ & Abs.\ err. & Rel.\ err. \\",
        r"\midrule",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"{r.width_m:.1f} & {r.flow_rate_empirical:.3f} & "
            f"{r.flow_rate_sim:.3f} & {r.flow_rate_std:.3f} & "
            f"{r.abs_error:.3f} & {r.rel_error_pct:.1f}\\% \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    out = RESA / "ood_table.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  ood_table.tex")


def external_comparison_table():
    cfs = pd.read_csv(
        RESN / "external_simulator" / "jupedsim_CollisionFreeSpeed_combined.csv"
    )
    sf = pd.read_csv(
        RESN / "external_simulator" / "jupedsim_SocialForce_combined.csv"
    )
    c1 = pd.read_csv(RES / "Bottleneck_w1.0_C1.csv")
    c4 = pd.read_csv(RES / "Bottleneck_w1.0_C4.csv")

    def mean_std(s):
        s = s.replace([np.inf, -np.inf], np.nan).dropna()
        return s.mean(), s.std()

    c1_t = mean_std(c1.evacuation_time)
    c4_t = mean_std(c4.evacuation_time)
    c1_col = mean_std(c1.collision_count)
    c4_col = mean_std(c4.collision_count)
    c1_rt = c1.wall_time_s.mean()
    c4_rt = c4.wall_time_s.mean()
    cfs_t = mean_std(cfs.evacuation_time)
    cfs_rt = cfs.wall_time_s.mean()
    sf_ex = sf.agents_exited
    sf_rt = sf.wall_time_s.mean()
    sf_complete = int((sf.evacuation_time != np.inf).sum())

    lines = [
        r"\begin{table}[h]",
        r"\caption{External simulator comparison at $w=1.0$\,m bottleneck, "
        r"50 agents, $n=25$ seeds. JuPedSim uses tool-default parameters "
        r"(not tuned to match ours). JuPedSim SF did not complete evacuation "
        r"in any seed within 60\,s; agents exited is reported instead of "
        r"evacuation time.}\label{tab:external}",
        r"\centering\scriptsize",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"\textbf{Tool} & \textbf{Evac.\ time (s)} & \textbf{Agents exited} "
        r"& \textbf{Contact-overlaps} & \textbf{Runtime (s)} \\",
        r"\midrule",
        f"Ours C1 (SFM) & ${c1_t[0]:.1f} \\pm {c1_t[1]:.1f}$ & 50/50 & "
        f"${c1_col[0]:.0f} \\pm {c1_col[1]:.0f}$ & {c1_rt:.1f} \\\\",
        f"Ours C4 (hybrid) & ${c4_t[0]:.1f} \\pm {c4_t[1]:.1f}$ & 50/50 & "
        f"${c4_col[0]:.0f} \\pm {c4_col[1]:.0f}$ & {c4_rt:.1f} \\\\",
        f"JuPedSim CFS & ${cfs_t[0]:.1f} \\pm {cfs_t[1]:.1f}$ & 50/50 & --- "
        f"& {cfs_rt:.1f} \\\\",
        f"JuPedSim SF & --- ({sf_complete}/25 complete) & "
        f"${sf_ex.mean():.1f} \\pm {sf_ex.std():.1f}$/50 & --- & "
        f"{sf_rt:.1f} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    out = RESA / "external_comparison.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  external_comparison.tex")


def main():
    print("Regenerating tables into", RESA)
    zonal_table()
    ood_table()
    external_comparison_table()
    print("Done.")


if __name__ == "__main__":
    main()
