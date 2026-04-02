# CLAUDE.md — CrowdTwin: Hybrid Crowd Simulation Digital Twin

> **READ THIS ENTIRE FILE BEFORE WRITING ANY CODE.**
> Single source of truth for architecture, equations, algorithms, parameters, and conventions.

---

## 0. PROJECT IDENTITY

**What:** Hybrid SFM/TTC/ORCA pedestrian crowd simulation engine in a Digital Twin architecture.
**Why:** No published system combines these three steering paradigms. No crowd safety DT includes hybrid steering + multi-method density estimation + composite risk + crush regime + barrier optimization. This is the first.
**Target:** SIMULTECH 2026 regular paper, 12 pages SciTePress, deadline April 16 2026. Double-blind.
**Stack:** Python 3.11+, NumPy-vectorized, all models from scratch. No third-party sim libraries.
**Performance:** 1000 agents at ≥30 steps/sec (dt=0.01s → ≤33ms/step).

---

## 1. REPO LAYOUT

Existing: `paper/` (LaTeX), `data/` (FZJ + ETH-UCY). New code goes in `sim/`.

```
pedestrian-abs/
├── CLAUDE.md                   # THIS FILE
├── STATUS.json                 # State tracker (Phase 1 creates, every phase updates)
├── AUDIT_LOG.md                # Build log (Phase 1 creates, every phase appends)
├── pyproject.toml              # Phase 1 creates
├── .gitignore                  # Phase 1 updates
├── config/params.yaml          # Phase 1 creates
├── scripts/
│   ├── audit.sh                # Phase 1 creates
│   ├── run_experiments.py      # Phase 8 creates
│   └── generate_figures.py     # Phase 8 creates
├── sim/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── helpers.py          # check_forces, safe_normalize, clamp_speed
│   │   ├── agent.py            # AgentState dataclass
│   │   ├── world.py            # Wall, Obstacle, World, geometry utils
│   │   ├── simulation.py       # Simulation loop + metrics
│   │   └── integrator.py       # Euler / RK4
│   ├── steering/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract SteeringModel
│   │   ├── desired.py          # Goal-seeking force
│   │   ├── sfm.py              # Social Force Model
│   │   ├── ttc.py              # Time-to-Collision
│   │   ├── orca.py             # ORCA velocity optimization
│   │   ├── walls.py            # Wall forces
│   │   ├── crush.py            # Crush regime
│   │   └── hybrid.py           # Density-weighted hybrid
│   ├── density/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── grid.py
│   │   ├── voronoi.py
│   │   ├── kde.py
│   │   └── risk.py
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── barrier.py
│   │   └── optimizer.py
│   ├── scenarios/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── corridor.py         # 10x3.6m
│   │   ├── bottleneck.py       # 10x10m room + exit
│   │   ├── bidirectional.py    # 20x3.6m
│   │   ├── crossing.py         # 90deg intersection
│   │   └── funnel.py           # 10m→3m taper
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── configs.py          # C1-C4, D1-D4, etc.
│   │   ├── runner.py           # Batch execution → CSV
│   │   └── analysis.py         # Statistics
│   ├── viz/
│   │   ├── __init__.py
│   │   ├── style.py
│   │   ├── fundamental_diagram.py
│   │   ├── ablation_bars.py
│   │   ├── trajectories.py
│   │   ├── heatmaps.py
│   │   ├── scaling.py
│   │   └── convergence.py
│   └── data/
│       ├── __init__.py
│       ├── loader.py           # FZJ + ETH-UCY loading
│       └── fundamental_diagram.py
├── tests/
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_world.py
│   ├── test_integrator.py
│   ├── test_desired.py
│   ├── test_sfm.py
│   ├── test_walls.py
│   ├── test_ttc.py
│   ├── test_orca.py
│   ├── test_crush.py
│   ├── test_hybrid.py
│   ├── test_density.py
│   ├── test_risk.py
│   ├── test_scenarios.py
│   ├── test_simulation.py
│   └── test_smoke.py
├── results/                    # gitignored
├── figures/                    # gitignored
├── paper/                      # EXISTING
│   ├── main.tex
│   ├── references.bib          # 36 refs
│   ├── SCITEPRESS.sty
│   └── orcid.eps
└── data/                       # EXISTING
    ├── eth-ucy/{raw,eth,hotel,univ,zara1,zara2}/
    └── fzj/{unidirectional,bidirectional,bottleneck}/
```

