# CLAUDE.md — CrowdSim Ablation Study

> **READ THIS ENTIRE FILE BEFORE WRITING ANY CODE.**
> Single source of truth for architecture, equations, algorithms, parameters, and conventions.

---

## 0. PROJECT IDENTITY

**What:** Diagnostic ablation study of SFM, TTC, and ORCA pedestrian steering paradigms, with a density-adaptive convex blend as a mitigation. Built as a NumPy-vectorized Python simulation.

**Thesis:** Every steering paradigm fails in some regime. We characterise *where* and *why* each fails, and show that density-adaptive blending mitigates each failure mode without requiring scenario classification at runtime.

**Why this framing:** A previous version of this project framed the work as a "Hybrid Crowd Simulation Digital Twin" with five contributions (hybrid steering, calibration, density estimation, crush regime, barrier optimization). External review identified that (a) the DT framing was aspirational and unimplemented, (b) the FD calibration was decoupled from steering choice and therefore did not validate the hybrid, (c) the crush regime's collision-reduction result was a mechanical artefact of spring stiffening, (d) the barrier optimization was a negative result from a bad initial guess, and (e) the most novel content — TTC alone *worsening* deadlocks (0/25 vs 1/25 for plain SFM), ORCA alone *reducing* counterflow throughput — was buried. The pivot is to make those negative findings the headline.

**Hard constraint — reuse existing data.** Existing simulation results are reused. No re-running of experiments at higher n or for cosmetic consistency. New simulations are permitted only when generating data that doesn't exist yet (currently: C1+ε control, force-magnitude diagnostic, external simulator comparison, and possibly collision-location logging if not already saved).

**Cut from scope:** Digital Twin framing, crush regime as a contribution (Section 3.3 and 4.6 of the old paper), barrier optimization (Section 3.4 and 4.7), composite risk metric (Eq. 6), KDE and grid density as contributions (Voronoi-only is retained for the final paper).

**Target:** SIMULTECH 2026 regular paper, 12 pages SciTePress, deadline April 16 2026. Double-blind.

**Stack:** Python 3.11+, NumPy-vectorized, all models from scratch. No third-party simulation libraries except for the external comparison baseline (JuPedSim → Vadere → RVO2, in that fallback order).

**Performance:** 1000 agents at ≥30 steps/sec (dt=0.01s → ≤33ms/step) for the SFM-only path. ORCA path is acknowledged as ~45× slower; this is reported as a limitation, not optimised.

---

## 1. REPO LAYOUT

Existing: `paper/` (LaTeX), `data/` (FZJ + ETH-UCY), `sim/` (existing simulation code), `results/` (existing experiment outputs).

