# Existing Data Inventory — `results/`

**Date:** 2026-04-11
**Layout:** Flat directory of CSV / JSON files. **No per-seed subdirectories.** The CLAUDE.md describes an idealised layout (`results/bottleneck/C1/w0.8/seed0/`); the actual layout is one CSV per `(scenario, config)` combination, with seeds as rows.

**Critical finding:** every CSV holds **scalar per-seed summary metrics only**. Trajectories, per-collision records, and per-agent force breakdowns are **never persisted** by the existing simulation pipeline.

---

## A. What is saved per simulation run

`sim/core/simulation.py` keeps an in-memory `metrics_log` of per-step scalars (`time`, `n_active`, `mean_speed`, `max_density`, `collision_count`, `agents_exited_step`). At the end of `run()`, `_compile_results()` reduces this to **eleven scalars** that get one row in the CSV:

| Column | Meaning |
|---|---|
| `scenario` | Class name (e.g. `BottleneckScenario`) |
| `config` | C1 / C2 / C3 / C4 (or D1–D4 for crush) |
| `seed` | Integer (range 42–66 for n=25 runs) |
| `wall_time_s` | Wall-clock for the run |
| `n_steps` | Total simulation steps |
| `evacuation_time` | Time when last agent exited (`inf` if not all out) |
| `mean_speed` | Mean of per-step mean speeds |
| `max_density` | Max of per-step max grid density |
| `collision_count` | **Scalar sum** over all timesteps (no per-collision data) |
| `flow_rate` | `agents_exited / time` |
| `agents_exited` | Final count |
| `mean_risk`, `max_risk`, `time_above_critical` | Risk metrics (mostly 0 — populated only when Voronoi estimator was used) |

**Per-step metrics_log is discarded after `_compile_results` returns**, so even the per-step `collision_count` is not retrievable.

The only special-case CSV is `fd_C*.csv` (corridor fundamental diagram), which has a different schema: `config, n_agents, rep, density, speed`.

---

## B. Required-artefact checklist

| Artefact required by R2/R3 | Status | Where it would live | Notes |
|---|---|---|---|
| Per-timestep agent positions (trajectories) | **MISSING for all experiments** | nowhere | `metrics_log` is in-memory and is reduced to scalars before write |
| Per-collision records `(t, i, j, x_i, y_i, x_j, y_j)` | **MISSING for all experiments** | nowhere | only the scalar total `collision_count` is summed |
| Per-collision records `(t, x, y)` (lighter form) | **MISSING for all experiments** | nowhere | same as above |
| Per-agent force breakdowns `\|F_des\|, \|F_SFM\|, \|F_TTC\|, \|F_ORCA\|` | **MISSING for all experiments** | nowhere | forces are computed and integrated, never logged |
| Random seeds | **PRESENT** | `seed` column in every CSV | range 42–66 for n=25, paired across configs |

**Implication for R2 / R3:**
- **R2.1 Zonal decomposition** → requires collision (x, y). **Case C: missing data**, requires re-run of C1, C4 at w∈{0.8, 1.0} with collision-location logging on.
- **R2.2 TTC distributions** → requires per-timestep positions. **Missing**, requires the same re-run (TTC can be computed post-hoc from trajectories).
- **R2.5 Arch lifetime** → requires C1 trajectories at w=0.8m to compute the "≥3 agents within 0.5 m of exit centerline, no exit crossing for ≥2 s" criterion. **Missing**, would also be covered by the same re-run if positions are logged.
- **R3.2 Force-magnitude logging** → already known to require new runs.

**Good news:** seeds are deterministic across configs (42, 43, 44, … always). A targeted re-run of `C1, C4` × `w0.8, w1.0` × seeds 42–66 with two new opt-in flags (`log_positions=True`, `log_collisions=True`) gives R2.1 + R2.2 + R2.5 in a single compute pass without invalidating any existing CSV (the new runs go to `results_new/`, the existing CSVs in `results/` stay untouched).

---

## C. Inventory of existing experiments

### C.1 Bottleneck (parametric width sweep) — primary ablation source

Geometry: `BottleneckScenario`, 50 agents, 60 s simulation window unless noted.