---

## 2. STATE TRACKING

### STATUS.json schema
```json
{
  "current_phase": 0,
  "phases_completed": [],
  "modules": {},
  "tests": {"passing": 0, "total": 0},
  "functions": {},
  "known_issues": [],
  "last_audit": null,
  "experiments": {},
  "figures": {},
  "paper": {
    "abstract": "skeleton", "sec1": "skeleton", "sec2": "skeleton",
    "sec3": "skeleton", "sec4": "skeleton", "sec5": "skeleton", "sec6": "skeleton"
  }
}
```

modules entry example:
```json
"sim/steering/sfm.py": {"lines": 145, "tests": 7, "status": "complete"}
```

functions entry example:
```json
"SocialForceModel.compute_agent_forces": {
  "module": "sim.steering.sfm",
  "sig": "(agent_state: AgentState, neighbor_lists: list[list[int]]) -> ndarray(N,2)"
}
```

### AUDIT_LOG.md format
```markdown
## Phase N — Name
- **Date:** YYYY-MM-DD HH:MM
- **Built:** file1.py (X lines), file2.py (Y lines)
- **Tests:** N new, M total, M passing
- **Gates:** gate1 ✓, gate2 ✓
- **Issues:** none | description
```

### scripts/audit.sh
```bash
#!/bin/bash
echo "=== FILES ===" && find sim/ -name "*.py" 2>/dev/null | sort
echo "=== TESTS ===" && python -m pytest tests/ -v --tb=short 2>&1 | tail -30
echo "=== IMPORT ===" && python -c "import sim; print('OK')" 2>&1
echo "=== LINES ===" && find sim/ -name "*.py" -exec wc -l {} + 2>/dev/null | sort -n | tail -15
echo "=== TODOS ===" && grep -rn "TODO\|FIXME\|HACK" sim/ 2>/dev/null || echo "Clean"
echo "=== STATUS ===" && python -c "
import json; s=json.load(open('STATUS.json'))
print(f'Phase: {s[\"current_phase\"]}, Tests: {s[\"tests\"][\"passing\"]}/{s[\"tests\"][\"total\"]}')
print(f'Issues: {len(s[\"known_issues\"])}')
" 2>&1
```

---

## 3. HELPERS (sim/core/helpers.py)

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
    """Normalize vector(s). Returns zero for sub-epsilon magnitudes."""
    if v.ndim == 1:
        m = np.linalg.norm(v)
        return v / m if m > eps else np.zeros_like(v)
    mag = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.maximum(mag, eps)

def clamp_speed(velocities: np.ndarray, max_speeds: np.ndarray) -> np.ndarray:
    """Per-agent speed clamping. max_speeds shape (N,)."""
    speeds = np.linalg.norm(velocities, axis=1)
    scale = np.where(speeds > max_speeds, max_speeds / np.maximum(speeds, 1e-8), 1.0)
    return velocities * scale[:, None]
```

---

## 4. AGENT STATE (sim/core/agent.py)

```python
@dataclass
class AgentState:
    positions: np.ndarray       # (N,2)
    velocities: np.ndarray      # (N,2)
    goals: np.ndarray           # (N,2)
    radii: np.ndarray           # (N,)
    desired_speeds: np.ndarray  # (N,)
    masses: np.ndarray          # (N,)
    taus: np.ndarray            # (N,) relaxation time
    active: np.ndarray          # (N,) bool

    @property
    def n(self) -> int: return len(self.positions)
    @property
    def n_active(self) -> int: return int(np.sum(self.active))
    @property
    def active_indices(self) -> np.ndarray: return np.where(self.active)[0]
    def deactivate(self, indices): self.active[indices] = False

    @classmethod
    def create(cls, n, spawn_area, goals, seed=42, heterogeneous=True,
               speed_mean=1.34, speed_std=0.26, radius_mean=0.25,
               radius_std=0.03, mass=80.0, tau=0.5):
        rng = np.random.Generator(np.random.PCG64(seed))
        x0,x1,y0,y1 = spawn_area
        pos = np.column_stack([rng.uniform(x0,x1,n), rng.uniform(y0,y1,n)])
        if goals.ndim == 1: goals = np.tile(goals, (n,1))
        if heterogeneous:
            spd = np.maximum(rng.normal(speed_mean, speed_std, n), 0.5)
            rad = np.maximum(rng.normal(radius_mean, radius_std, n), 0.15)
            tau_arr = rng.uniform(0.4, 0.6, n)
        else:
            spd = np.full(n, speed_mean); rad = np.full(n, radius_mean)
            tau_arr = np.full(n, tau)
        return cls(pos, np.zeros((n,2)), goals, rad, spd,
                   np.full(n,mass), tau_arr, np.ones(n,dtype=bool))
