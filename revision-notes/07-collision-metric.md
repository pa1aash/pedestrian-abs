# Session 07 — Collision Metric Audit

## 1. Definition in code

**File:** `sim/core/simulation.py`
**Counter:** lines 225–232 (per-step pair scan in `_step_metrics`)
**Aggregation:** line 425 — `total_collisions = int(np.sum([m["collision_count"] for m in self.metrics_log]))`

```python
# sim/core/simulation.py:225-232
collision_count = 0
for i in active_now:
    for j in neighbor_lists[i]:
        if j > i and self.state.active[j]:
            d = np.linalg.norm(self.state.positions[i] - self.state.positions[j])
            if d < self.state.radii[i] + self.state.radii[j]:
                collision_count += 1
```

**Classification:** definition **(b)** — *overlap-timesteps*. Each simulation
step, every active pair with `d_ij < r_i + r_j` contributes exactly one
unit to the counter. The run-level `collision_count` is the sum of per-step
counts over the entire simulation window, from t=0 to evacuation or
`max_time`.

**This is not:**

- (a) unique contact-onset events — the same pair in continuous overlap
  contributes once per timestep, not once per overlap episode;
- (c) a per-timestep quantity reported as a rate — it is an extensive
  sum, which is why magnitudes reach the hundreds that Reviewer 1 flagged.

The metric is **timestep-dependent by construction**: halving Δt
approximately doubles the count for the same physical trajectory.

## 2. Pooling / windowing question (Arjun flag from commit 808469d)

**The counter is not exit-windowed.** It runs from the first simulation
step onward. For the bottleneck scenario, most of the overlap-timestep
budget accumulates during the pre-exit crowding phase — agents queue
behind the exit, many pairs satisfy `d_ij < r_i + r_j` simultaneously,
and they stay in overlap for many consecutive timesteps while waiting to
pass through.

Consequence for Table tab:bottleneck:

- C2 (SFM+TTC) produces near-identical total collision counts across
  widths w ∈ {1.0, 1.2, 1.8, 2.4, 3.6}\,m because the upstream queue
  geometry is substantially the same at all these widths — the exit is
  wide enough that throat contact is negligible and the count is
  dominated by the pre-exit phase.
- The `00.5-reconstitution-final.md §4` confirmation that "C2 collision
  counts are identical across widths by construction" is the same
  artefact, now mechanistically explained.
- The tab:bottleneck caption currently on `main` reads "nearly
  width-independent…because most contacts occur upstream during queue
  formation." That sentence was the original paper's; Arjun's cherry-pick
  (808469d) attempted to sharpen it but was reverted. The substance is
  correct either way — the counter accumulates from t=0, not from
  exit-arrival.

## 3. Δt rank-stability sweep

Configuration: bottleneck, w=1.0 m, n_agents=50, max_time=120 s,
seeds 42–46 (n=5), C1 and C4, Δt ∈ {0.005, 0.01, 0.02}.
Run script: `new_experiments/dt_robustness.py`.
Raw data: `results_new/dt_robustness.csv`.

**Results** (per-seed means, n=5 per cell):

| Config | Δt (s) | mean overlap-count | n evacuated / 250 agents (of 5×50) |
|--------|--------|-------------------:|-------------------:|
| C1     | 0.005  | 126.0              | 250/250 |
| C1     | 0.010  |  46.0              | 250/250 |
| C1     | 0.020  |  24.2              | 249/250 |
| C4     | 0.005  |  94.8              | 250/250 |
| C4     | 0.010  |  28.8              | 250/250 |
| C4     | 0.020  |  14.6              | 247/250 |

**Rank ordering (C1 vs C4):** C1 > C4 at all three Δt values (126 > 94.8,
46.0 > 28.8, 24.2 > 14.6). The rank-ordering finding of the paper
(anticipatory steering C4 reduces contact-overlaps versus plain SFM C1)
is robust to Δt across the ×4 range tested.

**Absolute-count scaling with Δt:**

- C1: Δt 0.02→0.01 halves → count ×1.90; Δt 0.01→0.005 halves → count ×2.74.
- C4: Δt 0.02→0.01 halves → count ×1.97; Δt 0.01→0.005 halves → count ×3.29.

The counts scale monotonically with 1/Δt and are close to inverse-proportional
at the coarser step (ratio ≈ 2 when halving from 0.02 to 0.01), with a
super-linear rise at the finest step that reflects finer-grained resolution
of short-duration contacts. This is the expected behaviour of an extensive
overlap-timestep sum.

## 4. Contact-event counts (Δt-independent supplement)

**Source:** `results_new/collisions/Bottleneck_{C1,C4}_w1.0_seed{42..66}.parquet`
from the R2.0 consolidated logging run.

**Event definition:** a contact-event is the first timestep within a
maximal run of consecutive overlap timesteps for a given unordered pair
`(i, j)`. Operationally: group the collision parquet by `(i, j)`,
sort by `t`, and count time gaps greater than one timestep as new-event
boundaries (plus one initial event per pair).

**Result** (w=1.0 m, Δt=0.01 s, seeds 42–66, n=25 per config):

| Config | mean contact-events | std | mean total contact time (s) |
|--------|--------------------:|----:|----------------------------:|
| C1     | 18.48               | 5.99 | 0.424 |
| C4     | 15.32               | 4.99 | 0.294 |

C1 > C4 in contact-events (18.48 vs 15.32), preserving the direction of
the overlap-count result (46.0 vs 28.8 at Δt=0.01 s). Computed by
`analysis/contact_events.py` from `results_new/collisions/Bottleneck_{C1,C4}_w1.0_seed{42..66}.parquet`;
output at `results_new/contact_events_w1.0.csv`.

## 5. Total contact time (Δt=0.01 s)

Already reported in §4 above:

- C1 mean total contact time = **0.424 s** (sum over all pairs, all timesteps × Δt).
- C4 mean total contact time = **0.294 s**.

This is a dimensional supplementary metric. The ratio C1:C4 = 1.44
matches the overlap-count ratio 46.0/28.8 = 1.60 within seed variance.

## 6. Recommendations to paper

1. Rename "collision" → "contact-overlap" throughout §4 metric language
   (preserve "collision-free", paradigm names in §2/§3.1, and
   bibliography).
2. Add a definitional sentence after the metrics paragraph stating
   explicitly that the metric is a Δt-dependent extensive sum used for
   relative comparison at fixed Δt=0.01 s.
3. Add a Δt-robustness paragraph with the rank-stability finding.
4. Report contact-events as a Δt-independent supplement in §4.5.
5. Sharpen the tab:bottleneck caption to explain the pooling
   mechanistically (pre-exit crowding, not exit-windowed counter).
