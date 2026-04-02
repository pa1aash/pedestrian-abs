"""Data loaders for FZJ and ETH-UCY pedestrian datasets."""

import os

import numpy as np
import pandas as pd


def load_fzj(dataset: str = "unidirectional", data_dir: str = "data/fzj/") -> pd.DataFrame:
    """Load FZJ pedestrian tracking data.

    Args:
        dataset: One of "unidirectional", "bidirectional", "bottleneck".
        data_dir: Base directory for FZJ data.

    Returns:
        DataFrame with columns: frame_id, ped_id, x, y.
    """
    path = os.path.join(data_dir, dataset)
    dfs = []
    for f in sorted(os.listdir(path)):
        if f.endswith(".txt"):
            df = pd.read_csv(
                os.path.join(path, f),
                sep=r"\s+",
                header=None,
                names=["frame_id", "ped_id", "x", "y"],
                comment="#",
            )
            df["source_file"] = f
            dfs.append(df)
    if not dfs:
        return pd.DataFrame(columns=["frame_id", "ped_id", "x", "y"])
    return pd.concat(dfs, ignore_index=True)


def load_eth_ucy(
    scene: str = "eth",
    split: str = "train",
    data_dir: str = "data/eth-ucy/",
) -> pd.DataFrame:
    """Load ETH-UCY pedestrian tracking data.

    Args:
        scene: One of "eth", "hotel", "univ", "zara1", "zara2".
        split: One of "train", "val", "test".
        data_dir: Base directory.

    Returns:
        DataFrame with columns: frame_id, ped_id, x, y.
    """
    path = os.path.join(data_dir, scene, split)
    dfs = []
    if os.path.isdir(path):
        for f in sorted(os.listdir(path)):
            if f.endswith(".txt"):
                df = pd.read_csv(
                    os.path.join(path, f),
                    sep=r"\s+",
                    header=None,
                    names=["frame_id", "ped_id", "x", "y"],
                )
                df["source_file"] = f
                dfs.append(df)
    if not dfs:
        return pd.DataFrame(columns=["frame_id", "ped_id", "x", "y"])
    return pd.concat(dfs, ignore_index=True)
