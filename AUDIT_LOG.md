# Audit Log

## Phase 1 — Foundation
- **Date:** 2026-04-02
- **Built:** pyproject.toml, .gitignore, config/params.yaml, scripts/audit.sh, sim/core/helpers.py (60 lines), sim/core/agent.py (113 lines), sim/core/world.py (139 lines), tests/conftest.py, tests/test_agent.py, tests/test_world.py, 38 stub files (empty __init__.py + module placeholders), 13 empty test files
- **Tests:** 12 new, 12 total, 12 passing
- **Gates:** pip install ✓, all imports ✓, pytest 12/12 ✓, audit.sh ✓
- **Issues:** pyproject.toml build-backend corrected from `setuptools.backends._legacy:_Backend` to `setuptools.build_meta`

## Phase 2 — Core Loop
- **Date:** 2026-04-02
- **Built:** sim/core/integrator.py (90 lines), sim/steering/base.py (33 lines), sim/steering/desired.py (37 lines), sim/core/simulation.py (172 lines), tests/test_integrator.py, tests/test_desired.py, tests/test_simulation.py
- **Tests:** 20 new, 32 total, 32 passing
- **Gates:** all imports OK, pytest 32/32 ✓, audit.sh ✓
- **Issues:** none

## Phase 3 — SFM + Wall Forces
- **Date:** 2026-04-02
- **Built:** sim/steering/sfm.py (92 lines), sim/steering/walls.py (94 lines), tests/test_sfm.py, tests/test_walls.py
- **Tests:** 15 new, 47 total, 47 passing
- **Gates:** all imports OK, pytest 47/47 ✓, physics sanity (30 agents corridor 300 steps, mean_speed=1.10) ✓, audit.sh ✓
- **Issues:** none

## Phase 4 — TTC Force
- **Date:** 2026-04-02
- **Built:** sim/steering/ttc.py (99 lines), tests/test_ttc.py
- **Tests:** 6 new, 53 total, 53 passing
- **Gates:** analytical τ=0.75 ✓, pytest 53/53 ✓, audit.sh ✓
- **Issues:** none

## Phase 5 — ORCA
- **Date:** 2026-04-02
- **Built:** sim/steering/orca.py (341 lines), tests/test_orca.py
- **Tests:** 5 new, 58 total, 58 passing
- **Gates:** incremental LP ✓, scipy fallback ✓, four-agent crossing min_dist>0.3 ✓, pytest 58/58 ✓, audit.sh ✓
- **Issues:** severe overlaps produce infeasible LP constraints (by design — SFM body forces handle contact separation)

## Phase 6 — Assembly (Crush + Hybrid + Smoke Tests) — **ENGINE COMPLETE**
- **Date:** 2026-04-02
- **Built:** sim/steering/crush.py (81 lines), sim/steering/hybrid.py (157 lines), sim/experiments/configs.py (34 lines), sim/core/simulation.py updated (+37 lines from_scenario), tests/test_crush.py, tests/test_hybrid.py, tests/test_smoke.py
- **Tests:** 12 new, 70 total, 70 passing
- **Gates:** C1-C4 all run ✓, evacuation C4 50 agents exits ✓, single-agent goal ✓, head-on deflection ✓, sigmoid weights ✓, pytest 70/70 ✓, audit.sh ✓
- **Issues:** occasional force clamping warnings from TTC at high density (handled by check_forces)

## Phase 7 — Density + Risk + Scenarios
- **Date:** 2026-04-02
- **Built:** sim/density/base.py (22), grid.py (51), voronoi.py (107), kde.py (37), risk.py (87), sim/scenarios/base.py (38), corridor.py (52), bottleneck.py (50), bidirectional.py (70), crossing.py (81), funnel.py (50) — 645 new lines
- **Tests:** 22 new, 92 total, 92 passing
- **Gates:** all density estimators ✓, risk metric ✓, all 5 scenarios build+run ✓, from_scenario ✓, pytest 92/92 ✓
- **Issues:** fixed np.ptp() removal in NumPy 2.0 (voronoi.py)

## Phase 8 — Experiment Pipeline — **PIPELINE COMPLETE**
- **Date:** 2026-04-02
- **Built:** sim/experiments/runner.py (103), analysis.py (71), sim/optimization/barrier.py (61), optimizer.py (157), sim/viz/ 7 modules (382 total), sim/data/ 2 modules (125 total), scripts/ 2 CLIs (127 total), sim/core/simulation.py extended metrics — 1026 new lines
- **Tests:** 92 total, 92 passing (simulation.py _compile_results updated for full metrics)
- **Gates:** CSV output ✓ (bottleneck C1 2 reps, evac=53.5s), optimizer ✓ (nelder-mead 5 evals), pytest 92/92 ✓, audit.sh ✓
- **Issues:** none

## Phase 9 — Data Loading + Calibration
- **Date:** 2026-04-02
- **Built:** sim/data/loader.py rewritten (98 lines), sim/data/fundamental_diagram.py rewritten (30 lines), scripts/calibrate.py (53 lines)
- **Tests:** 92 total, 92 passing
- **Gates:** FZJ data loaded ✓ (2.6M rows, 952 peds, mean speed=0.82 m/s), empirical FD extracted ✓ (4436 frames, density [0.19, 11.20]), Weidmann curve ✓, calibrate.py produces CSV+PDF ✓, pytest 92/92 ✓
- **Issues:** fixed FZJ column order (ped_id frame_id x y z, not frame_id ped_id x y), fixed fps=16 (not 25), fixed add_velocities to use actual frame gaps
