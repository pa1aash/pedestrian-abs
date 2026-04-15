# S10 force-magnitude + gate-occupancy

## Figure 2 regenerated

- Source: results_new/force_logging/force_C4_w1.0_seed{42..46}.parquet (n=5 seeds)
- Method: per-seed median per log-spaced density bin; across-seed mean ± 1 sd
- Output: figures/force_magnitude.pdf

## Band quality (relative sd = across-seed sd / across-seed mean)

- mag_des: median relative sd = 0.075
- mag_sfm: median relative sd = 0.088
- mag_ttc: median relative sd = 0.197
- mag_orca: median relative sd = 0.145

5-seed bands are adequate where the components separate by orders of magnitude (SFM vs ORCA at ρ>0.5). Near the ρ≈0.07 crossover, SFM sd is comparable to its median, but the crossover location (SFM ≈ ORCA) is bracketed unambiguously by the ordering of the point estimates across bins. A larger-n rerun would tighten bands near the crossover; this is future work, not run here.

## Gate occupancy

| Scenario | w_o>0.9 (ORCA-dominant) | w_o<0.1 (force-dominant) | 0.1–0.9 (transition) | N agent-timesteps |
|---|---|---|---|---|
| bottleneck_w1.0 | 1.0 | 0.0 | 0.0 | 55,727 |
| crossing | NA | NA | NA | 0 |
| bidirectional | NA | NA | NA | 0 |

Bottleneck w=1.0 m (C4, n=5 seeds, 55,727 samples): w_o>0.9 = 100.0%, w_o<0.1 = 0.0%, transition = 0.0%.

Crossing and bidirectional scenarios: archived agent-timestep density logs were not persisted during the original S0 runs (force_logging/ is bottleneck-only). Reported as data-gap; the paper text uses the bottleneck percentages and flags the gap.
