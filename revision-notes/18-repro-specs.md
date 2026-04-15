# S18 repro specs extracted

## Environment
- Apple M1, 8 GB RAM, macOS 26.3.
- Python 3.13.12; numpy 2.4.4; scipy 1.17.1; shapely 2.1.2; pandas 2.3.x;
  statsmodels 0.14.x; lifelines 0.28.x; matplotlib 3.10.x.
- Single CPU core for serial sims; `multiprocessing.Pool(10)` for cross-bin
  calibration and ablation sweeps.
- Git commit hash for authoritative artefacts: [anonymized for review].

## Hyperparameters (source: config/params.yaml + sim/steering/*.py)
- Agent: v_0 = 1.34 m/s, r = 0.25 m, m = 80 kg, τ = 0.5 s (relaxation).
- SFM (textbook, fixed): A = 2000 N, B = 0.08 m, k = 1.2×10^5 kg/s^2, κ = 2.4×10^5 kg/(m·s).
- TTC (textbook, fixed): k_ttc = 1.5, τ_0 = 3.0 s.
- ORCA: τ_h = 5.0 s (horizon), τ_ORCA = 0.5 s (force conversion), R = 3.0 m (KDTree).
- Density gate: ρ_0 = 4.0 ped/m^2 (Fruin LoS-E), k = 2.0.
- Desired-force Weidmann (α-light fitted): γ* = 0.8327, ρ_max* = 5.977.
- Integrator: Euler, Δt = 0.01 s.

## Voronoi density
- shapely-based tessellation, clipped to scenario boundary.
- Mullick mirror-points reflect boundary agents across walls; 4 reflections per boundary agent.
- Per-agent density = 1 / (cell area).

## Geometry
- Corridor: 18 × 5 m, periodic x; 9–162 agents (FD calibration).
- Bottleneck: 10 × 10 m room, variable exit width w ∈ {0.8, 1.0, 1.2, 1.8, 2.4, 3.6} m,
  50–100 agents, wall thickness 0.1 m.
- Bidirectional: 20 × 3.6 m corridor, 100+100 counter-flow agents.
- Crossing: two 20 m perpendicular corridors, 3.6 m wide each, 100+100 agents.

## Calibration protocol (authoritative: results_new/calibration_alight_result.json)
- Protocol: α-light — Nelder-Mead, single-start, 2 free params (γ, ρ_max),
  A = 2000 N and B = 0.08 m held fixed at textbook.
- Bounds: γ ∈ [0.3, 3.0]; ρ_max ∈ [3.0, 7.0].
- Tolerances: xatol = 1e-3, fatol = 1e-4.
- Seeds per evaluation: 3 (seeds 42, 43, 44).
- FD bins: 10 densities in {0.5, ..., 5.0} ped/m^2.
- Corridor: 18 × 5 m, 300 warmup + 500 measure steps.
- Parallelism: multiprocessing.Pool across 10 bins (2.2× speedup).
- Convergence: user-authorised pkill at eval 53; simplex at seed-noise floor
  (evals 44–53 oscillated within ±0.003 m/s of best RMSE). Not formal
  xatol/fatol convergence. Reported as methodological limitation.
- Results: γ* = 0.8327, ρ_max* = 5.977, baseline RMSE = 0.23509 m/s,
  calibrated RMSE = 0.09945 m/s, reduction = 57.70 %.

## Statistical procedures
- NB GLM: statsmodels GLM with family=NegativeBinomial, alpha estimated via MoM.
  Link: log. Offset: run duration (for rate comparisons).
- Cox PH: lifelines.CoxPHFitter, event = deadlock resolution.
- LMM: statsmodels MixedLM, random intercept per seed.
- Holm–Šidák correction: applied within per-scenario comparison family.
- Exclusions: none (all seeds retained).

## Data
- FZJ unidirectional corridor: 4776 (density, speed) points aggregated
  from 952 individual pedestrian trajectories (PED1/PED2 identifiers,
  data/fzj/unidirectional/).
- FZJ bottleneck (held-out): flow rates per exit width (data/fzj/bottleneck/).

## Reproduction commands
- FD calibration: `python scripts/session06_phaseD_alight.py`
- Bottleneck evacuation: `python scripts/run_experiments.py --scenario bottleneck --seeds 42-66`
- C1+ε σ-sweep: `python scripts/sigma_sweep.py`
- Zonal decomposition: `python analysis/zonal_decomposition.py`
- Force diagnostic: `python new_experiments/force_magnitude_logging.py`
- External sim (JuPedSim): `python new_experiments/external_simulator/jupedsim_runner.py`
- Scaling: `python scripts/scaling_benchmark.py`

## Artefact provenance (key files)
| File | sha256 (16) | Consumer |
|---|---|---|
| results_new/sigma_sweep.csv | ce706dbf... | Fig. 4; §4.6 |
| results_new/sigma_sweep_stats.json | (computed) | §4.6 σ_50, CI |
| results_new/calibration_alight_result.json | (computed) | §4.2; Table 1 |
| results_new/gate_occupancy.csv | (computed) | §4.4 |
| results_new/scaling_C{1,4}.csv | (computed) | Fig. 6; §4.8 |
| results_analysis/zonal_collisions.csv | (computed) | Fig. 5; §4.5 |
| results_analysis/ood_validation.csv | (computed) | §4.3 |
| results_analysis/oracle_baseline.md | (computed) | §4.5 Oracle |
| results_analysis/statistical_reanalysis.csv | (computed) | §4.5, §4.6 |
| results/legacy/Bottleneck_w*_C{1,4}.csv | (copy from backup) | Table 5; Fig. 4 |
