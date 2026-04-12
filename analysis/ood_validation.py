"""R2.6 — Out-of-distribution validation from bottleneck_validation.csv.

Computes absolute and relative error between simulated and empirical
FZJ bottleneck flow rates. Frames the -27% to -43% gap as OOD
generalisation, not a hidden weakness.
"""

import os
import sys

import numpy as np
import pandas as pd

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from analysis.inventory import RESULTS_DIR

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "results_analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("R2.6 OOD Validation", flush=True)

    path = os.path.join(RESULTS_DIR, "bottleneck_validation.csv")
    df = pd.read_csv(path)

    df["abs_error"] = df["flow_rate_sim"] - df["flow_rate_empirical"]
    df["rel_error"] = (df["flow_rate_sim"] - df["flow_rate_empirical"]) / df["flow_rate_empirical"]
    df["rel_error_pct"] = df["rel_error"] * 100

    # CSV output
    csv_path = os.path.join(OUTPUT_DIR, "ood_validation.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> {csv_path}")

    # LaTeX table
    tex_lines = [
        r"\begin{tabular}{@{}rrrrrr@{}}",
        r"\toprule",
        r"$w$ (m) & $J_{\text{emp}}$ (ped/s) & $J_{\text{sim}}$ (ped/s) & $\sigma_{\text{sim}}$ & Abs.\ err. & Rel.\ err. \\",
        r"\midrule",
    ]
    for _, row in df.iterrows():
        tex_lines.append(
            f"{row['width_m']:.1f} & {row['flow_rate_empirical']:.3f} & "
            f"{row['flow_rate_sim']:.3f} & {row['flow_rate_std']:.3f} & "
            f"{row['abs_error']:+.3f} & {row['rel_error_pct']:+.1f}\\% \\\\"
        )
    tex_lines.append(r"\bottomrule")
    tex_lines.append(r"\end{tabular}")

    tex_path = os.path.join(OUTPUT_DIR, "ood_table.tex")
    with open(tex_path, "w") as f:
        f.write("\n".join(tex_lines))
    print(f"  -> {tex_path}")

    # Paragraph
    rel_min = df["rel_error_pct"].min()
    rel_max = df["rel_error_pct"].max()

    paragraph = (
        f"To assess out-of-distribution generalisation, we compare the calibrated model's "
        f"bottleneck flow rates against FZJ empirical bottleneck measurements at five exit widths "
        f"(Table~\\ref{{tab:ood}}). "
        f"The model was calibrated exclusively on unidirectional corridor data (Section~\\ref{{sec:calibration}}); "
        f"the bottleneck geometry was not used during fitting. "
        f"Simulated flow rates systematically underestimate empirical values, with relative errors "
        f"ranging from {rel_min:+.0f}\\% to {rel_max:+.0f}\\%. "
        f"This negative bias is consistent with the known limitation that SFM-based models "
        f"over-predict body-contact forces at narrow exits, reducing effective throughput. "
        f"The gap motivates the diagnostic ablation approach of this paper: rather than "
        f"claiming the calibrated model generalises across geometries, we characterise "
        f"where each steering paradigm fails and use the ablation to identify which "
        f"paradigm component is responsible for the throughput deficit. "
        f"The OOD gap also establishes a concrete benchmark for future held-out "
        f"calibration against FZJ bottleneck trajectories."
    )

    para_path = os.path.join(OUTPUT_DIR, "ood_paragraph.md")
    with open(para_path, "w") as f:
        f.write("# R2.6 OOD Validation Paragraph\n\n")
        f.write("Drop-in for Section 4:\n\n")
        f.write(paragraph + "\n")
    print(f"  -> {para_path}")

    print(f"\n  Rel error range: {rel_min:+.1f}% to {rel_max:+.1f}%")
    print("Done.", flush=True)
    return df


if __name__ == "__main__":
    main()