```
pedestrian-abs/
├── CLAUDE.md                          # THIS FILE
├── STATUS.json                        # State tracker
├── AUDIT_LOG.md                       # Build log
├── inventory.md                       # NEW: existing-data inventory (Step 1)
├── pyproject.toml
├── .gitignore
├── config/
│   └── params.yaml
├── scripts/
│   ├── audit.sh
│   ├── run_experiments.py             # EXISTING — do not modify default behaviour
│   └── generate_figures.py            # EXISTING — extended in Step 5
├── sim/                               # EXISTING simulation code, mostly preserved
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── helpers.py                 # check_forces, safe_normalize, clamp_speed
│   │   ├── agent.py                   # AgentState dataclass
│   │   ├── world.py                   # Wall, Obstacle, World, geometry utils
│   │   ├── simulation.py              # main loop + metrics; collision-location logging flag
│   │   └── integrator.py              # Euler / RK4
│   ├── steering/
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract SteeringModel
│   │   ├── desired.py                 # Goal-seeking force
│   │   ├── sfm.py                     # Social Force Model
│   │   ├── ttc.py                     # Time-to-Collision
│   │   ├── orca.py                    # ORCA velocity optimization
│   │   ├── walls.py                   # Wall forces
│   │   ├── crush.py                   # ARCHIVED — kept for reproducibility, not in paper
│   │   └── hybrid.py                  # Density-weighted blend; document the actual eq honestly
│   ├── density/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── grid.py                    # internal use only, not a paper contribution
│   │   ├── voronoi.py                 # the only density estimator the paper retains
│   │   ├── kde.py                     # internal use only, not a paper contribution
│   │   └── risk.py                    # ARCHIVED — composite risk dropped
│   ├── optimization/                  # ARCHIVED — barrier optimisation dropped
│   │   ├── __init__.py
│   │   ├── barrier.py
│   │   └── optimizer.py
│   ├── scenarios/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── corridor.py                # 10x3.6m periodic for FD
│   │   ├── bottleneck.py              # 10x10m room + variable exit
│   │   ├── bidirectional.py           # 20x3.6m
│   │   ├── crossing.py                # 90deg intersection
│   │   └── funnel.py                  # ARCHIVED — crush scenario, not in paper
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── configs.py                 # C1-C4 active; D1-D4 archived not deleted
│   │   ├── runner.py                  # batch execution, do not modify defaults
│   │   └── analysis.py                # legacy summary stats; superseded by analysis/
│   ├── viz/
│   │   ├── __init__.py
│   │   ├── style.py
│   │   ├── fundamental_diagram.py
│   │   ├── ablation_bars.py
│   │   ├── trajectories.py
│   │   ├── heatmaps.py                # archived, no longer used in paper
│   │   ├── scaling.py
│   │   └── convergence.py             # archived, barrier optimiser figure dropped
│   └── data/
│       ├── __init__.py
│       ├── loader.py                  # FZJ + ETH-UCY loading
│       └── fundamental_diagram.py
├── analysis/                          # NEW: post-hoc analysis on existing data; no new sims
│   ├── __init__.py
│   ├── inventory.py                   # Step 1: catalogue results/ contents
│   ├── zonal_decomposition.py         # Step 3.1: collision zone tagging
│   ├── ttc_distributions.py           # Step 3.2: empirical vs simulated TTC W1 distance
│   ├── statistical_reanalysis.py      # Step 3.3: NB GLM, Cox PH, LMM, Holm–Šidák
│   ├── oracle_baseline.py             # Step 3.4: per-scenario best single-paradigm baseline
│   └── arch_lifetime.py               # Step 3.5: arch lifetime distribution from C1 0.8m runs
├── new_experiments/                   # NEW: only the genuinely missing simulations
│   ├── __init__.py
│   ├── c1_epsilon_control.py          # Step 4.1: SFM with σ=0.05 m/s velocity perturbation
│   ├── force_magnitude_logging.py     # Step 4.2: per-agent force breakdowns at 10-step interval
│   └── external_simulator/
│       ├── __init__.py
│       ├── jupedsim_runner.py         # Step 4.3 primary
│       ├── vadere_runner.py           # fallback
│       └── rvo2_runner.py             # fallback
├── tests/                             # EXISTING — keep all passing
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_world.py
│   ├── test_integrator.py
│   ├── test_desired.py
│   ├── test_sfm.py
│   ├── test_walls.py
│   ├── test_ttc.py
│   ├── test_orca.py
│   ├── test_crush.py                  # tests still run, even though crush is out of paper
│   ├── test_hybrid.py
│   ├── test_density.py
│   ├── test_risk.py                   # tests still run
│   ├── test_scenarios.py
│   ├── test_simulation.py
│   ├── test_smoke.py
│   ├── test_zonal_decomposition.py    # NEW (Step 3.1)
│   ├── test_ttc_distributions.py      # NEW (Step 3.2)
│   ├── test_statistical_reanalysis.py # NEW (Step 3.3)
│   └── test_c1_epsilon.py             # NEW (Step 4.1)
├── results/                           # EXISTING — READ-ONLY, do not delete or regenerate
│   ├── bottleneck/{C1,C2,C3,C4}/w{0.8,1.0,1.2,1.8,2.4,3.6}/seed{0..24}/
│   ├── bidirectional/{C1,C2,C3,C4}/seed{0..24}/
│   ├── crossing/{C1,C2,C3,C4}/seed{0..24}/
│   ├── corridor_fd/{C1,C2,C3,C4}/...
│   ├── deadlock_0.8m/{C1,C2,C3,C4}/seed{0..24}/
│   ├── sigmoid_sweep/                 # archived, reframed in paper not rerun
│   ├── crush/                         # archived, NOT in final paper
│   └── barrier/                       # archived, NOT in final paper
├── results_new/                       # NEW: outputs of new_experiments/ only
│   ├── c1_epsilon/
│   ├── force_logging/
│   └── external_simulator/
├── results_analysis/                  # NEW: outputs of analysis/ scripts
│   ├── zonal_collisions.csv
│   ├── ttc_wasserstein.json
│   ├── statistical_reanalysis.csv
│   ├── oracle_baseline.md
│   └── arch_lifetimes.csv
├── figures/                           # gitignored, regenerated from existing + new data
└── paper/                             # EXISTING — heavy edits in Step 2
    ├── main.tex
    ├── main.tex.bak                   # NEW: pre-surgery backup
    ├── references.bib
    ├── SCITEPRESS.sty
    └── orcid.eps
└── data/                              # EXISTING
    ├── eth-ucy/{raw,eth,hotel,univ,zara1,zara2}/
    └── fzj/{unidirectional,bidirectional,bottleneck}/
```

