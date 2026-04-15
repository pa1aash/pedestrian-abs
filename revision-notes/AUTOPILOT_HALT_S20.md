# S20 HALT — abstract word count over SCITEPRESS limit

**Halt condition:** S20 step 3, "Word count abstract. SCITEPRESS limit
70-200. If over, halt for user to tighten."

**Measurement:** 213 words (target: 70–200). Over by 13 words.

**State at halt:**
- Compile: clean (0 errors, 15 pages = body 14 + appendix 1).
- Bib integrity: clean (no missing cites). 10 orphan bib entries were
  cleaned in S20 (safe removal of uncited entries).
- Forbidden-token grep: clean. Zero hits for "46%", "54%",
  "convex combination", "fully attributable", "real-time venue",
  "digital twin", "STATUS.json", "cannot avoid". "48%" zero hits.
  "52%" hits are all C3 = 13/25 references (rule 5 authorised).
  "validate" surviving hits all in authorised negation scoping
  ("does not validate", "further validation").
- Pinned numerical cross-check: all 22 values present with correct
  digits (see console output from numerical check).
- Anonymization: clean (S19 pass).
- Peer review: minor-revise, 3 category (c) items for response letter
  (S19).

**Not tagged.** The paper is otherwise submission-ready modulo two
user-facing decisions:
1. Tighten abstract from 213 → ≤ 200 words. Candidates for trim
   (judgment required, not autopiloted):
     - Second half of "a symmetry-breaking control experiment
       attributes to perturbation rather than to ORCA-specific
       velocity optimisation ($\sigma_{50} = 0.049$\,m/s, 95\% CI
       $[0.044, 0.053]$); within $n = 25$ we cannot separate a
       residual velocity-space-optimisation contribution from
       noise." could be trimmed to keep the σ_50 finding and drop
       the clause repeating "within n = 25 ...", since the "does
       not separate" idea appears earlier.
     - "The desired-force calibration substantially reduces in-sample
       FZJ speed--density RMSE (see \S\ref{sec:fd-validation})"
       could drop the cross-ref in an abstract context.
     - "Zone-decomposition shows that TTC reduces upstream
       queue-formation contact-overlaps by 30\%" is a §4.5 result
       that may belong only in §1, not the abstract.
2. Page count: body is 14 + appendix 1 = 15 total. SCITEPRESS
   regular-paper cap is 12 pages. Preexisting overrun (entered the
   batch at 14 body pages). Trim strategies in the user's judgment:
     - Collapse some §5 "Discussion" subheadings into one paragraph.
     - Compress §4.7 (External Simulator) — currently verbose.
     - Tighten Limitations paragraph (L474), currently a wall of text.

**What S20 did NOT do (per halt rules):**
- Did not tag `revision-v1-submitted`.
- Did not run `git tag`.
- Did not push an empty "ready for submission" marker commit.

Compile, bib cleanup, and numerical check remain committed to main
and pushed — these are safe preparatory steps. Tagging is deferred
to the user after they tighten the abstract (and optionally trim the
body to 12 pages).

**S20 commit (planned, separate):** compile + bib-cleanup + final
grep notes.