```

---

## 5. WORLD + GEOMETRY (sim/core/world.py)

```python
@dataclass
class Wall:
    start: np.ndarray  # (2,)
    end: np.ndarray    # (2,)

@dataclass
class Obstacle:
    vertices: np.ndarray  # (M,2)

class World:
    def __init__(self, walls, obstacles=None):
        self.walls = walls
        self.obstacles = obstacles or []
```

### point_to_segment_distance
```
Input: point(2,), seg_start(2,), seg_end(2,)
Output: (distance, closest_point(2,), normal(2,))

AB = end - start; AP = point - start
if |AB|² < 1e-12: degenerate segment → distance to start
t = clamp(dot(AP,AB)/dot(AB,AB), 0, 1)
closest = start + t·AB
diff = point - closest; dist = |diff|
if dist < 1e-8: normal = perpendicular to AB (normalized)
else: normal = diff/dist
```

### agents_to_walls — vectorized over agents, loop over walls
```
Input: positions(N,2), walls list
Output: distances(N,W), normals(N,W,2)
```

---

## 6. DESIRED FORCE (sim/steering/desired.py)

```
F = m · (v0·ê - v) / τ,  ê = normalize(goal - pos)
```
Fully vectorized. Worked example: agent at origin, goal (5,0), v=0, m=80, τ=0.5 → F=(214.4, 0)N.

---

## 7. SFM AGENT-AGENT (sim/steering/sfm.py)

```
f_ij = A·exp((r_ij-d_ij)/B)·n_ij              [social repulsion, always]
     + k·g(r_ij-d_ij)·n_ij                    [body compression, contact only]
     + κ·g(r_ij-d_ij)·dot(Δv_ji,t_ij)·t_ij   [friction, contact only]

r_ij = r_i+r_j,  d_ij = |x_i-x_j|,  n_ij = (x_i-x_j)/d_ij  (j→i)
t_ij = (-n_ij[1], n_ij[0]),  g(x) = max(0,x),  Δv_ji = v_j-v_i
A=2000N, B=0.08m, k=120000 kg/s², κ=240000 kg/(m·s)

Edge cases:
- d_ij < 1e-6 → set 1e-6, arbitrary normal
- j==i → skip
- Force symmetry: f_ij = -f_ji by construction
```

Worked example: agents at (0,0) and (0.4,0), r=0.25 each → overlap=0.1, social≈-6980N, body=-12000N → total≈-19000N pushing agent 0 left.

---

## 8. WALL FORCES (sim/steering/walls.py)

Same SFM structure. Agent-to-segment distance replaces d_ij. Friction uses v_i not Δv (wall stationary).

---

## 9. TTC FORCE (sim/steering/ttc.py)

### τ computation
```
dx = x_j - x_i,  dv = v_i - v_j,  r = r_i + r_j
a = dot(dv,dv),  b = -dot(dx,dv),  c = dot(dx,dx) - r²
disc = b² - a·c

τ = (-b - √disc) / a      ← THIS EXACT FORMULA

