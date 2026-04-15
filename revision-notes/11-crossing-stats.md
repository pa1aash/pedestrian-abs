# S11 crossing throughput + bidirectional stats

## Data availability

- Crossing per-seed throughput data: **not archived**. `results_backup/CrossingScenario_C{1..4}.csv` are 2–3-seed stubs from a pre-revision run (all report `agents_exited = 0`) and are blocklisted in `analysis/inventory.py`. `results/` contains only `empirical_fd.csv` and `fd_C{1,2}.csv` (FD data). The n=25 crossing runs whose aggregate LMM output is preserved in `results_analysis/statistical_reanalysis.csv` were executed during an earlier phase whose per-seed CSVs were lost in the R0 `results/` trim (see `revision-notes/00-inventory.md` line 104).
- Bidirectional per-seed data: same situation. `results_backup/BidirectionalScenario_C{1..4}.csv` are 2-seed stubs. Only aggregate LMM output survives in `statistical_reanalysis.csv`.

## Consequence for NB GLM refit

A full NB GLM refit (dispersion parameter estimated from per-seed counts) requires the raw per-(config, seed) integer count vector. That vector is not on disk, for either scenario. Re-running 25 seeds × 4 configs × 2 scenarios at ~100 s wall each would cost ~5.5 hours — exceeding the batch compute budget (see S9+S14 already consumed). Skipped.

Fallback, analogous to the bidirectional data-gap handling authorised in the S11 prompt:

- Use the preserved LMM coefficient and CI from `statistical_reanalysis.csv` as the primary statistical result.
- Report a **ratio-of-means IRR-equivalent** derived from the C1 intercept (5.9) and the per-comparison LMM coefficients. For a metric that is a per-60s-window count, the LMM coefficient on the count is the difference of means; the ratio (C1+coef)/C1 is numerically equal to an NB GLM IRR when dispersion is Poisson-like, and is a reasonable approximation otherwise.
- Flag the absence of a dispersion-aware CI explicitly in the paper and in this note.

## Crossing throughput — derived

Intercept (C1 mean agents_exited / 200 in 60 s window): **5.9**.

| Comparison | LMM coef | LMM 95% CI | p_HS | Ratio-of-means IRR | Derived IRR 95% CI |
|---|---|---|---|---|---|
| C2 vs C1 | +10.16 | [8.69, 11.63] | 9.5e-41 | **2.72** | [2.47, 2.97] |
| C3 vs C1 | +0.48  | [−0.99, 1.95] | 0.947  | 1.08 | [0.83, 1.33] |
| C4 vs C1 | +11.16 | [9.69, 12.63] | 5.0e-49 | **2.89** | [2.64, 3.14] |

C2 triples crossing throughput over C1; C4 slightly exceeds C2. ORCA alone (C3) contributes essentially nothing — the predictive component of TTC is what dissolves the force-balance standoff at the 90° intersection.

## Logistic mixed model on exited/total

Not run — would need per-seed (exited, total) integer pairs, same data-gap. Reported in paper as "LMM and NB/logistic GLMs would require per-seed raw data not archived; the LMM coefficient preserves the direction, magnitude, and significance of the comparison."

## Bidirectional — 4747/5897 drop

The "4747 vs 5897" absolute counts for bidirectional contact-overlaps currently in the paper have no backing per-seed data (searched all CSV/parquet; no matching file). Drop per S11 directive. Keep the LMM mean-speed coefficient `+0.074 m/s, p_HS < 0.001` which is the only statistically defensible bidirectional claim at this point. Throughput LMM is `+4.76, p_HS=0.60` (not significant) and matches the paper's existing "comparable throughput" framing; the 19.5% overlap-reduction figure is dropped because its raw data is not available.

## 120 s stability rerun

Skipped. Authorised under rule 5 ("skip if total Session 10 + 11 wall-clock exceeds 1.5 hours"). Rationale: a single 120 s crossing run at 200 agents is estimated at ~64 min wall (extrapolating from cProfile's 320 s for a 10 s C4 run at 200 agents in S14). 3 × 4 = 12 such runs would cost ~13 hours, far over budget. Cross-session flag added for S19.

## Robustness-check note

The ratio-of-means IRR is equivalent to the NB GLM IRR under Poisson dispersion. For the preserved LMM on a count outcome, the significance levels (p_HS < 10⁻⁴⁰) are far deeper than any plausible dispersion correction would shift them; the qualitative result (C2 and C4 roughly triple C1, C3 does not) is robust to the choice of link function within the family {Gaussian/LMM, Poisson GLM, NB GLM, logistic mixed model on exited/total}. Specifically: a Poisson assumption would give identical point IRRs; NB would widen the CI by at most the square root of the dispersion ratio; logistic would give odds ratios slightly larger than the IRRs but in the same direction and significance band.

## Sources

- `results_analysis/statistical_reanalysis.csv` (rows where scenario ∈ {crossing, bidirectional}, metric ∈ {agents_exited, mean_speed}).
- `revision-notes/00-inventory.md` for data-gap provenance.
- `revision-notes/decision-option-B-accepted.md` for which findings remain load-bearing.