**Directory rules (non-negotiable):**
- `results/` is **read-only**. Never overwrite or delete an existing seed directory.
- `results_new/` and `results_analysis/` are the only writable output directories from the revision work.
- Existing `sim/` code is read for reference and may be extended with **opt-in logging flags** (force logging, collision-location tagging, ε-perturbation) — the default code path must remain bit-identical so existing reproducibility holds.
- `sim/optimization/`, `sim/steering/crush.py`, `sim/scenarios/funnel.py`, `sim/density/risk.py`, and `sim/density/kde.py` are archived: they remain in the repo, their tests still pass, but they are not referenced from the paper.

---

## 2. STATE TRACKING

### STATUS.json schema

```json
{
  "current_phase": 0,
  "thesis": "ablation_first",
  "phases_completed": [],
  "modules": {},
  "tests": {"passing": 0, "total": 0},
  "functions": {},
  "known_issues": [],
  "last_audit": null,
  "existing_experiments": {},
  "new_experiments": {},
  "post_hoc_analyses": {},
  "figures": {},
  "paper": {
    "abstract": "skeleton", "sec1": "skeleton", "sec2": "skeleton",
    "sec3": "skeleton", "sec4": "skeleton", "sec5": "skeleton", "sec6": "skeleton"
  },
  "gates": {
    "inventory_approved": false,
    "manuscript_surgery_approved": false,
    "zonal_decomposition_case": null,
    "c1_epsilon_interpretation": null,
    "external_simulator_chosen": null,
    "final_review_approved": false
  }
}
```

`existing_experiments` entry example:

```json
"results/bottleneck/C4/w0.8": {
  "scenario": "bottleneck",
  "config": "C4",
  "width_m": 0.8,
  "n_seeds": 25,
  "has_trajectories": true,
  "has_collision_locations": false,
  "has_force_breakdown": false,
  "frozen": true
}
```

`post_hoc_analyses` entry example:

```json
"zonal_decomposition": {
  "script": "analysis/zonal_decomposition.py",
  "input": "results/bottleneck/",
  "output": "results_analysis/zonal_collisions.csv",
  "status": "complete",
  "case": "B"
}
```

### AUDIT_LOG.md format

