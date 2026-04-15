# Task 1 HALT — fresh FD sweep projected >3 hour budget

Date: 2026-04-15.

## Timing probe results

Ran `scripts/fd_timing_probe.py` (6 single-rep runs):

| config | ρ (ped/m²) | n_agents | wall (s) |
|---|---|---|---|
| C1 | 0.5 | 45  | 1.3 |
| C1 | 2.5 | 225 | 19.2 |
| C1 | 5.0 | 450 | 57.8 |
| C4 | 0.5 | 45  | 25.1 |
| C4 | 2.5 | 225 | 396.0 |
| C4 | 5.0 | 450 | ~1188 (projected; killed after 18 min elapsed) |

## Full-sweep projection

Protocol requested: 4 configs × 10 bins (ρ = 0.5…5.0 step 0.5) × 3 seeds = 120 runs.

Per-config wall (estimated by integrating the probe points, linear-in-n_agents):

- C1: ~16 min
- C2: ~25–32 min (TTC ~1.5–2× C1)
- C3: ~7–8 h (ORCA 29–36× overhead, per S14 cProfile; higher at 450 agents because of quadratic neighbour cost)
- C4: ~7–8 h

**Total projected: ~16 hours.** Budget ceiling per prompt rule: 3 hours. Projection exceeds by >5×.

Rule from prompt: "> 3 hours projected → halt and report." Task 1 halted before starting Phase 2.

Probe process killed after 5 of 6 data points collected (C4 ρ=5.0 not run to completion; projection uses linear extrapolation from C4 ρ=2.5).

## Paths forward (for user decision)

1. **Cut scope**: drop C3 and C4 (the ORCA-enabled configs) from the fresh sweep; run C1 and C2 only. Combined ~48 min. Retain the existing C3/C4 figure scatter from HEAD (which is visually identical to bf7ae59's PDF that was restored earlier — the "lost" dense data). This is a compromise: fresh Fig 1 is accurate for C1/C2, provenance-gap-tagged for C3/C4.
2. **Run reduced protocol**: 1 seed per bin (not 3), 5 bins (ρ ∈ {0.5, 1.5, 2.5, 3.5, 5.0}) instead of 10. Total 4 × 5 × 1 = 20 runs. C3 and C4 still dominate wall but with ~1/6 the total volume: ~2.5 h. Just under budget, single-seed data is noisier.
3. **Run overnight** (not authorised under current unattended session): user explicitly approves 16 h wall if willing to leave the machine.
4. **Keep the current (visually-correct, provenance-opaque) Figure 1** and move on.

Task 2 proceeds independently.

## Artefacts

- `scripts/fd_timing_probe.py` (new; minimal script; safe to delete)
- `/tmp/fd_probe.log` (probe output)

No sims written to `results_new/`. No git state modified by Task 1.
