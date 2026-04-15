# Figure regen summary

## Task 1 — Figure 1 fresh FD sweep at α-light

**Status:** HALTED before Phase 2 (no sims run).

Timing probe (`scripts/fd_timing_probe.py`, 5 of 6 intended runs completed):

| config | ρ | wall (1 rep) |
|---|---|---|
| C1 | 0.5, 2.5, 5.0 | 1.3 s, 19.2 s, 57.8 s |
| C4 | 0.5, 2.5, 5.0 | 25.1 s, 396 s, ~1188 s (projected) |

Full-sweep projection for 4 configs × 10 bins × 3 seeds: **~16 h**. Budget ceiling 3 h. Halt rule fired. See `revision-notes/task1-halt.md` for the four paths forward (cut scope, reduced protocol, overnight, or keep current figure).

No output written to `results_new/fd_sweep_alight.csv`. No Figure 1 regenerated.

Visual verification: not applicable (no figure produced).

## Task 2 — Figure 2 redesign (sigmoid gate + observed density)

**Status:** Committed `65a26c6` (pushed to main).

**Phase A data source:** hybrid.
- Bottleneck w=1.0 m: raw per-agent-timestep density from `results_new/force_logging/force_C4_w1.0_seed{42..46}.parquet` (n=5 seeds, 55,727 samples). Panel B histogram uses this.
- Crossing, bidirectional: per-agent-timestep density logs not archived. Panel B annotates the gap; paper text notes it.

**Panel B method:** density histogram over bottleneck samples, 160 bins across ρ ∈ [0, 8], normalised to probability density. Overlay: transition-region shaded band [2.9, 5.1] in orange for direct visual comparison with Panel A; vertical dashed line at ρ₀ = 4.0.

Panel A's transition band is at ρ ∈ [2.9, 5.1]; observed max (99.9th percentile) is ρ = 1.56. The distance is visible at a glance — the main communicative goal of the redesign.

**§4.4 rewrite:** subsection retitled from "Force-Magnitude Diagnostic" to "Density-Adaptive Gate and Observed Density Range". Prose leads with the occupancy admission (previously buried after the force-magnitude paragraph). Force-component dominance kept as a single brief sentence. The old pseudoreplication-free force-magnitude band plot is no longer the primary subsection figure; it remains available via `analysis/force_magnitude_and_gate.py` if restored to a supplementary appendix.

**Caption:** updated to the "(A) sigmoid gate; (B) observed density" structure. Explicitly states that crossing / bidirectional density logs are not archived.

Figure filename unchanged: `figures/force_magnitude.pdf`. The `main.tex` `\includegraphics` path is unchanged.

**Cross-session impact:**
- S5/S15 admissions-consolidation target (from `cross-session-flags.md`) shrinks by one: the §4.4 gate admission is now embodied in Figure 2 itself and no longer requires prose that competes with the figure. S15 can collapse the four admission locations more aggressively.

## Halts and resolutions

1. Task 1 compute-budget halt: documented in `revision-notes/task1-halt.md`, awaiting user decision on paths forward.
2. No Task 2 halts.

## Git state at end of session

HEAD = `65a26c6` (Fig 2 redesign commit), pushed to `origin/main`.

Working tree: clean of figure-related changes. Unchecked-in artefacts are prior-session untracked files (results_new/, revision-notes/, scripts/ from S9–S14).