Cases: a<1e-8→∞, disc<0→∞, τ≤0→∞, τ>τ_max→skip
```

### ANALYTICAL TEST — MUST PASS
```
A at (-1,0) vel (1,0) r=0.25, B at (1,0) vel (-1,0) r=0.25
dx=(2,0), dv=(2,0), r=0.5
a=4, b=-4, c=3.75, disc=1.0
τ = (-(-4) - 1)/4 = (4-1)/4 = 0.75s ✓
Physical: 2m gap, 2m/s closing, collide when gap=0.5m → (2-0.5)/2 = 0.75s ✓
```

### Force
```
F_mag = k_ttc·exp(-τ/τ_0)/τ²    k_ttc=1.5, τ_0=3.0, τ_max=8.0
n_avoid = safe_normalize((x_i+v_i·τ) - (x_j+v_j·τ))
F_TTC_i = Σ F_mag · n_avoid     (over valid pairs)
```

---

## 10. ORCA (sim/steering/orca.py)

Outputs velocity → convert to force: F = m·(v_orca - v)/τ_orca, τ_orca=0.5s

### 10.1 Half-plane: COLLISION case (dist < r_sum)
```python
direction = x_rel/dist if dist > 1e-6 else [1,0]
u = -(r_sum - dist)/dt · direction    # push apart
normal = safe_normalize(-direction)
point = vel_i + 0.5·u
```

### 10.2 Half-plane: NON-COLLISION case
```python
x_rel = pos_j - pos_i; v_rel = vel_i - vel_j
w = v_rel - x_rel/τ_h    # vector from truncation circle center to v_rel
r_trunc = r_sum/τ_h

# Cap vs leg: dot(w,x_rel)<0 AND dot(w,x_rel)²>r_sum²·dot(w,w) → cap
# Cap projection:
  u = (r_trunc/|w| - 1)·w

# Leg projection:
  leg = sqrt(dist² - r_sum²)
  cross = x_rel[0]·v_rel[1] - x_rel[1]·v_rel[0]  # determines left/right
  if cross > 0: direction = [x_rel[0]·leg - x_rel[1]·r_sum, x_rel[0]·r_sum + x_rel[1]·leg] / dist²
  else:         direction = [x_rel[0]·leg + x_rel[1]·r_sum, -x_rel[0]·r_sum + x_rel[1]·leg] / dist²
  u = dot(v_rel,direction)·direction - v_rel

normal = u/|u|; point = vel_i + 0.5·u
```

### 10.3 Incremental 2D LP
```
Start: result = clamp(v_pref, max_speed)
For each constraint (point_k, normal_k):
  if dot(result-point_k, normal_k) ≥ 0: skip (satisfied)
  else: project result onto constraint line
    line_dir = (-normal_k[1], normal_k[0])
    t_left, t_right = -1e9, 1e9
    for each previous constraint j:
      denom = dot(line_dir, normal_j)
      numer = dot(point_j - point_k, normal_j)
      if |denom|<1e-10: if numer<0 → infeasible; else continue
      t = numer/denom
      if denom>0: t_left = max(t_left, t)
      else: t_right = min(t_right, t)
    clamp to speed circle (quadratic in t)
    t_opt = clamp(dot(v_pref - point_k, line_dir), t_left, t_right)
    result = point_k + t_opt·line_dir
```

### 10.4 scipy fallback
```python
from scipy.optimize import minimize
def solve_lp_scipy(halfplanes, v_pref, max_speed):
    constraints = [{'type':'ineq','fun':lambda v,p=pt,n=nm: np.dot(v-p,n)} for pt,nm in halfplanes]
    constraints.append({'type':'ineq','fun':lambda v: max_speed**2 - np.dot(v,v)})
    res = minimize(lambda v: np.sum((v-v_pref)**2), v_pref, method='SLSQP', constraints=constraints)
    return res.x if res.success else v_pref
```

### 10.5 Per-agent loop
```python
for i in active_agents:
    halfplanes = [construct_halfplane(i,j) for j in neighbors[i] if j!=i and valid]
    v_pref = desired_speed_i · normalize(goal_i - pos_i)
    v_orca = solve_2d_lp(halfplanes, v_pref, 2·desired_speed_i)
    forces[i] = mass_i · (v_orca - vel_i) / τ_orca
