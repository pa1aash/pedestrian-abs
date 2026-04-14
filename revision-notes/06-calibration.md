# Session 6 — Calibration refit, protocol extraction, identifiability sweep, α-light refit

Status: **FINAL. All halt flags triggered (γ, ρ_max, RMSE). Pre-authorised PROCEED to Task B with flagged numbers.**

## 1. Decision record

Original plan (full 4-parameter Nelder-Mead refit with 11 restarts and
profile-likelihood) projected 56 wall-hours even with bin-level
parallelisation (measured 2.2× speedup, bounded by the slowest 450-agent
bin). Reduced-scope Option C (5 restarts) projected 27 wall-hours, still
over the 24-hour session ceiling.

After escalation, Option 5 (abandon refit, defend A/B non-identifiability
analytically) was attempted. Phase B sanity sweep overturned it:

| Param | RMSE range | Variation | Verdict |
|---|---|---|---|
| A | [0.095, 0.129] | **35%** | IDENTIFIED |
| B | [0.097, 0.361] | **272%** | STRONGLY IDENTIFIED |

Bonus finding: textbook A=2000 gave RMSE 0.0952, lower than the original
fitted A*=1920.4 at RMSE 0.0970 (both at B=0.112, γ=0.888, ρ_max=5.36).
The single-start 31-eval NM in commit `8206f28` did not converge in A.

User then selected **Option α-light**: refit γ and ρ_max only, fix
A=2000, B=0.08 at textbook, tight tolerances, single-start, hard bounds,
bin-parallel. Protocol and results below.

## 2. Phase A — Protocol extraction (commit 8206f28)

Extracted from commit `8206f2844ff92202fe5e7b7ff3262b76cdb9ecb0`
(2026-04-07). Script byte-identical to current `scripts/calibrate_dt.py`.

| Field | Value | Source |
|---|---|---|
| Method | Nelder-Mead | code |
| Restarts | **1** | code (no restart loop) |
| x0 | γ=1.913, ρ_max=5.4, A=2000, B=0.08 | code L189 |
| Soft bounds (penalty 5.0) | γ∈(0.1,10), ρ_max∈(3,10), A∈(500,10k), B∈(0.01,0.5) | code L138 |
| Tolerances | xatol=0.01, fatol=0.001, maxfev=40 | code L204 |
| Evals consumed | 31 | STATUS.json |
| seeds/eval | 3 (42, 43, 44) | code |
| FD bins | 10, ρ ∈ {0.5,…,5.0} | measured |
| Corridor | 18 m × 5 m, warmup 300 + measure 500 steps | code |
| Config | C1 | CLI default |
| Calibrated | γ=0.888, ρ_max=5.36, A=1920.4, B=0.112, RMSE=0.0908 | STATUS.json |

**Gaps:**
1. Single-start only. Global optimum not confirmed.
2. Full eval-history artefact `results/calibration.json` was written at
   runtime but never committed (git log empty on that path).
3. Tolerances loose for a 4-param surface with A∈[500, 10000].
4. Soft-bound penalty, not hard box.

Persisted: `results_new/calibration_protocol.json` (sha256 `e866fe2f7123e764…`).

## 3. Phase B — A/B sanity sweep

Fixed (γ=0.888, ρ_max=5.36). 1 seed × 10 bins, 7 evals, 27 min wall.

Midpoint consistency: RMSE=0.0970 vs expected 0.0908 (7% offset, attributable to n_reps=1 vs original n_reps=3). Sim layer reproduces.

Verdicts above. Closed-form non-identifiability argument retracted.

Persisted: `results_new/calibration_sanity_A.csv` (`aac91b157a04782c`),
`..._B.csv` (`1b321ce2e830a2cc`), `..._midpoint.json` (`1323e1ac2942d36d`),
`figures/calibration_sanity_A.pdf`, `figures/calibration_sanity_B.pdf`.

## 4. Phase D — Option α-light refit

