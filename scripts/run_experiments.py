#!/usr/bin/env python
"""CLI for running experiments."""

import argparse
import json
import os

from sim.experiments.configs import BOTTLENECK_WIDTHS, CRUSH_CONFIGS
from sim.experiments.runner import ExperimentRunner
from sim.scenarios.bidirectional import BidirectionalScenario
from sim.scenarios.bottleneck import BottleneckScenario
from sim.scenarios.corridor import CorridorScenario
from sim.scenarios.crossing import CrossingScenario
from sim.scenarios.funnel import FunnelScenario


def main():
    parser = argparse.ArgumentParser(description="Run CrowdTwin experiments")
    parser.add_argument(
        "--experiment", required=True,
        choices=["fd", "bottleneck", "bidirectional", "crossing",
                 "crush", "optimize", "scaling", "all"],
    )
    parser.add_argument("--configs", default="C1,C2,C3,C4")
    parser.add_argument("--replications", type=int, default=5)
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
        opt = BarrierOptimizer(
            BottleneckScenario, configs[0],
            n_agents=50, n_reps=2, max_time=args.max_time,
        )
        result = opt.optimize("nelder-mead", max_evals=20)
        print(f"Best cost: {result['cost']:.2f}, params: {result['params']}")
        # Save history
        with open(os.path.join(args.output, "optimizer_history.json"), "w") as f:
            json.dump(result["history"], f)
        return

    experiments = {
        "fd": lambda: _run_fd(runner, configs, args),
        "bottleneck": lambda: _run_bottleneck(runner, configs, args),
        "bidirectional": lambda: _run_standard(runner, BidirectionalScenario, configs, args, n_per_direction=20),
        "crossing": lambda: _run_standard(runner, CrossingScenario, configs, args, n_per_stream=20),
        "crush": lambda: _run_crush(runner, args),
    }

    if args.experiment == "all":
        for name, fn in experiments.items():
            print(f"\n=== {name.upper()} ===")
            fn()
    else:
        experiments[args.experiment]()


def _run_fd(runner, configs, args):
    """Family A: Fundamental diagram with corridor at various densities."""
    for n_agents in [20, 40, 60]:
        for cfg in configs:
            print(f"FD / {cfg} / n={n_agents} x {args.replications} reps...")
            df = runner.run(
                CorridorScenario, cfg,
                n_replications=args.replications,
                max_time=args.max_time,
                n_agents=n_agents,
            )
            print(f"  -> {len(df)} rows, mean_speed={df['mean_speed'].mean():.2f}")


def _run_bottleneck(runner, configs, args):
    """Family B: Bottleneck at 6 exit widths."""
    for width in BOTTLENECK_WIDTHS:
        for cfg in configs:
            print(f"Bottleneck / {cfg} / width={width}m x {args.replications} reps...")
            df = runner.run(
                BottleneckScenario, cfg,
                n_replications=args.replications,
                max_time=args.max_time,
                n_agents=50,
                exit_width=width,
            )
            # Custom filename with width
            fname = f"Bottleneck_w{width}_{cfg}.csv"
            df.to_csv(os.path.join(args.output, fname), index=False)
            print(f"  -> {len(df)} rows, evac={df['evacuation_time'].mean():.1f}s")


def _run_standard(runner, scenario_class, configs, args, **kwargs):
    """Run a standard scenario across configs."""
    for cfg in configs:
        print(f"{scenario_class.__name__} / {cfg} x {args.replications} reps...")
        df = runner.run(
            scenario_class, cfg,
            n_replications=args.replications,
            max_time=args.max_time,
            **kwargs,
        )
        print(f"  -> {len(df)} rows, evac={df['evacuation_time'].mean():.1f}s")


def _run_crush(runner, args):
    """Family D: Crush threshold variations using D-configs on funnel."""
    d_configs = list(CRUSH_CONFIGS.keys())
    for cfg in d_configs:
        print(f"Crush / {cfg} x {args.replications} reps...")
        df = runner.run(
            FunnelScenario, cfg,
            n_replications=args.replications,
            max_time=args.max_time,
            n_agents=100,
        )
        print(f"  -> {len(df)} rows, max_density={df['max_density'].mean():.2f}")


if __name__ == "__main__":
    main()
