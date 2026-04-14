# Session 04 — Methodology §3.1 Audit (read-only)

Scope: paper/main.tex §3.1 "Hybrid Steering Model" (lines 102–170) vs.
sim/steering/hybrid.py and sim/steering/orca.py.

## 1. Undefined symbols — first appearance in main.tex

| Symbol | First line | Referenced as | Defined? |
|---|---|---|---|
| `τ_ORCA` | line 141 | `F_i^ORCA = m_i (v_i^ORCA − v_i) / τ_ORCA` | NO |
| `v_pref^ORCA` | line 141 (implicit, "preferred velocity") | "velocity closest to the preferred velocity" | NO |
| `R` (KDTree query radius) | line 157 (Algorithm 1) | `query_ball_point(x_i, R)` | NO |

Source values from code:
- `τ_ORCA = 0.5 s` — `sim/steering/hybrid.py:57`, `sim/steering/orca.py:267`, `config/params.yaml:5`.
- `v_pref^ORCA = v_i^0 · ê_i` — `sim/steering/orca.py:328-329` (`v_pref = desired_speeds[i] * goal_dir`).
- `R = 3.0 m` — `sim/core/simulation.py:52,99,106,119`, `config/params.yaml:1` (`neighbor_radius: 3.0`).

## 2. F_des gating — paper vs code (CRITICAL)

**Paper Eq (1), line 112:**
```
a_i = (1 − w_o(ρ_i))·(a_des + a_SFM + a_TTC) + w_o(ρ_i)·a_ORCA + a_wall
```
Claim: convex combination. F_des, F_SFM, F_TTC all gated by `(1 − w_o)`.

**Code, sim/steering/hybrid.py:131-153:**
```python
F  = (1.0 − w_crush)[:,None] * F_desire        # line 131  ← gated by w_crush, NOT w_o
F += self.sfm.compute_agent_forces(...)        # line 134  ← UNWEIGHTED
F += self.ttc.compute_ttc_forces(...)          # line 138  ← UNWEIGHTED
F += w_orca[:,None] * self.orca.compute_...(...)  # line 142 ← additive, weight w_orca
F += w_crush[:,None] * self.crush.compute_...     # line 148 ← only when crush enabled
F += self.wall_forces.compute_wall_forces(...)    # line 153
```

With crush disabled (the paper configuration), `w_crush ≡ 0`, so:
```
F_actual = F_des + F_SFM + F_TTC + w_orca · F_ORCA + F_wall
```

**Disagreement summary.** The implemented blend is *additive*, not a
convex combination. F_des, F_SFM, and F_TTC are at full gain at all
densities; only the ORCA term is density-weighted (and its weight is
not paired with a `(1 − w_o)` reduction of the other terms). Eq (1) as
written misrepresents what C1–C4 actually compute.

This is larger than the F_des-gating question the session prompt
posed. The prompt offered options (a) move F_des outside the gate, or
(b) keep it inside and justify it; neither captures the code, because
SFM and TTC are also outside the gate.

## 3. Recommendation