```markdown
## Phase N — Name
- **Date:** YYYY-MM-DD HH:MM
- **Built:** file1.py (X lines), file2.py (Y lines)
- **Tests:** N new, M total, M passing
- **Gates:** gate1 ✓, gate2 ✓
- **New compute:** description and wall-clock time, or "none (post-hoc)"
- **Issues:** none | description
```

### scripts/audit.sh

```bash
#!/bin/bash
echo "=== FILES ===" && find sim/ analysis/ new_experiments/ -name "*.py" 2>/dev/null | sort
echo "=== TESTS ===" && python -m pytest tests/ -v --tb=short 2>&1 | tail -30
echo "=== IMPORT ===" && python -c "import sim, analysis; print('OK')" 2>&1
echo "=== LINES ===" && find sim/ analysis/ new_experiments/ -name "*.py" -exec wc -l {} + 2>/dev/null | sort -n | tail -20
echo "=== TODOS ===" && grep -rn "TODO\|FIXME\|HACK" sim/ analysis/ new_experiments/ 2>/dev/null || echo "Clean"
echo "=== EXISTING RESULTS UNTOUCHED ===" && find results/ -name "*.parquet" -newer STATUS.json 2>/dev/null | head -5
echo "=== STATUS ===" && python -c "
import json; s=json.load(open('STATUS.json'))
print(f'Phase: {s[\"current_phase\"]}, Thesis: {s[\"thesis\"]}, Tests: {s[\"tests\"][\"passing\"]}/{s[\"tests\"][\"total\"]}')
print(f'Issues: {len(s[\"known_issues\"])}, Gates: {sum(1 for v in s[\"gates\"].values() if v)}/{len(s[\"gates\"])}')
" 2>&1
```

The "EXISTING RESULTS UNTOUCHED" check is critical: any file in `results/` modified after `STATUS.json` is a violation of the read-only rule and must be investigated immediately.

---

## 3. EXECUTION PHASES (revision plan)

The original phase numbering for first-build (Phases 1–8) is archived. The revision uses a new phase numbering tied directly to the SIMULTECH revision plan.

| Phase | Name | New compute? | Gate |
|-------|------|--------------|------|
| R0 | Inventory existing data | None | inventory_approved |
| R1 | Manuscript surgery | None | manuscript_surgery_approved |
| R2 | Post-hoc analyses + consolidated logging re-run | 100 sims (~half day) for trajectories+collisions | zonal_decomposition_case |
| R3 | New experiments | C1+ε, force logging, external sim | c1_epsilon_interpretation, external_simulator_chosen |
| R4 | Manuscript rewrite | None | — |
| R5 | Reproducibility release | None | final_review_approved |

Phases must run in order. Each phase pauses at its gate; the user must approve before proceeding.

### R0 — Inventory (no compute)
1. Walk `results/` and produce `inventory.md` listing every (scenario, config, width, n_seeds) tuple, plus what artefacts each contains (trajectories, collisions with locations, force breakdowns).
2. Update `STATUS.json["existing_experiments"]`.
3. **Gate:** present `inventory.md` to user and wait for approval.

### R1 — Manuscript surgery (no compute)
1. `cp paper/main.tex paper/main.tex.bak`
2. Delete: all DT framing, Section 3.3, Section 4.6, Section 3.4, Section 4.7, Eq. (6) and surrounding paragraph, the 60.5% sentence in the abstract.
3. Update title to *"When Steering Paradigms Fail: A Diagnostic Ablation of Force-Based, Anticipatory, and Velocity-Obstacle Pedestrian Models with Density-Adaptive Mitigation."*
4. Replace abstract with the placeholder version (Section 6 of this file).
5. Compile, report new page count.
6. **Gate:** user approves new structure and page count.

### R2 — Post-hoc analyses (one consolidated re-run + analysis on existing data)