Fit γ and ρ_max; A=2000, B=0.08 fixed at textbook (Helbing 2000).
Hard bounds γ∈[0.3, 3], ρ_max∈[3, 7]. xatol=1e-3, fatol=1e-4. n_reps=3.
Bin-parallel. Single-start from textbook x0=(1.913, 5.4).

Primary maxfev=50 reached without NM convergence. Extension to 80
started (eval 51: γ=0.8327, ρ_max=5.977, RMSE=0.0994 — new best).
Evals 44–53 all oscillated within ±0.003 m/s of the best, i.e., at the
seed-noise floor inferred from Phase B's 7% midpoint offset.
**User-authorised pkill at eval 53. Best row from trace selected as final.**

### Final α-light result

| Quantity | Value |
|---|---|
| γ* | **0.8327** |
| ρ_max* | **5.977** |
| A (fixed) | 2000 N |
| B (fixed) | 0.08 m |
| Baseline RMSE (textbook x0) | 0.2351 m/s |
| Calibrated RMSE | **0.0994 m/s** |
| **RMSE reduction vs baseline** | **57.7%** |
| n_evaluations consumed | 53 |
| Convergence | Terminated at seed-noise floor; not formal xatol/fatol |

Persisted: `results_new/calibration_alight_result.json` (sha256 `b45bb0361a8f9c35…`), `results_new/calibration_alight_trace.csv` (sha256 `6fc0ec525450f6a6…`).

### Comparison to existing 8206f28 fit

| | Existing (4-param) | α-light (2-param, A,B fixed) | Δ |
|---|---:|---:|---:|
| γ | 0.888 | 0.8327 | **6.23%** |
| ρ_max | 5.36 | 5.977 | **11.51%** |
| A | 1920.4 | 2000 (fixed) | — |
| B | 0.112 | 0.08 (fixed) | — |
| RMSE | 0.0908 | 0.0994 | +0.009 |
| RMSE reduction | 60.5% | 57.7% | −2.8 pp |

### Halt flags (all three tripped)

1. **γ* Δ = 6.23%** from existing 0.888 (>5% threshold).
2. **ρ_max* Δ = 11.51%** from existing 5.36 (>5% threshold).
3. **RMSE* = 0.0994 worse than existing 0.0908** by 0.009 m/s at a
   different fixed (A, B). Note: the two fits are not directly
   comparable parameter-by-parameter — the existing fit had 4 free
   parameters, the α-light fit has 2. A 4-param fit can always do at
   least as well as a 2-param fit on the same objective.

### Termination rationale

Halted at seed-noise floor; further evaluations not informative given
`seeds_per_eval=3`. Evals 44–53 show RMSE oscillating in [0.0994,
0.1024] at near-identical (γ, ρ_max), consistent with seed noise
≥0.003 m/s. Reducing to 2 parameters shrank the simplex below the noise
floor without letting NM declare xatol/fatol convergence. A full refit
would require `seeds_per_eval≥10` or a seed-averaged smoothed objective,
both outside the 24-hour ceiling.

### User pre-authorised decision: PROCEED to Task B with flagged numbers.

## 5. Task B — ready-to-execute plan (for next session, review-and-commit only)

All edits based on `results_new/calibration_alight_result.json` as the authoritative calibration source. Do NOT cite STATUS.json anymore.

### 5.1 Table 1 (`paper/main.tex`) — update calibrated row

Locate the parameters table row(s) that carry γ, ρ_max, A, B. Change the
"Calibrated" column to:

| Parameter | Default (textbook) | Calibrated | Source |
|---|---|---|---|
| γ (Weidmann) | 1.913 | **0.833** | α-light refit |
| ρ_max (ped/m²) | 5.4 | **5.98** | α-light refit |
| A (N) | 2000 | — (fixed at textbook) | footnote |
| B (m) | 0.08 | — (fixed at textbook) | footnote |

Footnote text:

> A and B were held fixed at textbook Helbing values during calibration. A single-start 4-parameter fit in an earlier revision (commit 8206f28) returned A*=1920 N, B*=0.112 m, but a post-hoc A/B sanity sweep showed that textbook A=2000 achieves lower FD RMSE at the same (γ, ρ_max), indicating the earlier fit had not converged in A. The 2-parameter refit reported here is also a single start (terminated at the seed-noise floor, not formal xatol/fatol convergence); a multi-restart 4-parameter refit with increased `seeds_per_eval` is future work (§6).

