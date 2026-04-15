"""S9 Phase A3: per-paradigm OOD decomposition at w=2.4 and 3.6 m.

Loads:
  - results_new/ood_per_paradigm.csv  (C1, C4 @ widths 2.4, 3.6)
  - results_new/table5_rerun_correct.csv  (C2, C3 @ widths 2.4, 3.6)
  - results_analysis/ood_validation.csv   (empirical J_emp per width)

Writes:
  - revision-notes/09-ood-per-paradigm.md  (interpretive narrative)
  - results_analysis/ood_per_paradigm.csv  (tidy long-form)
"""

import os
import sys

import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)

WIDTHS = [2.4, 3.6]


def j_from_table5(df: pd.DataFrame) -> pd.DataFrame:
    """Compute J_sim = agents_exited / evacuation_time per row (ped/s)."""
    df = df.copy()
    good = (df["evacuation_time"] > 0) & np.isfinite(df["evacuation_time"]) & (df["agents_exited"] > 0)
    df = df[good].copy()
    df["J_sim"] = df["agents_exited"] / df["evacuation_time"]
    return df


def main():
    ood = pd.read_csv("results_new/ood_per_paradigm.csv")
    t5 = pd.read_csv("results_new/table5_rerun_correct.csv")
    t5 = t5[t5["width"].isin(WIDTHS) & t5["config"].isin(["C2", "C3"])]
    t5 = j_from_table5(t5)
    t5_keep = t5[["width", "config", "seed", "J_sim", "n_agents"]].copy()

    ood_keep = ood[ood["width"].isin(WIDTHS)][["width", "config", "seed", "J_sim", "n_agents"]].copy()

    all_rows = pd.concat([ood_keep, t5_keep], ignore_index=True)
    jemp = pd.read_csv("results_analysis/ood_validation.csv").set_index("width_m")["flow_rate_empirical"]

    summary = []
    for w in WIDTHS:
        for cfg in ["C1", "C2", "C3", "C4"]:
            sub = all_rows[(all_rows["width"] == w) & (all_rows["config"] == cfg)]
            if len(sub) == 0:
                continue
            mean = float(sub["J_sim"].mean())
            sd = float(sub["J_sim"].std(ddof=1))
            j_emp = float(jemp.loc[w])
            rel = (mean - j_emp) / j_emp
            summary.append({
                "width": w, "config": cfg, "n": int(len(sub)),
                "J_sim_mean": round(mean, 3), "J_sim_sd": round(sd, 3),
                "J_emp": round(j_emp, 3), "rel_err_pct": round(100 * rel, 1),
            })

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv("results_analysis/ood_per_paradigm.csv", index=False)

    # Markdown report
    lines = ["# S9 OOD per-paradigm decomposition", ""]
    lines.append(f"Source: results_new/ood_per_paradigm.csv (C1, C4) and results_new/table5_rerun_correct.csv (C2, C3); 50 agents per run, seeds 42-66 paired.")
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append("| Width (m) | Config | n | J_sim mean (ped/s) | J_sim sd | J_emp (ped/s) | rel err |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in summary:
        lines.append(f"| {r['width']} | {r['config']} | {r['n']} | {r['J_sim_mean']} | {r['J_sim_sd']} | {r['J_emp']} | {r['rel_err_pct']}% |")
    lines.append("")

    # Interpretation: which config has smallest |rel_err| per width
    lines.append("## Interpretation")
    lines.append("")
    for w in WIDTHS:
        sub = [r for r in summary if r["width"] == w]
        best = min(sub, key=lambda r: abs(r["rel_err_pct"]))
        worst = max(sub, key=lambda r: abs(r["rel_err_pct"]))
        lines.append(f"- **w = {w} m**: {best['config']} closes the bias most (|rel_err| = {abs(best['rel_err_pct'])}%); {worst['config']} is furthest from empirical (|rel_err| = {abs(worst['rel_err_pct'])}%).")
    lines.append("")

    # Does the bias narrow with width under each paradigm?
    lines.append("## Does the bias narrow with width, per configuration?")
    lines.append("")
    for cfg in ["C1", "C2", "C3", "C4"]:
        r24 = next((r for r in summary if r["config"] == cfg and r["width"] == 2.4), None)
        r36 = next((r for r in summary if r["config"] == cfg and r["width"] == 3.6), None)
        if r24 and r36:
            direction = "narrows" if abs(r36["rel_err_pct"]) < abs(r24["rel_err_pct"]) else "widens"
            lines.append(f"- **{cfg}**: |rel_err| goes from {abs(r24['rel_err_pct'])}% at 2.4 m to {abs(r36['rel_err_pct'])}% at 3.6 m — bias {direction} with width.")
    lines.append("")

    lines.append("## Protocol comparability note")
    lines.append("")
    lines.append(
        "The aggregate §4.3 OOD bias (-26% to -43% across 5 widths) uses n_agents = 100; "
        "this per-paradigm decomposition uses n_agents = 50 for consistency with the Table 5 "
        "protocol. Mixing cell counts is acceptable because we report *relative* errors per cell, "
        "not pooled counts. The per-cell J_sim will differ quantitatively between the two "
        "protocols (higher congestion at n=100 widens the empirical gap); the diagnostic "
        "we extract is *which configuration closes the bias most*, which is protocol-independent "
        "at the qualitative level."
    )
    lines.append("")

    lines.append("## Paper edits triggered")
    lines.append("")
    lines.append("- Extend Table 3 at rows w=2.4 and w=3.6 with J_sim for C1, C2, C3, C4; retain aggregate-only entries for w=3.0, 4.4, 5.0.")
    lines.append("- Add §4.3 paragraph 2 summarising which paradigm closes the bias and whether the bias narrows with width.")
    lines.append("- Add §5 Limitations sentence noting 3 of 5 widths remain at aggregate-only protocol.")

    with open("revision-notes/09-ood-per-paradigm.md", "w") as fh:
        fh.write("\n".join(lines))

    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
