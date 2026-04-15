# S17 verb softening + cosmetic changes

## Verb softening (judgment-based, per prompt)
- L203 (Table 1 caption, calibration): "sanity sweep ... confirms both are identifiable" → "indicates both are identifiable".
- L320 (§4.5 zonal): "confirming the mechanism is not width-specific" → "consistent with the mechanism being not width-specific".
- L462 (§5 arch lifetime): "and confirm the arching deadlock is a stable force-balance configuration" → "and are consistent with the arching deadlock being a stable force-balance configuration".

## Arjun cosmetic re-applications
- §2: removed stale `% TODO R4: restructure §2 around three failure modes ...` comment (S03 already restructured §2).
- `tab:scenarios` caption: deduplicated `\small` preceding `\scriptsize`. Now only `\scriptsize`.

## Fig 4 caption
Replaced "Red dashed: σ = 0.05, the operating point used in the paper's earlier prose" scratchpad leak. New caption (self-contained):
- Vertical dotted line: σ_50 = 0.049 m/s with 95% CI [0.044, 0.053] as shaded band (Clopper-Pearson on logistic-fit midpoint).
- Horizontal dashed line: C3 completion rate (13/25 = 52%).
- Explanation: "logistic curve intersects C3 reference near σ ≈ σ_50, indicating passive Gaussian noise at the transition midpoint matches ORCA's deadlock-resolution rate within n=25 sampling resolution."

## Notation (no changes needed)
τ-family already unambiguous:
- τ_i (agent relaxation time, §3.1 L110, Table 3 simplified to τ).
- τ_ij (pairwise time-to-collision, §3.1 L133-136).
- τ_0 (TTC decay constant, 3.0 s, Table 3).
- τ_h (ORCA horizon, 5.0 s, Table 3).
- τ_ORCA (ORCA force-conversion relaxation, 0.5 s, §3.1 L114 and L141).
Each defined once on first use, consistent across §3.1 and Table 3.

R (KDTree query radius) defined at §3.1 L114 with R = 3.0 m, referenced by Algorithm 1.

## Grep-clean
- "earlier prose" / "earlier version" / "previously reported" / "originally claimed" / "this paper used to": zero hits in final file.
