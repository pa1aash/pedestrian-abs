"""Main simulation loop: neighbor search, force computation, integration, metrics."""

import numpy as np
from scipy.spatial import KDTree

from sim.core.agent import AgentState
from sim.core.helpers import clamp_speed
from sim.core.integrator import EulerIntegrator
from sim.core.world import World
from sim.steering.base import SteeringModel
from sim.steering.desired import compute_desired_force
from sim.steering.walls import WallForces


class Simulation:
    """Orchestrates the simulation loop.

    Each step: KDTree neighbor search -> density estimation -> force computation
    -> integration -> speed clamping -> goal deactivation -> metrics recording.

    Args:
        world: World geometry (walls, obstacles).
        agent_state: Initial agent state.
        steering_model: Steering model for force computation (None = desired only).
        integrator: Numerical integrator (default: EulerIntegrator).
        params: Dict of simulation parameters.
    """

    def __init__(
        self,
        world: World,
        agent_state: AgentState,
        steering_model: SteeringModel | None,
        integrator: EulerIntegrator | None = None,
        params: dict | None = None,
    ):
        self.world = world
        self.state = agent_state
        self.steering = steering_model
        self.integrator = integrator or EulerIntegrator()
        self.params = params or {
            "dt": 0.01,
            "neighbor_radius": 3.0,
            "max_time": 300.0,
            "goal_reached_dist": 0.5,
        }
        self.time = 0.0
        self.step_count = 0
        self.metrics_log: list[dict] = []
        self.periodic_length: float | None = None  # set for periodic corridors

    def step(self) -> dict:
        """Execute one simulation timestep.

        Returns:
            Dict with step metrics (time, n_active, mean_speed).
        """
        active = self.state.active_indices
        if len(active) == 0:
            return {"time": self.time, "n_active": 0}

        # 1. KDTree neighbor search (active agents only, self excluded)
        active_idx = self.state.active_indices
        active_pos = self.state.positions[active_idx]
        N_active = len(active_idx)
        # Map from local (active-only) index to global index
        neighbor_lists: list[list[int]] = [[] for _ in range(self.state.n)]

        if self.periodic_length is not None:
            L = self.periodic_length
            ghosts_r = active_pos.copy(); ghosts_r[:, 0] += L
            ghosts_l = active_pos.copy(); ghosts_l[:, 0] -= L
            extended = np.vstack([active_pos, ghosts_r, ghosts_l])
            tree = KDTree(extended)
            raw_nbs = tree.query_ball_point(active_pos, r=self.params["neighbor_radius"])
            for local_i, nbrs in enumerate(raw_nbs):
                global_i = active_idx[local_i]
                real = list({active_idx[j % N_active] for j in nbrs} - {global_i})
                neighbor_lists[global_i] = real
        else:
            tree = KDTree(active_pos)
            raw_nbs = tree.query_ball_point(active_pos, r=self.params["neighbor_radius"])
            for local_i, nbrs in enumerate(raw_nbs):
                global_i = active_idx[local_i]
                neighbor_lists[global_i] = [active_idx[j] for j in nbrs if active_idx[j] != global_i]

        # 2. Simple grid density: count / (pi * R^2)
        r = self.params["neighbor_radius"]
        area = np.pi * r * r
        densities = np.array(
            [len(n) / area for n in neighbor_lists], dtype=float
        )

        # 3. Compute forces
        if self.steering is not None:
            forces = self.steering.compute_forces(
                self.state, neighbor_lists, self.world.walls, densities
            )
        else:
            forces = compute_desired_force(
                self.state.positions,
                self.state.velocities,
                self.state.goals,
                self.state.desired_speeds,
                self.state.masses,
                self.state.taus,
                local_densities=densities,
            )
            if self.world.walls:
                forces += WallForces().compute_wall_forces(self.state, self.world.walls)

        # 4. Integrate
        dt = self.params["dt"]
        new_pos, new_vel = self.integrator.integrate(
            self.state.positions,
            self.state.velocities,
            forces,
            self.state.masses,
            dt,
        )

        # 5. Clamp speed to 2x desired
        max_speeds = 2.0 * self.state.desired_speeds
        new_vel = clamp_speed(new_vel, max_speeds)

        # 6. Update state
        self.state.positions = new_pos
        self.state.velocities = new_vel

        # 6b. Periodic boundary: wrap x-coordinate, keep goals ahead
        if self.periodic_length is not None:
            L = self.periodic_length
            self.state.positions[:, 0] = self.state.positions[:, 0] % L
            self.state.goals[:, 0] = self.state.positions[:, 0] + 5.0
            reached = np.array([], dtype=int)  # never deactivate
        else:
            # 7. Deactivate agents that reached their goal
            dists_to_goal = np.linalg.norm(
                self.state.goals - self.state.positions, axis=1
            )
            reached = np.where(
                self.state.active & (dists_to_goal < self.params["goal_reached_dist"])
            )[0]
            self.state.deactivate(reached)

        # 8. Record metrics
        self.time += dt
        self.step_count += 1
        active_now = self.state.active_indices
        n_exited_this_step = len(reached)

        if len(active_now) > 0:
            mean_speed = float(
                np.mean(np.linalg.norm(self.state.velocities[active_now], axis=1))
            )
            max_density = float(np.max(densities[active_now]))
        else:
            mean_speed = 0.0
            max_density = 0.0

        # Collision count: pairs with distance < sum of radii
        collision_count = 0
        for i in active_now:
            for j in neighbor_lists[i]:
                if j > i and self.state.active[j]:
                    d = np.linalg.norm(self.state.positions[i] - self.state.positions[j])
                    if d < self.state.radii[i] + self.state.radii[j]:
                        collision_count += 1

        metrics = {
            "time": self.time,
            "n_active": self.state.n_active,
            "mean_speed": mean_speed,
            "max_density": max_density,
            "collision_count": collision_count,
            "agents_exited_step": n_exited_this_step,
        }
        self.metrics_log.append(metrics)
        return metrics

    def inject_agents(self, n: int, seed: int) -> None:
        """Inject new agents at the left boundary of the corridor.

        Args:
            n: Number of agents to inject.
            seed: Random seed for placement.
        """
        new = AgentState.create(
            n,
            spawn_area=(0.3, 2.0, 0.3, 3.3),
            goals=np.array([26.0, 1.8]),
            seed=seed,
        )
        # Append to existing state
        s = self.state
        s.positions = np.vstack([s.positions, new.positions])
        s.velocities = np.vstack([s.velocities, new.velocities])
        s.goals = np.vstack([s.goals, new.goals])
        s.radii = np.concatenate([s.radii, new.radii])
        s.desired_speeds = np.concatenate([s.desired_speeds, new.desired_speeds])
        s.masses = np.concatenate([s.masses, new.masses])
        s.taus = np.concatenate([s.taus, new.taus])
        s.active = np.concatenate([s.active, new.active])

    def run(
        self, max_steps: int = 10000, max_time: float | None = None
    ) -> dict:
        """Run the simulation until completion.

        Args:
            max_steps: Maximum number of timesteps.
            max_time: Maximum simulation time in seconds.

        Returns:
            Summary dict with n_steps, time, agents_exited, mean_speed.
        """
        if max_time is None:
            max_time = self.params.get("max_time", 300.0)

        # Check if scenario uses continuous injection
        scenario = getattr(self, '_scenario', None)
        inj_rate = getattr(scenario, 'injection_rate', 0) if scenario else 0
        inj_accum = 0.0
        inj_seed_counter = 10000

        while (
            self.step_count < max_steps
            and self.time < max_time
            and self.state.n_active > 0
        ):
            # Inject agents if configured
            if inj_rate > 0:
                dt = self.params.get("dt", 0.01)
                inj_accum += inj_rate * dt
                if inj_accum >= 1.0:
                    n_inject = int(inj_accum)
                    inj_accum -= n_inject
                    self.inject_agents(n_inject, seed=inj_seed_counter)
                    inj_seed_counter += 1

            self.step()

            # Deactivate agents past corridor exit
            if inj_rate > 0:
                past_exit = np.where(
                    self.state.active & (self.state.positions[:, 0] > 24.5)
                )[0]
                self.state.deactivate(past_exit)

        return self._compile_results()

    @classmethod
    def from_scenario(
        cls,
        scenario,
        config_name: str = "C1",
        seed: int = 42,
        param_overrides: dict | None = None,
    ) -> "Simulation":
        """Build a Simulation from a scenario object and config name.

        Args:
            scenario: Scenario with a build(seed) method returning (World, AgentState).
            config_name: One of C1-C4.
            seed: Random seed.
            param_overrides: Optional dict to override params.yaml values.

        Returns:
            Configured Simulation instance.
        """
        import yaml

        from sim.experiments.configs import get_config, get_param_overrides
        from sim.steering.hybrid import HybridSteeringModel

        world, agent_state = scenario.build(seed=seed)
        with open("config/params.yaml") as f:
            params = yaml.safe_load(f)
        flat: dict = {}
        for v in params.values():
            if isinstance(v, dict):
                flat.update(v)
        # Apply D-config overrides first, then explicit overrides
        flat.update(get_param_overrides(config_name))
        if param_overrides:
            flat.update(param_overrides)
        config = get_config(config_name)
        steering = HybridSteeringModel(config, flat)
        sim = cls(world, agent_state, steering, EulerIntegrator(), flat)
        sim._scenario = scenario
        sim.periodic_length = getattr(scenario, 'periodic_length', None)
        return sim

    def _compile_results(self) -> dict:
        """Compile summary statistics from the simulation run.

        Returns:
            Dict with all metrics from CLAUDE.md Section 19.
        """
        if not self.metrics_log:
            return {
                "n_steps": 0, "evacuation_time": 0.0, "mean_speed": 0.0,
                "max_density": 0.0, "collision_count": 0, "flow_rate": 0.0,
                "agents_exited": 0, "mean_risk": 0.0, "max_risk": 0.0,
                "time_above_critical": 0.0,
            }

        agents_exited = self.state.n - self.state.n_active
        evac_time = self.time if self.state.n_active == 0 else float('inf')

        mean_speed = float(np.mean([m["mean_speed"] for m in self.metrics_log]))
        max_density = float(np.max([m["max_density"] for m in self.metrics_log]))
        total_collisions = int(np.sum([m["collision_count"] for m in self.metrics_log]))

        dt = self.params.get("dt", 0.01)
        flow_rate = agents_exited / max(self.time, dt)

        # Risk and time above critical (density > 5.5)
        critical_threshold = self.params.get("rho_crit", 5.5)
        time_above_critical = sum(
            dt for m in self.metrics_log if m["max_density"] > critical_threshold
        )

        return {
            "n_steps": self.step_count,
            "evacuation_time": evac_time,
            "mean_speed": mean_speed,
            "max_density": max_density,
            "collision_count": total_collisions,
            "flow_rate": flow_rate,
            "agents_exited": agents_exited,
            "mean_risk": 0.0,  # populated by runner when density estimators used
            "max_risk": 0.0,
            "time_above_critical": time_above_critical,
        }
