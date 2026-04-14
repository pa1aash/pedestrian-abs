# Decision: Option B accepted for mechanism attribution

Date: 2026-04-14
Supersedes: contribution (ii) as currently written in main.tex §1 and
the "46%/54%" decomposition in the abstract and §4.6.

## What is accepted

Option B from revision-notes/pre-s1-blocker2-sigma-sensitivity.md:
drop the point-attribution decomposition ("46%/54%" or "52%/48%")
entirely and replace with the logistic transition framing.

## Authoritative numbers going forward

All prose sessions (1-20) must cite these values, not any earlier
variants:

- σ₅₀ = 0.0485 m/s, 95% CI [0.044, 0.053] (Clopper-Pearson,
  logistic fit over σ ∈ {0, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07,
  0.10, 0.20}, n = 25 per σ).
- Completion rate at σ = 0.05: 0.52, 95% CI [0.32, 0.72].
- Noise-vs-ORCA attribution ratio: 1.00, 95% CI [0.54, 1.83].
- C1 (plain SFM) at w = 0.8 m, seeds 42-66: 0/25.
- C2 (SFM+TTC) at w = 0.8 m, seeds 42-66: 0/25.
- C3 (SFM+ORCA) at w = 0.8 m: 13/25 (52%).
- C4 (full hybrid) at w = 0.8 m: 14/25 (56%).

Sources: results_new/sigma_sweep.csv (sha256 ce706dbf...),
results_new/sigma_sweep_stats.json, results_analysis/statistical
_reanalysis.csv, figures/sigma_sweep_logistic.pdf.

## What changes in the paper

1. Abstract contribution sentence on mechanism.
   OLD: "A symmetry-breaking control experiment decomposes ORCA's
   deadlock-resolution effect into approximately 46% geometric
   symmetry-breaking and 54% velocity-space optimisation."
   NEW: "A symmetry-breaking control experiment characterises the
   noise threshold for deadlock resolution (σ₅₀ = 0.049 m/s, 95% CI
   [0.044, 0.053]) and finds that passive Gaussian noise at
   σ ≈ σ₅₀ recovers ORCA's deadlock-breaking effect within sampling
   resolution; an n = 25 experiment cannot separate a residual
   velocity-space-optimisation contribution from noise."

2. Abstract deadlock contrast.
   OLD: "resolves arching deadlocks in 56% of trials versus 4% for
   SFM alone" and "TTC anticipation locks symmetric arches at
   narrow exits (0/25 evacuations versus 1/25 for plain SFM)".
   NEW: "at a 0.8 m bottleneck, neither plain SFM nor SFM+TTC
   evacuates any of 25 trials, while ORCA-enabled configurations
   evacuate 52-56%."

3. Contribution (ii) in §1.
   OLD: "A symmetry-breaking control experiment (C1+ε) that
   decomposes ORCA's deadlock-resolution effect into approximately
   46% geometric symmetry-breaking and 54% velocity-space
   optimisation, showing that both mechanisms contribute and
   neither is sufficient alone."
   NEW: "A symmetry-breaking control experiment (C1+ε) that
   characterises the noise threshold for deadlock resolution
   (σ₅₀ ≈ 0.049 m/s) and establishes that within our sample size
   passive Gaussian noise is indistinguishable from ORCA's coordinated
   LP-based velocity selection as a deadlock-breaking mechanism."

4. §4.6 narrative.
   Drop the "approximately 46% / 54%" paragraph and the
   "velocity-space optimisation" framing that follows it. Replace
   with a logistic-fit paragraph reporting σ₅₀ with CI, the full
   sweep table (σ ∈ {0, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.10,
   0.20}, completions/25), and the Option B interpretation. Include
   figures/sigma_sweep_logistic.pdf as a new figure.

5. §5 Discussion.
   Drop the "both mechanisms contribute; neither is sufficient
   alone" sentence. Replace with a sentence acknowledging that
   within n = 25 the residual contribution of velocity-space
   optimisation beyond symmetry-breaking is not separable, and
   flagging larger-n attribution as future work.

6. §6 Conclusion.
   Remove any reference to the 46%/54% decomposition.

## What does NOT change

- The "0/25 for both SFM and SFM+TTC vs 13/25 and 14/25 for
  ORCA-enabled" directional finding. This is load-bearing for the
  diagnostic-ablation contribution and is robust to the Option B
  reframe.
- The zone-decomposed collision analysis in §4.5 (TTC reduces
  upstream queue collisions by 30%). Unaffected.
- The crossing scenario tripling finding in §4.5. Unaffected.
- The bidirectional finding (LMM coef +0.074 m/s). Unaffected.
- The FD calibration result (60.5% RMSE reduction). Unaffected.
- The OOD held-out bias (26-43% underestimation). Unaffected.

## Sessions affected

- Session 1 (abstract): incorporate new contribution sentence and
  deadlock framing as specified above.
- Session 2 (intro + contribution list): rewrite contribution (ii).
- Session 12 (deadlock + σ-sweep): consumes existing sigma_sweep.csv
  and sigma_sweep_stats.json rather than rerunning; write-only
  session. Scope reduced from ~2 hr compute to ~30 min prose.
- Session 15 (Discussion restructure): drop 46%/54% language;
  integrate Option B framing.
- Session 16 (Conclusion): drop any 46%/54% residue.
- Session 19 (final peer-review pass): check that no "46%/54%" or
  equivalent decomposition language remains anywhere in main.tex.

## Sign-off

Recorded by: [user], on behalf of the paper's revision plan.
Blocker references: revision-notes/pre-s1-blocker1-deadlock-vs-sigma0.md,
revision-notes/pre-s1-blocker2-sigma-sensitivity.md.
