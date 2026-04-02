"""Extract speed-density (fundamental diagram) data from tracking datasets."""

import numpy as np
import pandas as pd


def extract_speed_density(
    df: pd.DataFrame,
    fps: float = 25.0,
    radius: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-pedestrian speed and local density from tracking data.

    Args:
        df: DataFrame with frame_id, ped_id, x, y columns.
        fps: Frame rate of the tracking data.
        radius: Counting radius for local density.

    Returns:
        (densities, speeds) arrays.
    """
    df = df.sort_values(["ped_id", "frame_id"])

    # Compute speeds: displacement / time between frames
    speeds_list = []
    densities_list = []

    frames = sorted(df["frame_id"].unique())
    if len(frames) < 2:
        return np.array([]), np.array([])

    dt = 1.0 / fps

    for i in range(1, len(frames)):
        f_prev, f_curr = frames[i - 1], frames[i]
        prev = df[df["frame_id"] == f_prev].set_index("ped_id")
        curr = df[df["frame_id"] == f_curr].set_index("ped_id")

        common = prev.index.intersection(curr.index)
        if len(common) < 2:
            continue

        for pid in common:
            p0 = prev.loc[pid, ["x", "y"]].values.astype(float)
            p1 = curr.loc[pid, ["x", "y"]].values.astype(float)
            speed = np.linalg.norm(p1 - p0) / (dt * (f_curr - f_prev))

            # Local density: count neighbors within radius
            all_pos = curr.loc[common, ["x", "y"]].values.astype(float)
            pos_i = curr.loc[pid, ["x", "y"]].values.astype(float)
            dists = np.linalg.norm(all_pos - pos_i, axis=1)
            n_neighbors = np.sum(dists < radius) - 1  # exclude self
            density = n_neighbors / (np.pi * radius * radius)

            speeds_list.append(speed)
            densities_list.append(density)

    return np.array(densities_list), np.array(speeds_list)