**R2.0 Consolidated trajectory + collision logging re-run (REQUIRED).** The R0 inventory confirmed that `sim/core/simulation.py` reduces its in-memory `metrics_log` to eleven scalars before writing to CSV. Trajectories, per-collision records, and per-agent force breakdowns are not persisted. This means R2.1 (zonal decomposition), R2.2 (TTC distributions), and R2.5 (arch lifetime) are all blocked on missing data, not on missing analysis. A single targeted re-run unblocks all three.

1. Add two opt-in logging flags to `sim/core/simulation.py`: `log_positions: bool = False` and `log_collisions: bool = False`. Both default off. Gated behind `if self.log_positions:` / `if self.log_collisions:` blocks at the end of every step. Default code path must remain bit-identical so existing reproducibility holds (CLAUDE.md §11.13).
2. When `log_positions=True`, append `(t, agent_id, x, y, vx, vy, active)` to a per-run buffer; flush as parquet to `results_new/trajectories/<scenario>_<config>_w<width>_seed<n>.parquet` at simulation end.
3. When `log_collisions=True`, append `(t, agent_i, agent_j, x_i, y_i, x_j, y_j)` to a per-run buffer for every overlap event detected during the contact-force pass; flush as parquet to `results_new/collisions/<scenario>_<config>_w<width>_seed<n>.parquet`.
4. Add a unit test in `tests/test_simulation.py` confirming that with both flags off, the simulation produces the same final state as before (use a stored reference seed).
5. Run cells: `C1, C4` × `w∈{0.8, 1.0}` × `seeds 42–66` = **100 simulations**. Estimated ~half day compute.
6. The new data covers R2.1, R2.2, and R2.5 in one pass. Existing CSVs in `results/` are not touched.
7. **Gate:** confirm with the user before launching the 100-run pass. This is the only piece of new compute in R2 and it is the only acceptable concession to the read-only rule because the existing experiments literally do not contain the required artefacts.

1. **R2.1 Zonal decomposition** (`analysis/zonal_decomposition.py`). Reads `results_new/collisions/` from R2.0; tags zones (upstream / throat / downstream); writes `results_analysis/zonal_collisions.csv` and a stacked-bar figure. **Gate:** report which case (A/B/C) applies before any prose is written.
2. **R2.2 TTC distributions** (`analysis/ttc_distributions.py`). Computes pairwise τ for FZJ bottleneck empirical and the C1–C4 simulated trajectories generated by R2.0 at w=1.0 m. Reports W₁ distance per config. Writes `results_analysis/ttc_wasserstein.json`. The FZJ bottleneck experiments are not run at exactly w=1.0 m, so the comparison is a qualitative match of distribution shape rather than a tight quantitative validation — flag this honestly in Section 4.3 of the paper.
3. **R2.3 Statistical reanalysis** (`analysis/statistical_reanalysis.py`). statsmodels NB GLM for collision counts, lifelines Cox PH for deadlock, LMM for speed/throughput, Holm–Šidák correction. Writes `results_analysis/statistical_reanalysis.csv` and a LaTeX table.
4. **R2.4 Oracle baseline** (`analysis/oracle_baseline.py`). Pure analysis on existing data; identifies per-scenario best single-paradigm; writes `results_analysis/oracle_baseline.md`.
5. **R2.5 Arch lifetime** (`analysis/arch_lifetime.py`). Reads `results_new/trajectories/` from R2.0 for C1 at w=0.8 m. Defines an arch as ≥3 agents within 0.5 m of exit centerline, no exit crossing for ≥2 s. Writes `results_analysis/arch_lifetimes.csv`.

6. **R2.6 Held-out OOD validation** (`analysis/ood_validation.py`). The R0 inventory identified `results/bottleneck_validation.csv`: a held-out FZJ bottleneck flow-rate comparison showing −27% to −43% sim-vs-empirical mismatch across exit widths. This file already exists from prior work and is the strongest available out-of-distribution validation result. The original paper did not lean on it. The revised paper will. Load it, compute the per-width relative error, generate a small comparison table for Section 4.3, and write `results_analysis/ood_validation.csv`. Frame the result honestly: *"On the held-out FZJ bottleneck dataset, the calibrated model underpredicts flow rates by 27–43% across exit widths. We report this gap as a measure of out-of-distribution generalisation; the calibration was performed on the FZJ unidirectional corridor and tested without modification on the bottleneck geometry."* This converts the original paper's biggest weakness (in-sample calibration only) into a strength (rigorous OOD evaluation, even when unflattering). No new compute.