| File | Width (m) | Config | n_seeds | Seed range | Notes |
|---|---|---|---|---|---|
| `Bottleneck_w1.0_C1.csv` | 1.0 | C1 | 25 | 42–66 | normal evacuation |
| `Bottleneck_w1.0_C2.csv` | 1.0 | C2 | 25 | 42–66 |  |
| `Bottleneck_w1.0_C3.csv` | 1.0 | C3 | 25 | 42–66 |  |
| `Bottleneck_w1.0_C4.csv` | 1.0 | C4 | 25 | 42–66 |  |
| `Bottleneck_w1.2_{C1..C4}.csv` | 1.2 | each | 25 | 42–66 |  |
| `Bottleneck_w1.8_{C1..C4}.csv` | 1.8 | each | 25 | 42–66 |  |
| `Bottleneck_w2.4_{C1..C4}.csv` | 2.4 | each | 25 | 42–66 |  |
| `Bottleneck_w3.6_{C1..C4}.csv` | 3.6 | each | 25 | 42–66 |  |

### C.2 Bottleneck w=0.8 m (deadlock-prone) — three variants

| File | Config | n_seeds | sim time | Use |
|---|---|---|---|---|
| `Bottleneck_w0.8_C{1..4}.csv` | each | **5** | default 60 s | early stub data, `evacuation_time = inf` for all |
| `Bottleneck_w0.8_600s_C{1..4}.csv` | each | **25** | 600 s | **canonical deadlock data**: C1 1/25, C2 0/25, C3 13/25, C4 14/25 |
| `Bottleneck_w0.8_long_C{1,4}.csv` | C1, C4 | 5 | longer | exploratory, partial coverage |

`Bottleneck_w0.8_600s_*` is the file the deadlock subsection in the current paper relies on.

### C.3 Crossing — `CrossingScenario` 200 agents, 60 s

| File | Config | n_seeds | Seed range |
|---|---|---|---|
| `CrossingScenario_C{1..4}.csv` | each | 25 | 42–66 |

### C.4 Bidirectional — `BidirectionalScenario` 200 agents, 60 s

| File | Config | n_seeds | Seed range |
|---|---|---|---|
| `BidirectionalScenario_C{1..4}.csv` | each | 25 | 42–66 |

### C.5 Plain `BottleneckScenario` (legacy default-width)

| File | Config | n_seeds |
|---|---|---|
| `BottleneckScenario_C{1..4}.csv` | each | **5** |

50 agents, default 1.0 m exit. Stub-quality, n=5; superseded by `Bottleneck_w1.0_*.csv`. Can be ignored or archived.

### C.6 Fundamental diagram (corridor)

| File | Config | rows |
|---|---|---|
| `fd_C1.csv` | C1 | 360 |
| `fd_C2.csv` | C2 | 360 |
| `fd_C3.csv` | C3 | 300 |
| `fd_C4.csv` | C4 | 300 |

Schema: `config, n_agents, rep, density, speed`. 12 density bins × 30 reps for C1/C2 (n=30 each) and 12 × 25 for C3/C4. **No trajectories**, just steady-state mean speeds.

`empirical_fd.csv`: 4776 FZJ (frame_id, mean_density, mean_speed) bins from `data/fzj/unidirectional/`.

`calibration.json`: full Nelder-Mead history (31 evals) plus pre/post RMSE (0.230 → 0.091) and the calibrated `(γ=0.888, ρ_max=5.36, A=1920, B=0.112)`.

### C.7 Sigmoid threshold sensitivity (post-hoc, paper §4.4)

| File | rows | Schema |
|---|---|---|
| `sigmoid_sensitivity.csv` | 22 | early stub |
| `sigmoid_sensitivity_full.csv` | **540** | 18 cells × n=30; `centre, slope, rho_orca_fade, rho_crit, k_orca_fade, k_crit, width, n_agents, seed, evacuation_time, mean_speed, collision_count, agents_exited, wall_time_s` |

The full file is the canonical sensitivity sweep (3 centres × 2 slopes × 3 widths × 30 seeds). Scalar metrics only.

