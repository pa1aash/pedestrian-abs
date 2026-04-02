"""Extract speed-density (fundamental diagram) data from tracking datasets."""

import numpy as np
import pandas as pd


def compute_empirical_fd(
    df: pd.DataFrame,
    measurement_area: tuple[float, float, float, float],
    fps: float = 25.0,
) -> pd.DataFrame:
    """Compute speed-density per frame within a measurement area.

    Args:
        df: DataFrame with frame_id, ped_id, x, y, speed columns.
        measurement_area: (x_min, y_min, x_max, y_max) bounding box.
        fps: Frame rate (unused, speeds should already be computed).

    Returns:
        DataFrame with frame_id, mean_density, mean_speed columns.
    """
    x0, y0, x1, y1 = measurement_area
    area = (x1 - x0) * (y1 - y0)

    mask = (df["x"] >= x0) & (df["x"] <= x1) & (df["y"] >= y0) & (df["y"] <= y1)
    filtered = df[mask]

    rows = []
    for fid, g in filtered.groupby("frame_id"):
        if len(g) < 2:
            continue
        rows.append({
            "frame_id": fid,
            "mean_density": len(g) / area,
            "mean_speed": g["speed"].mean(),
        })

    return pd.DataFrame(rows)
