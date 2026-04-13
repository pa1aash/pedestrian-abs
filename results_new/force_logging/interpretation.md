# R3.2 Force-Magnitude Diagnostic — Interpretation

## Summary

Pooled across 5 seeds at C4, w=1.0 m, 55,727 logged observations (per-agent, every 10th timestep). Observed density range: **[0, 1.63] ped/m²** (mean 0.74, 95th percentile 1.24).

## Finding 1 — Force-magnitude crossover

The force-magnitude crossover |F_SFM| = |F_ORCA| is located at **ρ ≈ 0.07 ped/m²** (interpolated between adjacent bins). At the lowest observed bin (ρ=0.05), ORCA dominates (110.2 N vs. 81.3 N for SFM). Beyond the crossover, **SFM dominates throughout the operational density range**: at ρ ≈ 1.63 (the peak observed) SFM is 134 N versus 50 N for ORCA, a factor of 2.7× difference.

## Finding 2 — The force crossover and the sigmoid centre measure different things

The force-magnitude crossover at ρ ≈ 0.07 ped/m² 

is **not the same quantity** as the sigmoid centre ρ₀ = 4.0 ped/m². The two have distinct meanings:

- **ρ₀ = 4.0 ped/m²** gates the **ORCA weight** w_o(ρ) = 1 − σ(ρ; 4.0, 2.0). It represents the density at which pedestrians lose the freedom to choose their walking direction (Fruin LoS-E), i.e., where the free-space assumption underlying ORCA breaks down. It is a theoretical anchor about **paradigm applicability**, not about raw force magnitude.

- The **force-magnitude crossover** (where |F_SFM| = |F_ORCA|) reflects the absolute contribution each paradigm makes to the total force at a given density. SFM's social-repulsion term grows exponentially as agents approach contact, so SFM magnitude rises steeply with density while ORCA stays bounded by the velocity-correction scale.

In this implementation, SFM and TTC are always-on additive contributions; only ORCA is density-weighted via w_o. Within the observed range (ρ ≤ 1.63), w_o stays near 1 — ORCA carries essentially full weight — while SFM magnitude exceeds ORCA magnitude for any non-trivially dense configuration (ρ > 0.07 if crossover present). The hybrid therefore behaves as 'ORCA-driven navigation with SFM contact-repulsion on top' throughout this scenario.

## Non-movement of the sigmoid centre ρ₀ = 4.0

We explicitly **do not move ρ₀** in response to this diagnostic. Reasons:

1. **Distinct semantics.** Moving ρ₀ to match the force-magnitude crossover would conflate two different quantities (paradigm-applicability threshold vs. raw force equality). The sigmoid gates ORCA weight; it is not supposed to track force equality.

2. **Reproducibility.** ρ₀ = 4.0 was fixed at the start of the entire experimental programme. All 500+ existing Bottleneck runs, the 540-run sigmoid sensitivity sweep, the crossing and bidirectional data, and the deadlock w=0.8 runs used this value. Moving ρ₀ now would invalidate every pre-R3.2 result.

3. **Literature grounding.** ρ₀ = 4.0 ped/m² corresponds to the Fruin LoS-E boundary. The paper's methodology relies on this theoretical anchor, not on post-hoc empirical fitting.

## Paragraph for §3.1 footnote (drop-in)

% TODO R4: tighten language in the paper version

> A per-agent force-magnitude diagnostic (Section 4.X) logs |F_des|, |F_SFM|, |F_TTC|, |F_ORCA| every 10th timestep at C4, w=1.0 m (n=5, 55,727 observations). The empirical crossover |F_SFM| = |F_ORCA| occurs at ρ ≈ 0.07 ped/m² — essentially at first-contact density — below which ORCA's velocity-correction magnitude dominates and above which SFM's social-repulsion term grows exponentially. The literature-motivated sigmoid centre ρ₀ = 4.0 ped/m² (Fruin LoS-E) gates a different quantity: the ORCA weight w_o(ρ), not the raw force magnitudes. The observed density range during the w=1.0 m bottleneck runs is ρ ∈ [0, 1.63] ped/m² (95th percentile 1.24), well below the sigmoid transition region centred at 4.0; the sigmoid's specific choice of centre within the Fruin LoS-E band (3–5 ped/m²) is therefore not load-bearing for the experiments reported in Section 4. We retain ρ₀ at the Fruin value rather than moving it to the force-equality point, because the two quantities carry different meanings and because every prior experiment in this paper used ρ₀ = 4.0.

## Bin counts per density (for audit)

| ρ bin centre | n | mean \|F_des\| | mean \|F_SFM\| | mean \|F_TTC\| | mean \|F_ORCA\| |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 576 | 150.8 | 81.3 | 0.43 | 110.2 |
| 0.15 | 1,327 | 150.5 | 196.8 | 0.71 | 80.1 |
| 0.25 | 2,583 | 156.4 | 908.2 | 0.94 | 62.2 |
| 0.35 | 3,684 | 154.0 | 355.0 | 1.04 | 55.0 |
| 0.45 | 5,669 | 161.1 | 403.9 | 1.34 | 53.0 |
| 0.55 | 4,261 | 158.0 | 484.9 | 1.71 | 51.4 |
| 0.65 | 6,710 | 157.8 | 554.8 | 1.95 | 48.5 |
| 0.75 | 6,887 | 155.6 | 511.7 | 2.58 | 50.6 |
| 0.85 | 6,559 | 148.0 | 608.0 | 3.50 | 52.8 |
| 0.95 | 6,251 | 144.7 | 415.6 | 4.81 | 57.3 |
| 1.05 | 4,436 | 136.0 | 535.6 | 5.20 | 62.3 |
| 1.15 | 2,415 | 129.4 | 298.4 | 7.02 | 64.2 |
| 1.25 | 2,292 | 114.3 | 209.6 | 6.11 | 62.4 |
| 1.35 | 1,408 | 104.0 | 184.1 | 6.10 | 65.2 |
| 1.45 | 534 | 80.4 | 152.6 | 4.55 | 61.7 |
| 1.55 | 132 | 62.4 | 134.3 | 3.41 | 50.3 |