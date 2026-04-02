#!/usr/bin/env python
"""CLI for running experiments."""

import argparse
import sys

from sim.experiments.runner import ExperimentRunner
from sim.scenarios.corridor import CorridorScenario
from sim.scenarios.bottleneck import BottleneckScenario
from sim.scenarios.bidirectional import BidirectionalScenario
from sim.scenarios.crossing import CrossingScenario
from sim.scenarios.funnel import FunnelScenario

SCENARIO_MAP = {
    "fd": (CorridorScenario, {"n_agents": 50}),
    "bottleneck": (BottleneckScenario, {"n_agents": 100}),
    "bidirectional": (BidirectionalScenario, {"n_per_direction": 75}),
    "crossing": (CrossingScenario, {"n_per_stream": 50}),
    "crush": (FunnelScenario, {"n_agents": 400}),
}


def main():
    parser = argparse.ArgumentParser(description="Run CrowdTwin experiments")
    parser.add_argument(
        "--experiment", required=True,
        choices=["fd", "bottleneck", "bidirectional", "crossing", "crush", "optimize", "scaling", "all"],
    )
    parser.add_argument("--configs", default="C1,C2,C3,C4")
    parser.add_argument("--replications", type=int, default=30)
    parser.add_argument("--output", default="results/")
    parser.add_argument("--max-time", type=float, default=120.0)
    args = parser.parse_args()

    runner = ExperimentRunner(args.output)
    configs = args.configs.split(",")

    if args.experiment == "scaling":
        for cfg in configs:
            print(f"Scaling test: {cfg}")
            df = runner.run_scaling(cfg)
            print(df.to_string(index=False))
        return

    if args.experiment == "optimize":
        from sim.optimization.optimizer import BarrierOptimizer
        opt = BarrierOptimizer(BottleneckScenario, configs[0], n_agents=100, n_reps=3, max_time=args.max_time)
        result = opt.optimize("nelder-mead", max_evals=50)
        print(f"Best cost: {result['cost']:.2f}, params: {result['params']}")
        return

    if args.experiment == "all":
        experiments = list(SCENARIO_MAP.keys())
    else:
        experiments = [args.experiment]

    for exp_name in experiments:
        scenario_class, kwargs = SCENARIO_MAP[exp_name]
        for cfg in configs:
            print(f"Running {exp_name} / {cfg} x {args.replications} reps...")
            df = runner.run(
                scenario_class, cfg,
                n_replications=args.replications,
                max_time=args.max_time,
                **kwargs,
            )
            print(f"  -> {len(df)} rows, mean evac_time={df['evacuation_time'].mean():.2f}s")


if __name__ == "__main__":
    main()
