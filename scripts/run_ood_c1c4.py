"""Phase A2: Run C1 and C4 at w=2.4 and w=3.6 for seeds 42-66.

Produces results_new/ood_per_paradigm.csv with header:
  width, config, seed, J_sim, wall_seconds, n_agents

Also seeds 42-44 already exist in results_backup/ — those are re-run here
for consistency (same protocol, n_agents=50). Backup data had no n_agents
column, so we regenerate them with the table5 protocol.

Halt conditions:
  - total wall-clock > 3 hr
  - J_sim < 0 or > 20 ped/s
  - > 5 seed errors in any single cell

Logs failures to revision-notes/09-failures.log.
"""

import csv
import os
import sys
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
os.chdir(_PROJECT_ROOT)

from sim.core.simulation import Simulation
from sim.scenarios.bottleneck import BottleneckScenario

SEEDS = list(range(42, 67))  # 25 seeds
WIDTHS = [2.4, 3.6]
CONFIGS = ["C1", "C4"]
N_AGENTS = 50
MAX_TIME = 60.0  # seconds of sim time (generous for wide exits)

OUTPUT_CSV = os.path.join(_PROJECT_ROOT, "results_new", "ood_per_paradigm.csv")
FAILURE_LOG = os.path.join(_PROJECT_ROOT, "revision-notes", "09-failures.log")
FIELDNAMES = ["width", "config", "seed", "J_sim", "wall_seconds", "n_agents"]

HALT_WALL_HR = 3.0
HALT_JSIM_LO = 0.0
HALT_JSIM_HI = 20.0
HALT_MAX_ERRORS_PER_CELL = 5


def load_existing() -> set[tuple[str, float, int]]:
    """Return set of (config, width, seed) already written."""
    done: set[tuple[str, float, int]] = set()
    if not os.path.exists(OUTPUT_CSV):
        return done
    with open(OUTPUT_CSV, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            done.add((row["config"], float(row["width"]), int(row["seed"])))
    return done


def log_failure(msg: str) -> None:
    os.makedirs(os.path.dirname(FAILURE_LOG), exist_ok=True)
    with open(FAILURE_LOG, "a") as fh:
        fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def run_one(config: str, width: float, seed: int) -> dict:
    """Run one bottleneck simulation. Returns result dict."""
    scenario = BottleneckScenario(n_agents=N_AGENTS, exit_width=width)
    sim = Simulation.from_scenario(scenario, config, seed=seed)

    t0 = time.perf_counter()
    result = sim.run(max_steps=200_000, max_time=MAX_TIME)
    wall = time.perf_counter() - t0

    agents_exited = result["agents_exited"]
    evac_time = result["evacuation_time"]

    # J_sim = agents_exited / evac_time (ped/s), matching table5 protocol
    if evac_time is None or evac_time == float("inf") or evac_time <= 0:
        # Incomplete evacuation — use actual sim time as denominator
        j_sim = agents_exited / MAX_TIME if agents_exited > 0 else 0.0
    else:
        j_sim = agents_exited / evac_time

    return {
        "width": width,
        "config": config,
        "seed": seed,
        "J_sim": j_sim,
        "wall_seconds": wall,
        "n_agents": N_AGENTS,
        "_agents_exited": agents_exited,
        "_evac_time": evac_time,
    }


def main() -> None:
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    os.makedirs(os.path.dirname(FAILURE_LOG), exist_ok=True)

    done = load_existing()

    # Build work list: iterate cell by cell for checkpoint reporting
    work = [
        (cfg, w, s)
        for w in WIDTHS
        for cfg in CONFIGS
        for s in SEEDS
        if (cfg, w, s) not in done
    ]

    total_cells = len(WIDTHS) * len(CONFIGS)
    print(
        f"OOD C1/C4 runner: {len(work)} remaining of "
        f"{len(WIDTHS)*len(CONFIGS)*len(SEEDS)} total",
        flush=True,
    )

    write_header = not os.path.exists(OUTPUT_CSV) or os.path.getsize(OUTPUT_CSV) == 0

    t_global_start = time.time()

    with open(OUTPUT_CSV, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        idx_global = 0
        for w in WIDTHS:
            for cfg in CONFIGS:
                cell_errors = 0
                cell_label = f"{cfg} w={w}"

                for s in SEEDS:
                    if (cfg, w, s) in done:
                        continue

                    # Halt: wall-clock check
                    elapsed_hr = (time.time() - t_global_start) / 3600
                    if elapsed_hr > HALT_WALL_HR:
                        print(
                            f"\nHALT: wall-clock {elapsed_hr:.2f} hr > {HALT_WALL_HR} hr limit. "
                            "Persisting and stopping.",
                            flush=True,
                        )
                        fh.flush()
                        return

                    try:
                        row = run_one(cfg, w, s)
                    except Exception as exc:
                        cell_errors += 1
                        msg = f"SKIP {cfg} w={w} seed={s}: {exc}"
                        print(f"  ERROR: {msg}", flush=True)
                        log_failure(msg)
                        if cell_errors > HALT_MAX_ERRORS_PER_CELL:
                            print(
                                f"\nHALT: {cell_errors} errors in cell {cell_label} "
                                f"> {HALT_MAX_ERRORS_PER_CELL} limit.",
                                flush=True,
                            )
                            fh.flush()
                            return
                        continue

                    # Sanity check J_sim
                    j = row["J_sim"]
                    if not (HALT_JSIM_LO <= j <= HALT_JSIM_HI):
                        msg = (
                            f"HALT: J_sim={j:.3f} out of range [{HALT_JSIM_LO}, "
                            f"{HALT_JSIM_HI}] at {cfg} w={w} seed={s}"
                        )
                        print(f"\n{msg}", flush=True)
                        log_failure(msg)
                        fh.flush()
                        return

                    # Write (only FIELDNAMES columns)
                    writer.writerow(
                        {k: row[k] for k in FIELDNAMES}
                    )
                    fh.flush()
                    done.add((cfg, w, s))
                    idx_global += 1

                    print(
                        f"  [{idx_global}] {cfg} w={w} seed={s} "
                        f"J={j:.3f} ped/s exited={row['_agents_exited']} "
                        f"evac={row['_evac_time']:.1f}s "
                        f"wall={row['wall_seconds']:.1f}s "
                        f"elapsed={(time.time()-t_global_start)/60:.1f}min",
                        flush=True,
                    )

                # Cell checkpoint
                print(
                    f"CHECKPOINT: {cell_label} complete "
                    f"({cell_errors} errors) "
                    f"elapsed={(time.time()-t_global_start)/60:.1f}min",
                    flush=True,
                )

    elapsed_hr = (time.time() - t_global_start) / 3600
    print(
        f"\nDone: {idx_global} new runs, "
        f"total elapsed {elapsed_hr:.2f} hr",
        flush=True,
    )


if __name__ == "__main__":
    main()