### R3 — New experiments (minimal compute)
1. **R3.1 C1+ε control** (`new_experiments/c1_epsilon_control.py`). C1 at w=0.8 m, 100 agents, n=25, paired seeds with existing C1 0.8 m. Add Gaussian velocity perturbation σ=0.05 m/s every step. ~2 hr compute. Writes `results_new/c1_epsilon/`. **Gate:** report which interpretation (directional / symmetry-breaker / ORCA-worse) applies.
2. **R3.2 Force-magnitude logging** (`new_experiments/force_magnitude_logging.py`). C4 at w=1.0 m, n=5, with per-agent force component logging at every 10th timestep. ~30 min compute. Writes `results_new/force_logging/`. Generates `figures/force_magnitude_vs_density.pdf`. Do **not** move the sigmoid centre even if the empirical crossover differs — document the offset in Section 3.1 instead.
3. **R3.3 External simulator** (`new_experiments/external_simulator/jupedsim_runner.py` first, fall back to vadere then rvo2). w=1.0 m, 50 agents, n=25. Writes `results_new/external_simulator/`. **Gate:** report which tool was used; if all three fail, document the gap in Limitations.

### R4 — Manuscript rewrite (no compute)
Section-by-section rewrite per Section 7 of this file. Six figures, five tables, 12 pages.

### R5 — Reproducibility release (no compute)
GitHub repo, Zenodo DOI, reproduction README, supplementary appendix with hardware/timing/seeds.

---

## 4. HELPERS (sim/core/helpers.py — UNCHANGED)

```python
import numpy as np, warnings

def check_forces(forces: np.ndarray, name: str) -> np.ndarray:
    """Validate force array. MUST be called as last line of every force function."""
    if np.any(np.isnan(forces)):
        bad = np.unique(np.where(np.isnan(forces))[0])
        raise ValueError(f"NaN in {name} forces at agents {bad[:5].tolist()}")
    mask = np.abs(forces) > 1e6
    if np.any(mask):
        bad = np.unique(np.where(mask)[0])
        warnings.warn(f"Clamped extreme {name} forces at agents {bad[:5].tolist()}")
        forces = np.clip(forces, -1e6, 1e6)
    return forces

def safe_normalize(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    if v.ndim == 1:
        m = np.linalg.norm(v)
        return v / m if m > eps else np.zeros_like(v)
    mag = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.maximum(mag, eps)

def clamp_speed(velocities: np.ndarray, max_speeds: np.ndarray) -> np.ndarray:
    speeds = np.linalg.norm(velocities, axis=1)
    scale = np.where(speeds > max_speeds, max_speeds / np.maximum(speeds, 1e-8), 1.0)
    return velocities * scale[:, None]
```

---

## 5. FORCE MODEL (sim/steering/hybrid.py)

The original document presented Eq. (1) as the sum:

```
F = (1-w_crush)·F_desire + F_SFM + F_TTC + w_ORCA·F_ORCA + w_crush·F_crush + F_wall
```

For the revised paper, present this as a **convex combination of accelerations** in Section 3.1 of the manuscript:

```
a_i = (1 − w_o(ρ_i)) · (a_des + a_SFM + a_TTC) + w_o(ρ_i) · a_ORCA + a_wall
```

with w_o(ρ) = 1 − σ(ρ; 4.0, 2.0) and σ(x;x0,k) = 1/(1+exp(−k(x−x0))). Crush term is gone (archived).

