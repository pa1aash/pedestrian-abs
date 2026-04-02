"""Experiment configurations for hybrid steering ablation.

C1-C4: steering model combinations.
D1-D4: crush threshold variations.
"""

CONFIGS: dict[str, dict[str, bool]] = {
    "C1": {"sfm": True, "ttc": False, "orca": False, "crush": False},
    "C2": {"sfm": True, "ttc": True, "orca": False, "crush": False},
    "C3": {"sfm": True, "ttc": False, "orca": True, "crush": False},
    "C4": {"sfm": True, "ttc": True, "orca": True, "crush": True},
}

CRUSH_CONFIGS: dict[str, float | None] = {
    "D1": None,
    "D2": 5.0,
    "D3": 5.5,
    "D4": 7.0,
}


def get_config(name: str) -> dict[str, bool]:
    """Look up a steering configuration by name.

    Args:
        name: Configuration name (C1-C4).

    Returns:
        Dict with boolean keys sfm, ttc, orca, crush.

    Raises:
        KeyError: If name is not a valid configuration.
    """
    return CONFIGS[name]