```

---

## 11. CRUSH REGIME (sim/steering/crush.py)

Same as SFM contact forces with enhanced coefficients, NO social repulsion:
```
k_crush=360000 (3× normal), κ_crush=480000 (2× normal)
f_crush_ij = k_crush·g(r_ij-d_ij)·n_ij + κ_crush·g(r_ij-d_ij)·dot(Δv,t)·t
```

---

## 12. HYBRID (sim/steering/hybrid.py)

```
F = (1-w_crush)·F_desire + F_SFM + F_TTC + w_ORCA·F_ORCA + w_crush·F_crush + F_wall

σ(x;x0,k) = 1/(1+exp(-k·(x-x0)))
w_ORCA(ρ) = 1 - σ(ρ; 4.0, 2.0)     ρ=1→0.998, ρ=4→0.5, ρ=7→0.002
w_crush(ρ) = σ(ρ; 5.5, 3.0)         ρ=3→0.001, ρ=5.5→0.5, ρ=8→0.999
```

Configs:
```python
CONFIGS = {
    "C1": {"sfm":True, "ttc":False, "orca":False, "crush":False},
    "C2": {"sfm":True, "ttc":True,  "orca":False, "crush":False},
    "C3": {"sfm":True, "ttc":False, "orca":True,  "crush":False},
    "C4": {"sfm":True, "ttc":True,  "orca":True,  "crush":True},
}
CRUSH_CONFIGS = {"D1":None, "D2":5.0, "D3":5.5, "D4":7.0}
```

---

## 13. DENSITY (sim/density/)

Grid: `ρ = count(neighbors in R)/(πR²)`, R=2.0m
Voronoi: `ρ = 1/cell_area`, clip to domain with shapely. Add mirror points for boundary.
KDE: `scipy.stats.gaussian_kde(positions.T, bw=1.0).evaluate(positions.T)`

---

## 14. RISK (sim/density/risk.py)

```
R = (ρ̂/ρ_ref)·[1 + P/P_ref + |∇ρ|/∇ρ_ref]
ρ̂ = max(ρ_V, ρ_KDE), P = ρ̂·σ_v, σ_v = std(|v_j| for neighbors)
ρ_ref=6, P_ref=3, ∇ρ_ref=4
R<1:normal, 1-2:elevated, 2-3:high, ≥3:critical
```

---

## 15. INTEGRATION (sim/core/integrator.py)

Euler: `v += (F/m)·dt, x += v·dt`
RK4: standard 4th-order on (dx/dt=v, dv/dt=F/m) with 4 force evaluations
Post: clamp_speed(vel, 2·desired_speed)

---

## 16. SIMULATION LOOP (sim/core/simulation.py)

Each step:
1. KDTree from active positions
2. query_ball_point(r=neighbor_radius) → neighbor lists
3. Compute density (grid by default)
4. HybridSteeringModel.compute_forces(state, neighbors, walls, densities)
5. Integrate → new pos, vel
6. clamp_speed
7. Deactivate agents within goal_reached_dist of goal
8. Record metrics

---

## 17. PARAMETERS (config/params.yaml)

```yaml
simulation: {dt: 0.01, integrator: euler, neighbor_radius: 3.0, max_time: 300.0, goal_reached_dist: 0.5}
agent: {mass: 80.0, desired_speed: 1.34, desired_speed_std: 0.26, radius: 0.25, radius_std: 0.03, tau: 0.5}
sfm: {A: 2000.0, B: 0.08, k: 120000.0, kappa: 240000.0}
ttc: {k_ttc: 1.5, tau_0: 3.0, tau_max: 8.0}
orca: {time_horizon: 5.0, tau_orca: 0.5}
hybrid: {rho_orca_fade: 4.0, k_orca_fade: 2.0, rho_crit: 5.5, k_crit: 3.0}
crush: {k_crush: 360000.0, kappa_crush: 480000.0}
density: {grid_radius: 2.0, kde_bandwidth: 1.0}
risk: {rho_ref: 6.0, P_ref: 3.0, grad_rho_ref: 4.0}
optimization: {method: cma-es, population_size: 15, initial_sigma: 1.0, max_evaluations: 200}
```

---

## 18. SCENARIOS

| Name | Dims | Agents | Walls | Spawn | Goal |
|------|------|--------|-------|-------|------|
| Corridor | 10×3.6 | variable | 4 rect | x∈[0.5,2] y∈[0.3,3.3] | (10.5, y_i) |
| Bottleneck | 10×10 room | 100 | 3+2(gap) | x∈[1,8] y∈[1,9] | (11, 5) |
| Bidirectional | 20×3.6 | 150+150 | 4 rect | left/right ends | opposite end |
| Crossing | 10×10+corridors | 100+100 | T-intersection | bottom/left corridors | opposite |
| Funnel | 15m taper 10→3 | 300-500 | 2 angled+left | x∈[0.5,5] y∈[1,9] | (16, 5) |

Bottleneck exit widths: 0.8, 1.0, 1.2, 1.8, 2.4, 3.6 m (gap centered at y=5).
Funnel walls: top (0,10)→(15,6.5), bottom (0,0)→(15,3.5), left (0,0)→(0,10).

---

## 19. EXPERIMENTS

| Family | Scenario | Configs | Reps | Key Metric |
|--------|----------|---------|------|------------|
| A | Corridor FD | C1-C4 | 30 | Speed-density RMSE |
| B | Bottleneck 6 widths | C1-C4 | 30 | Evacuation time |
| C | Bidirectional+Crossing | C1-C4 | 30 | Lane formation |
| D | Funnel crush | D1-D4 | 30 | Max density, TACD |
| E | Barrier optimization | C4 | 5 | Evac improvement |
| F | Scaling | C4 | 3 | ms/step |

Metrics per run: evacuation_time, mean_speed, max_density, collision_count, flow_rate, agents_exited, mean_risk, max_risk, time_above_critical.

---

## 20. FIGURES (8 total)

1. Fundamental diagram: 2×2 subplot C1-C4, scatter + empirical + Weidmann
2. Ablation bars: groups=scenarios, bars=C1-C4, error bars=95%CI
3. Trajectories: top-down paths in bottleneck, color=time
4. Density heatmap: funnel at peak, YlOrRd
5. Evacuation vs width: lines=C1-C4, error bars
6. Scaling: log-log agents vs ms/step
7. Risk map: funnel composite risk heatmap
8. Optimizer convergence: evaluations vs objective

---

## 21. PAPER (12 pages SciTePress)

| Section | Pages | Key content |
|---------|-------|-------------|
| Abstract | 0.3 | Problem, approach, key result, implication |
| 1 Intro | 1.5 | Disasters, gap, 5 contributions |
| 2 Related | 1.5 | Models, hybrids, metrics, DTs |
| 3 Framework | 2.5 | Hybrid steering, density, crush, optimization |
| 4 Experiments | 3.5 | FD, ablation, crush, optimization, scaling |
| 5 Discussion | 1.0 | Why hybrid works, limitations |
| 6 Conclusions | 0.5 | Summary, future |
| References | 1.2 | 25-35 entries |

---

## 22. CODING RULES

1. Type hints + Google docstrings on every function
2. NumPy vectorization — no Python loops over agents (except ORCA LP, walls)
3. np.random.Generator(PCG64(seed)) — NEVER np.random.seed()
4. check_forces() as last line of every force function
5. safe_normalize() for every normalization
6. max(d, 1e-6) for every distance denominator
7. Skip j==i in every neighbor loop
8. Tests for every module, pytest must pass after every phase
9. Commit after every phase with message
10. CSV output: scenario, config, seed, metric columns
11. PDF figures: 10pt+ fonts, serif, colorblind-safe

---

## 23. DATA FORMATS

FZJ: `data/fzj/{unidirectional,bidirectional,bottleneck}/*.txt`
  Space-separated: frame_id ped_id x y. 25fps. Comment lines start with #.
ETH-UCY: `data/eth-ucy/{eth,hotel,univ,zara1,zara2}/{train,val,test}/*.txt`
  Space/tab-separated: frame_id ped_id x y. 2.5fps.
Loading: `pd.read_csv(path, sep=r'\s+', header=None, names=['frame_id','ped_id','x','y'], comment='#')`