**Critical:** before writing this paragraph in the paper, **read `sim/steering/hybrid.py` and confirm the actual implementation is consistent with the convex combination**. If the implementation differs (e.g., it's still the additive sum), document what the code actually does — honesty over elegance. The paper must describe the code, not the other way around.

The hysteresis claim made earlier in the plan is not implemented — do **not** claim it is. Instead, add one sentence in Limitations: *"The current sigmoid transitions are not hysteretic; we observed no oscillation artefacts in the present experiments but recommend hysteresis for deployments at densities sustained near ρ₀."*

Existing per-component force code (`desired.py`, `sfm.py`, `ttc.py`, `orca.py`, `walls.py`) is unchanged. Equations from the original document remain authoritative for those modules; refer to git history for the originals if needed.

---

## 6. ABSTRACT (placeholder, fill after R3)

> No single pedestrian steering paradigm performs well across all crowd scenarios. We present a zone-decomposed ablation of Social Force, time-to-collision, and Optimal Reciprocal Collision Avoidance steering across bottleneck, bidirectional, and crossing geometries (n = 25 per cell, negative-binomial GLM and Cox survival analysis with Holm–Šidák correction), and identify two failure modes that single-paradigm models cannot avoid: time-to-collision anticipation locks symmetric arches at narrow exits (0/25 evacuations versus 1/25 for plain SFM), while ORCA-style yielding produces gridlock in counterflow. A symmetry-breaking control experiment isolates the mechanism by which ORCA resolves arching deadlocks. We propose a density-adaptive convex combination of the three paradigms that mitigates each failure mode and validate it against 4776 FZJ pedestrian trajectory data points using both speed–density and time-to-collision distribution metrics. At 90° crossings the blended model triples throughput over plain SFM (p < 0.001); at narrow bottlenecks it resolves arching deadlocks in [Z]% of trials versus 4% for SFM alone. Comparison against [JuPedSim/Vadere/RVO2] confirms the framework produces equivalent aggregate behaviour while exposing per-paradigm contributions monolithic simulators do not. Code, data, and reproduction scripts are released.

---

## 7. PAPER STRUCTURE (12 pages SciTePress)

| Section | Pages | Key content |
|---------|-------|-------------|
| Abstract | 0.3 | Diagnostic framing, two failure modes, mitigation, external comparison |
| 1 Introduction | 1.25 | Disasters, diagnostic question, three claims, five contributions |
| 2 Related Work | 1.25 | Organised by failure modes, not model families |
| 3 Methodology | 2.5 | Convex acceleration formulation, Voronoi density, scenarios, collision zone tagging |
| 4 Experiments | 4.5 | Setup, force diagnostic, calibration (FD + TTC), zone-decomposed ablation, deadlock + C1+ε, external sim |
| 5 Discussion | 1.5 | Lead with negative findings, mechanism explanations, oracle gap, limitations |
| 6 Conclusion | 0.5 | Findings, artefacts, future work (DT mentioned only here) |
| References | 0.7 | ~25–30 entries |

---

## 8. FIGURES (six total)

1. Fundamental diagram, 2×2 C1–C4 (existing, recaption to acknowledge steering insensitivity)
2. **NEW** Force magnitude vs density (R3.2 output)
3. Calibration: FD train/test/sim + TTC distribution panel (combines existing FD with R2.2 output)
4. **NEW** Zonal collision stacked bars at w=1.0 m (R2.1 output)
5. Deadlock trajectory pair, C1 vs C4 (existing Figure 4, kept)
6. Computation time scaling (existing, kept)

Dropped: density heatmap (crush cut), barrier optimiser convergence (cut), mean speed bar chart (folded into the ablation summary table).

---

## 9. TABLES (six total)

1. Model parameters (existing)
2. Scenario summary (existing, trim crush/funnel rows)
3. **NEW** Zone-decomposed collision counts per (config, width)
4. **NEW** Deadlock completion rates including C1+ε row, plus Cox HR table
5. **NEW** External simulator comparison (one row each: C1, C4, JuPedSim/Vadere/RVO2)
6. **NEW** Held-out OOD validation: per-width FZJ bottleneck flow rate vs simulated, with relative error (from R2.6)

Plus: a statistical results summary table (NB GLM IRRs, Cox HRs) appended to Section 4.

---

## 10. PARAMETERS (config/params.yaml — UNCHANGED)

Crush, optimization, and risk sections retained in YAML for reproducibility of archived experiments. The paper draws parameters only from the simulation, agent, sfm, ttc, orca, hybrid, and density.voronoi sections.

---

## 11. CODING RULES

1. Type hints + Google docstrings on every function.
2. NumPy vectorization — no Python loops over agents (except ORCA LP, walls).
3. `np.random.Generator(PCG64(seed))` — never `np.random.seed()`.
4. `check_forces()` as last line of every force function.
5. `safe_normalize()` for every normalization.
6. `max(d, 1e-6)` for every distance denominator.
7. Skip `j==i` in every neighbor loop.
8. Tests for every new module under `analysis/` and `new_experiments/`; pytest must pass after every phase.
9. Commit after every phase with message `phase Rn: <name>`.
10. CSV output: scenario, config, seed, metric columns.
11. PDF figures: 10 pt+ fonts, serif, colorblind-safe.
12. **New rule:** any script that touches `results/` must open files read-only (`mode="rb"` or pyarrow read-only). Writing to `results/` is forbidden; write to `results_new/` or `results_analysis/` instead.
13. **New rule:** any new logging in `sim/core/simulation.py` is gated behind a default-off flag. Existing experiment reproducibility depends on the default code path being bit-identical.
14. **New rule:** every analysis script must import the canonical file allowlist from `analysis/inventory.py` and skip stub / superseded files. Do not glob `results/*.csv` directly. The allowlist (defined in `analysis/inventory.py`) excludes:
    - `BottleneckScenario_C*.csv` — n=5 stubs, superseded by `Bottleneck_w1.0_C*.csv`
    - `Bottleneck_w0.8_C*.csv` without the `_600s_` suffix — n=5 stubs, superseded by `Bottleneck_w0.8_600s_C*.csv`
    - `Bottleneck_w0.8_long_C*.csv` — exploratory partial coverage
    - `sigmoid_sensitivity.csv` (the 22-row stub) — superseded by `sigmoid_sensitivity_full.csv`
    - `optimizer_history.json` — older version, superseded by `optimizer_C{1,4}_history.json`
    
    These files remain in `results/` per the read-only rule but must never be loaded by analysis code. A pulled stub file will silently corrupt downstream statistics.

---

## 12. DATA FORMATS (UNCHANGED)

FZJ: `data/fzj/{unidirectional,bidirectional,bottleneck}/*.txt`. Space-separated `frame_id ped_id x y`. 25 fps. Comment lines start with `#`.
ETH-UCY: `data/eth-ucy/{eth,hotel,univ,zara1,zara2}/{train,val,test}/*.txt`. Space/tab-separated. 2.5 fps.
Loading: `pd.read_csv(path, sep=r'\s+', header=None, names=['frame_id','ped_id','x','y'], comment='#')`

---

## 13. WHAT NOT TO DO

- Do not re-run any experiment in `results/` to "improve" sample size or "regenerate cleanly". Existing data is frozen.
- Do not delete archived modules (`crush.py`, `risk.py`, `barrier.py`, `funnel.py`). Their tests still run.
- Do not claim hysteresis, real-time DT integration, sensor coupling, or any feature not actually implemented.
- Do not move the sigmoid centre ρ₀ even if the force-magnitude diagnostic suggests a different crossover — moving it would invalidate every existing experiment.
- Do not revive the crush regime, barrier optimisation, or composite risk metric in the paper text.
- Do not narrate the visualizer/skill/tool internals to the user.
- Do not proceed past a gate without explicit user approval.
