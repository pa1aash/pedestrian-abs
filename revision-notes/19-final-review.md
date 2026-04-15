# S19 adversarial peer-review (hostile-but-fair SIMULTECH reviewer)

## Summary
**Verdict: minor-revise.** The paper successfully reframes as a diagnostic ablation, honestly reports its calibration and OOD limitations, and resists overclaiming. Three category (c) reproducibility items remain and should be acknowledged in the response letter, but none block acceptance.

---

## Category (a) — novelty overclaim
**None found.** §1 explicitly frames the work as "a diagnostic ablation study, not a new-method paper" and the blend as a "mitigation probe". The three contribution bullets are scoped: zone-decomposed ablation, noise-threshold control experiment, and density-modulated blend *as a mitigation probe*. §5's Oracle paragraph was softened from "subsumes" to "matches or slightly exceeds ... we do not claim subsumption in any stronger sense". The "What this paper does not claim" paragraph at end of §5 is explicit about production-readiness, trajectory-level validation, real-time deployment, OOD generalisation, and the adaptive-gate-as-near-fixed-blend admission.

## Category (b) — statistical/methodological gap not addressed by Appendix A
**None blocking.** Appendix A.6 lists the four statistical procedures and their libraries. The NB GLM / Cox PH / LMM / Holm–Šidák protocol is adequately specified for replication. One potential reviewer objection: Appendix A.6 does not explicitly state how Cox PH handles the complete-separation C2 case (0/25 events) — §4.6 says "reported via Fisher's exact" but appendix A.6 doesn't mirror this. Minor; not blocking.

## Category (c) — reproducibility risk (flagged for response letter)
1. **Per-seed integer counts not archived for crossing and bidirectional scenarios.** §4.5 footnote discloses this and states the NB GLM fallback to ratio-of-means IRR is numerically identical under Poisson dispersion. Appendix A.9 does not list "archived per-seed counts" or explicitly mark them missing. A reviewer could ask: how would I verify your IRR is robust without the raw counts? Response-letter item.
2. **Gate-occupancy density-per-agent-timestep logs archived only for bottleneck w=1.0 m C4.** §4.4 discloses this; appendix A.7 does not explicitly mark it. A reviewer who wants to reproduce the "100% ORCA-dominant, 0% transition" number for crossing/bidirectional will find no archived data. Response-letter item.
3. **results/legacy/ migration not committed to the repo (project-level gitignore on results/).** The archival CSVs for Table 5 and Fig. 4 live on local disk only; the on-disk README documents this. Reviewer downloading the GitHub repo will see results/ absent. Response-letter item, or submit the legacy CSVs through the artefact track (Zenodo DOI if used).

## Category (d) — Option B inconsistency / 46%/54% residue
**None found.** Grep clean across main.tex and bib. All mechanism-attribution language uses the Option B formulation (σ_50 = 0.049 m/s, CI [0.044, 0.053], attribution ratio 1.00 CI [0.54, 1.83], "within n=25 not separable"). Abstract, §1 contribution (ii), §4.6, §5 Limitations, §5 "does not claim", and §6 Conclusion are consistent.

## Category (e) — calibration protocol honesty
**None blocking.** Table 1 caption, §3.3 (calibration methodology), §4.2 (FD validation), and Appendix A.5 all disclose: single-start Nelder–Mead, α-light (A=2000, B=0.08 fixed at textbook), pkill at seed-noise floor (not formal xatol/fatol convergence), 2-parameter subset (γ, ρ_max) only, in-sample RMSE only. A full 4-parameter multi-restart refit is explicitly listed as future work in §6. Table 1's superscript-dagger footnote is a clean reminder of the α-light scope. No honesty gap.

---

## Specific line-level objections

Q1 (line 474, §5 Limitations): "The force-magnitude diagnostic ... locates the empirical crossover |F_SFM| = |F_ORCA| at ρ ≈ 0.07 ped/m², offset from the literature-motivated sigmoid centre ρ_0 = 4.0 by orders of magnitude."
- Objection: A reviewer may ask why we then retain ρ_0 = 4.0 at all. The sentence does justify it ("the two quantities measure different things") but a hostile reviewer may call this post-hoc rationalisation.
- Recommendation: response letter acknowledges the critique and points to the sensitivity-sweep future-work item and the fact that no experiment traverses the transition band.

Q2 (line 445-446, §4.8 and §6 Future Work): paper lists "C/C++ acceleration of the ORCA linear program" as future work; reviewer may ask why this was not done given the paper's real-time framing in §1. The "What this paper does not claim" paragraph already addresses this.

Q3 (line 427, §4.7 external sim): "JuPedSim's C++ core runs approximately 39× faster than our pure-Python implementation; this well-understood performance gap does not affect the diagnostic contributions of this paper." Scoped correctly; OK.

Q4 (line 389-405, Table 5): the collision-count cells repeating across widths is disclosed in the caption but a reviewer may still call the table design confusing. Arjun's rewritten caption is already in place (L383); the appendix cross-reference to the zonal Table 3 is present. OK.

## Bottom line
**Minor-revise.** No (a)/(b)/(d)/(e) halt. Three (c) reproducibility items for the response letter (S21). The paper is internally consistent, honestly scoped, and its numerical results are reproducible with the archived scripts. Not self-fixing; flagging for the user's morning review.
