"""Data loaders for FZJ and ETH-UCY pedestrian trajectory datasets."""

import glob
import os

import numpy as np
import pandas as pd


def load_fzj(filepath: str) -> pd.DataFrame:
    """Load a single FZJ trajectory file.

    FZJ format: ped_id frame_id x y z (space-separated, comment=#).

    Args:
        filepath: Path to .txt file.

    Returns:
        DataFrame with columns ped_id, frame_id, x, y, sorted by ped_id, frame_id.
    """
    df = pd.read_csv(
        filepath,
        sep=r"\s+",
        header=None,
        names=["ped_id", "frame_id", "x", "y", "z"],
        comment="#",
    )
    return (
        df[["ped_id", "frame_id", "x", "y"]]
        .sort_values(["ped_id", "frame_id"])
        .reset_index(drop=True)
    )


def load_eth_ucy(filepath: str) -> pd.DataFrame:
    """Load a single ETH-UCY trajectory file.

    ETH-UCY format: frame_id ped_id x y (space/tab-separated).

    Args:
        filepath: Path to .txt file.

    Returns:
        DataFrame with columns ped_id, frame_id, x, y, sorted by ped_id, frame_id.
    """
    df = pd.read_csv(
        filepath,
        sep=r"\s+",
        header=None,
        names=["frame_id", "ped_id", "x", "y"],
    )
    return (
        df[["ped_id", "frame_id", "x", "y"]]
        .sort_values(["ped_id", "frame_id"])
        .reset_index(drop=True)
    )


def add_velocities(df: pd.DataFrame, fps: float) -> pd.DataFrame:
    """Add vx, vy, speed columns via finite differences.

    Accounts for variable frame gaps by using actual frame_id differences.

    Args:
        df: DataFrame with ped_id, frame_id, x, y columns.
        fps: Frame rate of the recording.

    Returns:
        DataFrame with added vx, vy, speed columns (NaN rows dropped).
    """
    df = df.sort_values(["ped_id", "frame_id"]).copy()
    # Time delta from actual frame gaps
    df["dt"] = df.groupby("ped_id")["frame_id"].diff() / fps
    df["vx"] = df.groupby("ped_id")["x"].diff() / df["dt"]
    df["vy"] = df.groupby("ped_id")["y"].diff() / df["dt"]
    df["speed"] = np.sqrt(df["vx"] ** 2 + df["vy"] ** 2)
    return df.dropna(subset=["vx"]).drop(columns=["dt"]).reset_index(drop=True)


def load_fzj_all(directory: str, fps: float = 16.0) -> pd.DataFrame:
    """Load all FZJ trajectory files from a directory and add velocities.

    Args:
        directory: Path to directory containing .txt files.
        fps: Frame rate (FZJ default: 16 fps per file headers).

    Returns:
        Combined DataFrame with velocities.
    """
    files = sorted(glob.glob(os.path.join(directory, "*.txt")))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        df = load_fzj(f)
        df = add_velocities(df, fps)
        df["source_file"] = os.path.basename(f)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def weidmann_speed(density: np.ndarray) -> np.ndarray:
    """Weidmann (1993) fundamental diagram: speed as a function of density.

    v(rho) = 1.34 * (1 - exp(-1.913 * (1/rho - 1/5.4)))

    Args:
        density: Density values (ped/m^2).

    Returns:
        Speed values (m/s).
    """
    rho = np.clip(np.asarray(density, float), 0.01, 5.39)
    return 1.34 * (1.0 - np.exp(-1.913 * (1.0 / rho - 1.0 / 5.4)))
