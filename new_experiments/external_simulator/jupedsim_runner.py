"""R3.3 — JuPedSim external simulator comparison.

Runs the same 10x10m bottleneck (w=1.0m exit, 50 agents) geometry in
JuPedSim using TWO of its built-in models:
  1. CollisionFreeSpeedModel (velocity-based, closest analogue to ORCA)
  2. SocialForceModel (force-based, closest analogue to our SFM)

Both use JuPedSim's default parameters — no tuning to match our values.
This is intentional: the comparison tests whether the same geometry
produces qualitatively similar aggregate behaviour under a completely
independent implementation.

Configuration:
  Geometry: 10x10m room, 1.0m exit centred on right wall (matching our BottleneckScenario)
  Agents: 50, spawned in [0.5, 8.5] x [0.5, 9.5], goal = exit
  Seeds: 42-66 (25 seeds)
  Max time: 60s, dt=0.01s

Output: results_new/external_simulator/jupedsim_<model>_seed{42..66}.csv
  Columns: model, seed, evacuation_time, agents_exited, wall_time_s
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import shapely

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import jupedsim as jps

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "results_new", "external_simulator")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEEDS = list(range(42, 67))
MAX_TIME = 60.0
DT = 0.01
N_AGENTS = 50
ROOM_W, ROOM_H = 10.0, 10.0
EXIT_WIDTH = 1.0


def build_geometry():
    """Build the 10x10 room with a 1.0m exit centred on the right wall.

    JuPedSim geometry = walkable area as a polygon. The exit is modelled
    as a small extension beyond the right wall that agents walk into.
    """
    half = EXIT_WIDTH / 2.0
    y_bot = ROOM_H / 2.0 - half  # 4.5
    y_top = ROOM_H / 2.0 + half  # 5.5

    # Room polygon with a small exit corridor extending 1m past the right wall
    coords = [
        (0, 0), (ROOM_W, 0),                    # bottom wall
        (ROOM_W, y_bot),                          # right wall below exit
        (ROOM_W + 1.0, y_bot),                    # exit corridor bottom
        (ROOM_W + 1.0, y_top),                    # exit corridor top
        (ROOM_W, y_top),                          # right wall above exit
        (ROOM_W, ROOM_H), (0, ROOM_H),           # top and left walls
        (0, 0),
    ]
    return shapely.Polygon(coords)


def build_exit_polygon():
    """Exit zone: a rectangle just past the right wall."""
    half = EXIT_WIDTH / 2.0
    y_bot = ROOM_H / 2.0 - half
    y_top = ROOM_H / 2.0 + half
    return shapely.Polygon([
        (ROOM_W + 0.5, y_bot),
        (ROOM_W + 1.0, y_bot),
        (ROOM_W + 1.0, y_top),
        (ROOM_W + 0.5, y_top),
    ])


def spawn_positions(seed: int, n: int) -> list[tuple[float, float]]:
    """Generate random spawn positions in the room interior."""
    rng = np.random.Generator(np.random.PCG64(seed))
    positions = []
    for _ in range(n * 10):  # oversample to handle rejections
        x = rng.uniform(1.0, 8.0)
        y = rng.uniform(1.0, 9.0)
        # Check minimum separation from existing agents
        too_close = False
        for px, py in positions:
            if (x - px) ** 2 + (y - py) ** 2 < 0.5 ** 2:
                too_close = True
                break
        if not too_close:
            positions.append((x, y))
        if len(positions) >= n:
            break
    return positions[:n]


def run_jupedsim(model_name: str, seed: int) -> dict:
    """Run one JuPedSim simulation."""
    geometry = build_geometry()
    exit_polygon = build_exit_polygon()

    # Select model with defaults
    if model_name == "CollisionFreeSpeed":
        model = jps.CollisionFreeSpeedModel()
    elif model_name == "SocialForce":
        model = jps.SocialForceModel()
    else:
        raise ValueError(f"Unknown model: {model_name}")

    sim = jps.Simulation(model=model, geometry=geometry, dt=DT)

    # Add exit stage and journey
    exit_id = sim.add_exit_stage(exit_polygon)
    journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))

    # Spawn agents
    positions = spawn_positions(seed, N_AGENTS)
    for pos in positions:
        if model_name == "CollisionFreeSpeed":
            params = jps.CollisionFreeSpeedModelAgentParameters(
                position=pos,
                journey_id=journey_id,
                stage_id=exit_id,
                desired_speed=1.2,
                radius=0.2,
            )
        else:  # SocialForce
            params = jps.SocialForceModelAgentParameters(
                position=pos,
                journey_id=journey_id,
                stage_id=exit_id,
                desired_speed=0.8,  # JuPedSim SFM default
                radius=0.3,
            )
        sim.add_agent(params)

    # Run
    t0_wall = time.perf_counter()
    max_steps = int(MAX_TIME / DT)
    step = 0

    try:
        for step in range(max_steps):
            sim.iterate()
            if sim.agent_count() == 0:
                break
    except RuntimeError as e:
        # Agent pushed outside geometry — record partial result
        print(f"      RuntimeError at step {step}: {e}", flush=True)

    elapsed = time.perf_counter() - t0_wall
    agents_exited = N_AGENTS - sim.agent_count()
    evac_time = (step + 1) * DT if sim.agent_count() == 0 else float("inf")

    return {
        "model": model_name,
        "seed": seed,
        "evacuation_time": evac_time,
        "agents_exited": agents_exited,
        "wall_time_s": elapsed,
    }


def main():
    print("R3.3 JuPedSim external comparison", flush=True)

    for model_name in ["CollisionFreeSpeed", "SocialForce"]:
        print(f"\n  Model: {model_name}", flush=True)
        rows = []

        for i, seed in enumerate(SEEDS):
            tag = f"jupedsim_{model_name}_seed{seed}"
            csv_path = os.path.join(OUTPUT_DIR, f"{tag}.csv")

            if os.path.exists(csv_path):
                print(f"    [{i+1}/{len(SEEDS)}] seed={seed} SKIP", flush=True)
                rows.append(pd.read_csv(csv_path).iloc[0].to_dict())
                continue

            result = run_jupedsim(model_name, seed)
            rows.append(result)
            pd.DataFrame([result]).to_csv(csv_path, index=False)

            evac = result["evacuation_time"]
            evac_str = f"{evac:.1f}s" if evac != float("inf") else "inf"
            print(f"    [{i+1}/{len(SEEDS)}] seed={seed} evac={evac_str} "
                  f"exit={result['agents_exited']}/{N_AGENTS} "
                  f"wall={result['wall_time_s']:.1f}s", flush=True)

        # Combined CSV per model
        combined = pd.DataFrame(rows)
        combined.to_csv(os.path.join(OUTPUT_DIR, f"jupedsim_{model_name}_combined.csv"),
                        index=False)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
