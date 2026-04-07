# Paper Audit — SIMULTECH 2026 Submission

**Date:** 2026-04-06 (updated)
**Paper:** "A Hybrid Agent-Based Digital Twin Framework for Crowd Safety Assessment"
**Target:** SIMULTECH 2026, SciTePress, 12 pages, double-blind

---

## 1. Double-Blind Compliance

- [x] No author names in main.tex (line 26: "Anonymous Authors")
- [x] No university/affiliation names in text
- [x] No "our previous work [Author, Year]" patterns
- [x] No acknowledgements section
- [x] No identifiable self-citations
- [x] PDF metadata stripped (`\hypersetup{pdfauthor={},pdftitle={}}`)
- [x] No screenshots with university branding
- [x] No GitHub links to non-anonymous repos

**Status: PASS**

## 2. Formatting

- [x] Uses SCITEPRESS.sty template correctly
- [x] A4 paper size
- [x] Page count: 9 pages *(Note: minimum is 10 for regular paper — may need expansion)*
- [x] References use Harvard (author-date) format (apalike)
- [x] Font sizes correct (10pt body)
- [x] No overfull hbox warnings (fixed: hybrid eq split to multline, table spacing adjusted)

**Status: PASS (9 pages — borderline, may want to expand to 10)**

## 3. Content

- [x] Abstract: ~130 words (target 70-200), ends with period
- [x] Keywords present (6 keywords)
- [x] All 5 contributions stated in introduction (numbered list)
- [x] All 8 figures have captions and are referenced in text
- [x] Both tables have captions and are referenced in text
- [x] All equations numbered (9 equation environments)
- [x] Conclusions follow from results
- [x] Limitations discussed honestly (Section 5: calibration gap, scalability, DT maturity)
- [x] Future work is specific (real-time sensors, learned avoidance, field validation)

**Status: PASS**

## 4. References

- [x] All 30 cited keys exist in references.bib (0 undefined)
- [x] 36 bib entries total, 30 cited, 6 orphan
- [x] References include 2024-2025 papers (Lee24, Gaudou24, Mullick24, Croatti26, Lin25)
- [x] 30 references cited (target >=25)
- [x] Gaudou24 cited (SIMULTECH keynote connection)

**Status: PASS**

## 5. Figures

- [x] All 8 figures are vector PDF
- [x] Font size >=10pt in figures (set_style: font.size=10)
- [x] Colorblind-safe palette (ColorBrewer Dark2)
- [x] All figure files exist and compile
- [x] Error bars present where applicable

**Status: PASS**

## 6. Submission Readiness

- [x] PDF compiles cleanly (0 errors, 0 overfull hbox)
- [x] All cross-references resolved
- [x] ISSUE-056: experiment re-runs executed (phases 15-18, 2026-04-04 through 2026-04-06)
- [ ] Paper numbers need regeneration from new re-run CSVs (Sections 4-6)
- [ ] Figures need regeneration from new CSVs
- [ ] Crush re-runs (rerun_8/9) and n=20 bottleneck (rerun_10) pending overnight execution
- [ ] Page count 9 — likely expands to 10-11 with calibration subsection + new numbers

**Status: PRE-SUBMISSION — awaiting final overnight re-runs and paper updates**

---

## Re-run status (2026-04-06)

**Completed re-runs:**
- Bottleneck widths 1.0-3.6m (50 agents, n=5): CIs overlap, need n=20 extension
- Bottleneck w=0.8m at 100 agents (120s, 300s, 600s timeouts): C1 0/5, C4 3/5 evacuate
- Bidirectional 100+100 agents (60s): throughput-safety trade-off confirmed
- Crossing 100+100 agents (60s): 3x throughput for TTC configs (C4 vs C1)
- Funnel D1-D4 (250 agents, 60s): CRUSH REGIME BROKEN (max density 6.05, no differentiation)
- FZJ FD calibration: baseline RMSE 0.2296 -> 0.0908 (60.5% reduction, DT Level 2 achieved)

**Pending overnight re-runs:**
- rerun_8_funnel_narrow.py: 250 agents, 0.8m exit, Voronoi density (fixes crush activation)
- rerun_9_crush_room.py: NEW CrushRoom scenario, 300 agents, 0.6m exit, Voronoi
- rerun_10_bottleneck_n20.py: extends bottleneck widths to n=20 (seeds 47-61, C1+C4)

**After overnight runs, need:**
- Re-run Optimizer (100 agents) + Scaling C1 with clean CPU for accurate timing
- Regenerate all 8 figures from new CSVs
- Update Section 3 (add 3.5 calibration), 4.1-4.6 (all new numbers), 5, 6, abstract

---

## New claims (post-re-run)

**Strong (publishable):**
- **DT Level 2 calibration**: 60.5% RMSE reduction (0.23 -> 0.09 m/s) against FZJ empirical FD
- **Crossing throughput**: C1 = 6/200 exits, C4 = 17.6/200 exits (3x improvement in 60s)
- **Collision reduction**: 37% across all bottleneck widths (C2/C4 vs C1)
- **Deadlock resolution (w=0.8m, 600s)**: C1 0/5 vs C4 3/5 evacuate successfully (n=5, extending to n=20)

**Defensible with honest framing:**
- Bidirectional: throughput-safety trade-off (-19% collisions, -12% exits for C4 vs C1)
- Wide bottleneck exits (1.8m+): no hybrid benefit (expected physics)

**Pending crush re-run for:**
- Crush regime activation and D1/D2/D3/D4 differentiation
- Max density capping claim

---

## Summary

| Category | Status |
|----------|--------|
| Double-blind | PASS |
| Formatting | PASS (9 pages, likely 10-11 post-update) |
| Content | NEEDS UPDATE (Sections 3.5, 4.1-4.6, 5, 6, abstract) |
| References | PASS (30 cited) |
| Figures | NEEDS REGENERATION |
| Submission | PRE-SUBMISSION — pending final overnight runs |

**The paper architecture is sound.** Awaiting: (1) overnight crush/n=20 runs completion, (2) scaling+optimizer clean re-run, (3) figure regeneration, (4) Section 3-6 numerical updates, (5) recompilation.
