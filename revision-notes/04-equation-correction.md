# Equation (1) correction — Session 4

Date: 2026-04-14
Sessions: 4
Commit: [fill in after commit]

## What changed

§3.1 Eq (1) was corrected from a convex combination to an additive
blend to match the simulation code.

OLD (paper, pre-Session-4):
  a_i = (1 - w_o(ρ_i)) · (a_des + a_SFM + a_TTC)
        + w_o(ρ_i) · a_ORCA + a_wall

NEW (paper, post-Session-4, matches code):
  a_i = a_des + a_SFM + a_TTC + w_o(ρ_i) · a_ORCA + a_wall

## Why

Session 4 audit (revision-notes/04-methodology-audit.md) found the
paper's equation did not match hybrid.py:131-153. The code implements
an additive blend where SFM and TTC are unconditional and only ORCA
is density-modulated. F_des is gated in code by (1 - w_crush), which
is identically 1 in all reported experiments (crush mode off).

The correction was made to the paper, not to the code. CLAUDE.md
prohibits silent changes to simulation behaviour; the paper was
wrong, the code was right.

## Scientific implications

- The low-density regime story changes: ORCA operates alongside
  full-strength SFM and TTC rather than dominating them.
- The high-density regime story is unchanged: ORCA fades out, SFM
  and TTC dominate.
- The "goal-seeking delegated to ORCA at low density" narrative
  from pre-Session-4 drafts is retracted; F_des is always active
  in reported experiments.
- No reported numerical result is affected. The code behaviour is
  unchanged. Only the paper's description of the code is corrected.

## Sections edited

- Abstract: "convex combination" → "density-modulated blend"
- §1 contribution (iii): same rename
- §3.1: Eq (1), regime paragraph, notation block, ORCA disclaimer,
  preservation sentence
- Algorithm 1: line 165 and caption
- §4: any residual "convex combination" phrasing
- §6 Future Work: one sentence disclosing the crush gate is supported
  but unused in reported experiments

## Response-letter flag

Session 21 must acknowledge this correction in the response letter.
Reviewers running the released code against the submitted paper
would otherwise notice the equation discrepancy. Recommended framing:
"During revision we identified that the paper's description of the
hybrid steering equation did not match the code implementation; we
have corrected the paper to match the code. No reported numerical
result is affected."

## Audit trail

- revision-notes/04-methodology-audit.md (Task A audit + Task B
  completion section)
- This file (decision record)
- Commit [hash] on fix/S04-methodology