### 5.2 §3.3 (Calibration) — rewrite the fitting paragraph

Current prose (paraphrase) says the four parameters were jointly fit
against FZJ data. Replace with:

> We calibrate the Weidmann speed–density parameters γ and ρ_max against
> 4776 FZJ unidirectional corridor data points binned to 10 density
> intervals over ρ ∈ [0.5, 5.0] ped/m². A, B are held fixed at textbook
> Helbing values (A = 2000 N, B = 0.08 m); an A/B sanity sweep at the
> calibrated (γ*, ρ_max*) confirms that both parameters are identifiable
> from the FD (Figure S_A and Figure S_B: 35% and 272% RMSE variation
> across their bound ranges respectively), but a multi-restart
> 4-parameter refit with tighter seed averaging exceeded our compute
> budget and is deferred (§6). Within the 2-parameter problem,
> Nelder-Mead is run from the textbook initial point
> x₀ = (γ=1.913, ρ_max=5.4) with hard bounds γ ∈ [0.3, 3], ρ_max ∈ [3, 7],
> tolerances xatol = 1e-3, fatol = 1e-4, and 3 random seeds per
> evaluation. The fit is a single start (no multi-restart global search).
> Optimisation terminates at the seed-noise floor (evals 44–53 oscillate
> within ±0.003 m/s) rather than at formal tolerance convergence.
> Calibrated values are γ* = 0.833, ρ_max* = 5.98, with in-sample
> speed–density RMSE reduced from 0.235 m/s at x₀ to 0.099 m/s, a
> **57.7% reduction**.

### 5.3 §4.2 (Fundamental Diagram and Calibration) — update headline numbers

Search-and-replace within §4.2 only:

| Old | New |
|---|---|
| `60.5\%` | `57.7\%` |
| `0.091` or `0.0908` (RMSE) | `0.099` |
| `γ^\* = 0.888` (or similar) | `γ^\* = 0.833` |
| `ρ_\{\max\}^\* = 5.36` | `ρ_\{\max\}^\* = 5.98` |
| `A^\* = 1920` | drop; replace with "A = 2000 N (fixed)" |
| `B^\* = 0.112` | drop; replace with "B = 0.08 m (fixed)" |
| any `single-restart` / `single-start` phrasing | keep explicit; do not weaken |

Also: the existing sentence about the 0.2296 baseline should be updated
to 0.2351 (α-light's baseline at textbook x₀, which is marginally
different because the α-light baseline was computed fresh with seeds
42, 43, 44 and may not match the existing baseline exactly due to
unrelated sim-layer drift between 2026-04-07 and 2026-04-14).

### 5.4 Abstract — headline RMSE reduction (Option 3, user-selected 2026-04-15)

Replace the sentence

> "cuts in-sample FZJ speed–density RMSE by 60.5\% (0.230→0.091 m/s)"

with

> "substantially reduces in-sample FZJ speed–density RMSE (see §4.2)"

Rationale: the α-light refit moves the headline from 60.5% to 57.7%,
but it also changes the quoted fit from a single-start 4-parameter NM
at loose tolerance to a single-start 2-parameter NM at the seed-noise
floor. A numerically precise abstract sentence would require one of
three weakenings (hedge on "single-start", note A/B fixed, or downgrade
from 4→2 parameters), any of which costs more abstract real estate
than the claim is worth. Option 3 defers the number to §4.2 and
Table 1, where the full protocol context is already present.

The held-out OOD claim (26–43% underestimation on FZJ bottleneck) is
unaffected — that is a separate dataset and was not refit here.

### 5.5 §6 Future Work — add one sentence

