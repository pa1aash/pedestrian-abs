"""S14: cProfile one C4 run at 200 agents for 10s of sim time.

Output:
  revision-notes/14-profile.txt  — full cProfile dump (cumtime, sorted)
  revision-notes/14-profile-raw.prof — binary stats for re-analysis
"""
import cProfile
import os
import pstats
import sys
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
os.chdir(_PROJECT_ROOT)

from sim.core.simulation import Simulation
from sim.scenarios.bottleneck import BottleneckScenario

SIM_DURATION_S = 10.0
N_AGENTS = 200
CONFIG = "C4"
SEED = 42
OUT_TXT = os.path.join(_PROJECT_ROOT, "revision-notes", "14-profile.txt")
OUT_BIN = os.path.join(_PROJECT_ROOT, "revision-notes", "14-profile-raw.prof")


def run():
    scenario = BottleneckScenario(n_agents=N_AGENTS, exit_width=3.6)
    sim = Simulation.from_scenario(scenario, CONFIG, seed=SEED)
    sim.run(max_steps=200_000, max_time=SIM_DURATION_S)


def main():
    t0 = time.perf_counter()
    pr = cProfile.Profile()
    pr.enable()
    run()
    pr.disable()
    wall = time.perf_counter() - t0
    pr.dump_stats(OUT_BIN)

    with open(OUT_TXT, "w") as fh:
        fh.write(f"cProfile: {CONFIG} n={N_AGENTS} duration={SIM_DURATION_S}s seed={SEED}\n")
        fh.write(f"Wall: {wall:.2f} s\n\n")
        st = pstats.Stats(pr, stream=fh)
        st.strip_dirs().sort_stats("cumulative").print_stats(60)
        fh.write("\n\n=== BY TOTAL TIME ===\n")
        st2 = pstats.Stats(pr, stream=fh)
        st2.strip_dirs().sort_stats("tottime").print_stats(40)
    print(f"DONE wall={wall:.2f}s -> {OUT_TXT}", flush=True)


if __name__ == "__main__":
    main()