**Adopt option (a), broadened:** rewrite Eq (1) to match the code.
The paper must describe the simulation. Per CLAUDE.md §13 ("Do not
re-run any experiment to 'improve' … existing data is frozen") and the
session-prompt rule "do not change simulation behaviour", the only
honest fix is to correct the equation, the surrounding paragraph, and
Algorithm 1 line 165 so they describe the additive blend the code
actually executes.

Proposed corrected equation (subject to your approval):
```
a_i = a_des + a_SFM + a_TTC + w_o(ρ_i)·a_ORCA + a_wall
```
with one sentence noting:
- F_des is always present because the goal-seeking signal must persist
  at all densities; ORCA's preferred velocity coincides with v⁰ê_i so
  there is partial double-counting in the low-density regime, which we
  accept as the price of paradigm interoperability.
- The ORCA term is the only density-modulated component; SFM and TTC
  are continuously active. C1–C4 toggle paradigm presence (booleans),
  not gating weights, except that C3/C4 enable `w_o(ρ)`.

Algorithm 1 line 165 must change correspondingly:
```
a_i ← a_des + a_SFM + a_TTC + w_o · a_ORCA + a_wall
```

The phrase "convex combination" in line 110 and §3.1 lead-in (line
105) must be replaced with "density-modulated additive blend" or
similar.

## 4. Other §3.1 prose ↔ code disagreements

- **Line 141 ("preserving the collision-free velocity target while
  enabling smooth blending").** ORCA's collision-free guarantee is a
  property of the *velocity* selected by the LP, not of the force
  obtained by relaxing toward that velocity over `τ_ORCA = 0.5 s`. The
  conversion breaks the guarantee. The paper does not currently
  acknowledge this — the session prompt's Task B item 3 addresses it.
- **Line 149 ("at low density (ρ < 2), ORCA dominates (w_o ≈ 1); at
  high density (ρ > 6), the force-based components dominate
  (1 − w_o ≈ 1)").** The "1 − w_o ≈ 1" framing is consistent with the
  *intended* convex combination but not the implemented additive blend
  (where SFM/TTC are at full gain regardless of `w_o`). This sentence
  needs softening to: "at low density ORCA contributes nearly fully
  (w_o ≈ 1); at high density its contribution decays to zero, leaving
  the force-based components which are continuously active."
- **τ_ORCA hardcoded value:** code default 0.5 s matches
  `config/params.yaml`. No drift between code and config. Safe to cite
  τ_ORCA = 0.5 s in the paper.

## 5. STOP

No edits to main.tex have been made. Awaiting approval to proceed
with Task B per the corrected option (a, broadened).

---

## 6. Task B completion (post-approval)

Edits applied to `paper/main.tex`:

1. **Eq (1) (line 111-113)** rewritten to additive form:
   `a_i = a_des + a_SFM + a_TTC + w_o(ρ_i)·a_ORCA + a_wall`.
2. **Line 105 (§3 lead-in):** "convex-combination" → "density-modulated additive".
3. **Line 110 prose:** "convex combination of accelerations" → "density-modulated additive blend of accelerations". C1–C4 descriptors updated to remove `w_o ≡ 0` mentions where they no longer apply; C4 renamed "full additive blend".
4. **Notation block appended after Eq (1)** declaring `τ_ORCA = 0.5 s` (hybrid.py:57), `v_pref^ORCA = v⁰ ê_i` (orca.py:329), `R = 3.0 m` (simulation.py:52).
5. **ORCA paragraph (line 141)** now cites `v_pref^ORCA` explicitly and contains the disclaimer paragraph: "engineering choice that preserves ORCA's velocity target but does not inherit its formal collision-free guarantee … the blend is empirical."
6. **Regime-interpretation paragraph (line ~149)** rewritten: low density = ORCA roughly full strength alongside unconditional desired/SFM/TTC; high density = ORCA suppressed, steering dominated by SFM + TTC. Added the preservation sentence reflecting the additive form (SFM + TTC unconditional; ORCA mutually-consistent velocity target only when w_o ≈ 1; LP feasibility and SFM detailed-balance are *not* preserved).
7. **Algorithm 1 line 165** updated to the additive form. Caption (line 168) updated to "density-modulated additive steering"; R = 3.0 m noted.
8. **Abstract (line 37):** "density-adaptive convex combination" → "density-adaptive additive blend in which only the ORCA contribution is density-modulated".
9. **§1 Introduction (line 52):** "density-driven convex blend" → "density-modulated additive blend … (only the ORCA term is density-weighted)".
10. **§1 contribution list (line 59):** "density-driven convex blend" → "density-modulated additive blend … only the ORCA contribution is density-weighted".
11. **§1 roadmap (line 62):** "convex-combination methodology" → "density-modulated additive blend methodology".
12. **§4 oracle paragraph (line 428):** "convex combination" → "additive blend".
13. **§6 Conclusions (line 451):** "density-adaptive convex combination" → "density-modulated additive blend … with only the ORCA term density-weighted".
14. **§6 Future Work:** appended the crush-term sentence per session item 4 (chosen placement).

Numeric provenance:
- `τ_ORCA = 0.5 s` ← `sim/steering/hybrid.py:57` and `config/params.yaml:5` (verified consistent).
- `R = 3.0 m` ← `sim/core/simulation.py:52,99,106,119` and `config/params.yaml:1` (verified consistent).
- `v_pref^ORCA = v⁰ ê_i` ← `sim/steering/orca.py:328-329` (`v_pref = desired_speeds[i] * goal_dir`).

Verification sweep:
- `grep -n "convex" paper/main.tex` returns zero hits (verified).
- §3.1 statements now consistent with code: F_des, F_SFM, F_TTC unconditional; only F_ORCA scaled by `w_o`; no claim of LP feasibility preservation; no claim of hysteresis (already addressed by existing limitation sentence at line 440).

Remaining tensions (none blocking):
- Eq (1) abstracts away the `(1 − w_crush)` factor on F_des that exists in code (`hybrid.py:131`). With `crush ≡ 0` in all reported runs this factor is identically 1, so the printed equation matches every reported experiment exactly. The crush sentence in §6 Future Work documents the omission honestly.
- TTC paragraph (line 134) writes the per-pair scalar magnitude `F_TTC` rather than the vector form actually summed in code; this is a pre-existing notational shorthand, not introduced by this session and out of scope.

Compile status: `pdflatex` is not available on this host; LaTeX compile not run. The text edits are syntactically inert (no new packages, no environments, no math-mode boundary changes outside of inline `$…$` and a simple equation body swap). User should run a compile pass before merge.

**Confidence: 4/5.** The paper now describes the simulation. One point withheld for the unverified compile.

Suggested commit message:
```
S04 §3.1 methodology: align eq (1) with code (additive blend),
define τ_ORCA/v_pref^ORCA/R, ORCA-as-force disclaimer, crush TODO

- Rewrite Eq (1) as density-modulated additive blend; drop "convex
  combination" throughout (abstract, §1, §3, §4, §6).
- Update Algorithm 1 line 165 and caption to additive form.
- Add notation: τ_ORCA = 0.5 s (hybrid.py:57), v_pref^ORCA = v⁰ê_i
  (orca.py:329), R = 3.0 m (simulation.py:52).
- ORCA paragraph: state that force-conversion does not inherit
  ORCA's formal collision-free guarantee.
- §3.1 regime paragraph: SFM and TTC unconditional, only ORCA fades.
- §6 Future Work: document the implementation's crush term being
  zeroed in all reported experiments.
- Sources: revision-notes/04-methodology-audit.md.
```