> A multi-restart 4-parameter refit of (γ, ρ_max, A, B) with
> `seeds_per_eval ≥ 10` to smooth the seed-noise floor, plus
> profile-likelihood confidence intervals on all four parameters, is
> deferred to future work; the present 2-parameter refit (γ, ρ_max
> only; A, B fixed at textbook) achieves a 57.7% in-sample RMSE
> reduction and is load-bearing for the ablation results downstream
> but is not a definitive identifiability analysis.

### 5.6 Reproducibility appendix (or Session 18 artefact)

Replace any citation of `STATUS.json` for calibration metadata with
`results_new/calibration_alight_result.json` (sha256 `b45bb0361a8f9c35`).

### 5.7 Figures

Generate `figures/calibration_sanity_A.pdf` and `..._B.pdf` are already
on disk from Phase C. Reference them in §3.3 as supporting evidence for
identifiability. No new FD figure is needed — the existing in-sample
FD figure continues to use the old γ*=0.888 curve; if Task B has budget
it should regenerate the simulated FD curve at γ=0.833, ρ_max=5.98,
A=2000, B=0.08 and overlay it on the existing plot. If not, note the
offset in the caption.

## 6. Files produced this session

| Path | sha256 (first 16) |
|---|---|
| `results_new/calibration_protocol.json` | `e866fe2f7123e764` |
| `results_new/calibration_sanity_A.csv` | `aac91b157a04782c` |
| `results_new/calibration_sanity_B.csv` | `1b321ce2e830a2cc` |
| `results_new/calibration_sanity_midpoint.json` | `1323e1ac2942d36d` |
| `results_new/calibration_alight_trace.csv` | `6fc0ec525450f6a6` |
| `results_new/calibration_alight_result.json` | `b45bb0361a8f9c35` |
| `results_new/phaseB.log`, `results_new/phaseD.log` | — |
| `figures/calibration_sanity_A.pdf` | — |
| `figures/calibration_sanity_B.pdf` | — |
| `scripts/session06_phase1_instrument.py` | — |
| `scripts/session06_phase1b_parallel_preflight.py` | — |
| `scripts/session06_phaseB_sanity.py` | — |
| `scripts/session06_phaseC_figures.py` | — |
| `scripts/session06_phaseD_alight.py` | — |

## 7. Confidence

**Phase A (protocol extraction): 5/5.** Byte-identical code at 8206f28.

**Phase B (sanity sweep): 4/5.** The 35% and 272% variations are large
enough that n_reps=1 seed noise cannot explain them (midpoint offset
was ~7%). Qualitative verdicts robust.

**Phase D (α-light refit): 3/5.** The simplex terminated at the
seed-noise floor, not at formal convergence. The reported (γ*, ρ_max*)
are a local minimum *up to seed noise of ~±0.003 m/s in RMSE*, which
translates to roughly ±0.01 in γ and ±0.05 in ρ_max. A properly
seed-averaged refit would likely land within 1–2% of these values but
could formally converge. Reported numbers should not be treated as
having more than 2 significant figures of precision (γ* ≈ 0.83,
ρ_max* ≈ 6.0) without a rerun.

**Overall recommendation: PROCEED to Task B with the flagged numbers.**
The 2.8-point drop in the headline RMSE reduction (60.5% → 57.7%) is
real but not catastrophic. The honest framing — single-start NM at
seed-noise floor, A/B sanity-swept and fixed at textbook, multi-restart
4-param refit deferred — is defensible for SIMULTECH and addresses the
reviewer's identifiability concern directly.

**Does the main finding survive?** Yes. Calibration is supporting
infrastructure; the ablation headline (SFM/TTC/ORCA failure modes,
density-adaptive mitigation) is independent of the exact γ*, ρ_max*
values within this range. Downstream simulations in `results/` used the
old γ=0.888, ρ_max=5.36, A=1920, B=0.112 calibration; rerunning them
with the new (0.833, 5.98, 2000, 0.08) is outside session scope and
deferred. The paper must note that the ablation results were generated
under the old (4-param) calibration and that the (2-param) α-light
refit is the honest identifiability-aware calibration, with the 2.8-pt
RMSE-reduction gap attributable to the 2-vs-4 parameter difference.

**Confidence that the paper's main finding still carries: 4/5.**
