"""Data inventory: allowlist for existing results/ CSVs.

Excludes stub files (n=5), superseded runs, and non-CSV artefacts.
All analysis scripts import from here to guarantee a consistent data source.
"""

import glob
import os

import pandas as pd

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

# Files excluded from analysis: stubs (n=5), superseded, or non-experiment files
EXCLUDED_FILENAMES = {
    # n=5 stubs superseded by n=25 Bottleneck_w* files
    "BottleneckScenario_C1.csv",
    "BottleneckScenario_C2.csv",
    "BottleneckScenario_C3.csv",
    "BottleneckScenario_C4.csv",
    # n=5 short-window w=0.8 stubs (superseded by 600s versions)
    "Bottleneck_w0.8_C1.csv",
    "Bottleneck_w0.8_C2.csv",
    "Bottleneck_w0.8_C3.csv",
    "Bottleneck_w0.8_C4.csv",
    # n=5 exploratory long runs (partial coverage)
    "Bottleneck_w0.8_long_C1.csv",
    "Bottleneck_w0.8_long_C4.csv",
    # Early sigmoid stub
    "sigmoid_sensitivity.csv",
    # Legacy optimizer history
    "optimizer_history.json",
}


def load_allowed_csv(pattern: str) -> pd.DataFrame:
    """Glob for CSVs matching pattern, exclude stubs, concat.

    Args:
        pattern: Glob pattern relative to results/ dir (e.g. "Bottleneck_w*_C*.csv").

    Returns:
        Concatenated DataFrame from all matching, non-excluded files.
    """
    full_pattern = os.path.join(RESULTS_DIR, pattern)
    paths = sorted(glob.glob(full_pattern))
    dfs = []
    for p in paths:
        if os.path.basename(p) in EXCLUDED_FILENAMES:
            continue
        dfs.append(pd.read_csv(p))
    if not dfs:
        raise FileNotFoundError(f"No allowed CSVs match {pattern} in {RESULTS_DIR}")
    return pd.concat(dfs, ignore_index=True)


def list_allowed(pattern: str = "*.csv") -> list[str]:
    """List allowed CSV filenames matching pattern."""
    full_pattern = os.path.join(RESULTS_DIR, pattern)
    paths = sorted(glob.glob(full_pattern))
    return [os.path.basename(p) for p in paths
            if os.path.basename(p) not in EXCLUDED_FILENAMES]