### C.8 Scaling

| File | Config | rows | Schema |
|---|---|---|---|
| `scaling_C1.csv` | C1 | 5 | `n_agents, ms_per_step, config` for `{50, 100, 200, 500, 1000}` |
| `scaling_C4.csv` | C4 | 4 | `{50, 100, 250, 500}` |
| `scaling_combined.csv` | both | 9 | merged |

### C.9 ARCHIVED — crush regime (CLAUDE.md §3.3 / §4.6 cut)

| File | Config | n_seeds |
|---|---|---|
| `FunnelScenario_D{1..4}.csv` | each | 25 |
| `CrushRoomScenario_D{1..4}.csv` | each | 25 |

D1 = no crush; D2 ρ_crit=5.0; D3 ρ_crit=5.5; D4 ρ_crit=7.0. Scalar metrics only. **Per CLAUDE.md, these stay in `results/` for reproducibility but are not referenced from the new paper.**

### C.10 ARCHIVED — barrier optimisation (CLAUDE.md §3.4 / §4.7 cut)

| File | Format |
|---|---|
| `optimizer_C1_history.json` | list of 30 `{params, cost}` |
| `optimizer_C4_history.json` | list of 30 `{params, cost}` |
| `optimizer_history.json` | list of 30 (older) |

No agent-level data, just optimiser convergence traces. Cut from paper.

### C.11 Auxiliary

| File | Notes |
|---|---|
| `bottleneck_validation.csv` | 5 rows: `width_m, flow_rate_empirical, n_peds, duration_s, flow_rate_sim, flow_rate_std`. Held-out FZJ bottleneck validation; showed −27 to −43% sim vs empirical mismatch. |
| `experiment_log.txt` | 5,289 lines; mostly stdout/stderr from runs (force-clamp warnings dominate). No structured metrics. |

---

## D. Summary of what is and isn't possible without re-runs

### Possible on existing scalar CSVs (no compute required)

- **R2.3 Statistical reanalysis**: NB GLM on `collision_count`, Cox PH on deadlock events (event = `evacuation_time != inf`), LMM on `mean_speed` / `agents_exited`, Holm–Šidák correction. All inputs are present in existing CSVs.
- **R2.4 Oracle baseline**: per-scenario best single-paradigm. Already computable from the existing scalar metrics.
- All paper rewrites in R1 and R4 (no compute).

### Requires new compute (Case C — collision-location + position logging missing)

- **R2.1 Zonal decomposition** — needs `(t, x, y)` collision coordinates
- **R2.2 TTC distributions** — needs per-timestep positions
- **R2.5 Arch lifetime** — needs per-timestep positions for C1 w=0.8 m

→ **Single targeted re-run** would cover all three: `C1, C4` × `w∈{0.8, 1.0}` × seeds 42–66, with two opt-in logging flags (`log_positions=True`, `log_collisions=True`) added to `sim/core/simulation.py` behind a default-off gate (per CLAUDE.md rule §11.13). Outputs go to `results_new/`, not `results/`. Estimated compute: roughly half a day (4 cells × 25 seeds × ~1–8 min/seed depending on config and width).

- **R3.1 C1+ε control** — already known to require new runs (paired seeds with existing C1 0.8 m, with σ=0.05 m/s velocity perturbation). ~2 hr compute.
- **R3.2 Force-magnitude logging** — already known to require new runs. C4 at w=1.0m, n=5. ~30 min compute.
- **R3.3 External simulator comparison** — requires JuPedSim / Vadere / RVO2 runs. Time depends on tool choice.

### Not blocking but worth noting

- **Paired-seed analysis is intact**: every n=25 file uses seeds 42–66, so C1↔C4↔C1+ε comparisons can use paired statistics.
- **Sigmoid sensitivity 540 runs**: already exists, can be reused for the §4.4 robustness paragraph; no new compute needed.
- **n=5 stub files** (`BottleneckScenario_C*.csv`, `Bottleneck_w0.8_C*.csv`, `*_long_*.csv`): can be ignored in favour of the n=25 superseding files. These should NOT be deleted (read-only rule), just not referenced.
