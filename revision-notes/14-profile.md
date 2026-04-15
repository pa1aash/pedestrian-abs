# S14 cProfile breakdown

## Setup
- Config: C4, 200 agents, 10 s simulation time, seed 42 (Bottleneck w=3.6)
- Source: `scripts/profile_c4.py` → `revision-notes/14-profile.txt`
- Total wall: **319.99 s** for 1001 steps (~319.7 ms/step)
- Hardware: Apple M1, 8 GB RAM, macOS 26.3.1 arm64, Python 3.13.12,
  numpy 2.4.4, scipy 1.17.1, shapely 2.1.2

## Wall-time breakdown (cumulative)

| Category | Wall (s) | % of total |
|---|---|---|
| ORCA (compute_orca_forces, incl. LP + halfplane) | 261.79 | **81.8%** |
| ORCA 2D LP solve alone (solve_2d_lp) | 122.51 | 38.3% |
| ORCA halfplane normal (_halfplane_normal) | 95.16 | 29.7% |
| Crush forces (archived, zero-output but still calls routines) | 28.83 | 9.0% |
| Simulation.step overhead (Euler + bookkeeping) | 6.97 | 2.2% |
| SFM compute_agent_forces | 5.99 | 1.9% |
| TTC compute_ttc_forces | 5.80 | 1.8% |
| KDTree (query_ball_point + init) | 0.52 | 0.16% |
| Voronoi tessellation | <0.1 | <0.03% |
| Wall forces | 0.34 | 0.11% |
| Other (helpers, imports, framework) | ~5 | ~1.6% |

## Top 3 C/C++ acceleration candidates

1. **ORCA 2D LP solve** (`sim/steering/orca.py:solve_2d_lp`) — 38% of wall. 177k calls, ~0.69 ms/call. Rewriting the per-agent incremental-2D-LP in C or vendoring a compiled ORCA library (RVO2 C++) is the single largest win available.
2. **ORCA halfplane normal construction** (`_halfplane_normal`) — 30% of wall. 8.5M calls, ~11 μs/call, dominated by `numpy.linalg.norm` over 2-vectors. Vectorising via explicit `sqrt(dx*dx + dy*dy)` or a Cython inner loop would eliminate most of this.
3. **Crush force loop** — 9% of wall even when the crush output is identically zero (all experiments in the paper set the crush weight to zero). The archived code path is not gated. Trivial optimisation: early-exit when `w_crush == 0`. Not a real-time-enabler but a 10% free speedup.

## Implication for §4.8

- ORCA dominates (82% cumulatively, 38% for the LP proper). C/C++ acceleration of the ORCA loop is the real-time-enabling path.
- SFM + TTC together are <4% of wall. No meaningful speedup from touching them.
- KDTree + Voronoi + wall forces are <0.5% combined. Not hotspots.
- The "Other" 1.6% is small enough that even a pure-Python refactor would not matter.

## Extrapolation disclaimer

C4 was benchmarked to 500 agents (results_new/scaling_C4.csv) because the per-step wall-time at 500 agents is already 6.35 s (1.3 steps / 8 min wall). At 1000 agents, linear-in-agents extrapolation from the 500-agent point predicts ~13 s/step; the ORCA LP's quadratic-in-neighbours cost likely makes it worse. The scaling trend is consistent with the real-time-ineligible conclusion at larger agent counts regardless of the exact extrapolation constant.
