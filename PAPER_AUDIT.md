# Paper Audit — Submission Readiness

## 1. Double-Blind Compliance
- [x] No author names anywhere in main.tex (Anonymous Authors placeholder)
- [x] No university/affiliation names in text (empty affiliation)
- [x] No "our previous work" patterns
- [x] No acknowledgements section
- [x] No identifiable self-citations
- [x] PDF metadata stripped (hypersetup pdfauthor={})
- [x] No screenshots with university branding
- [x] No GitHub links to non-anonymous repos

## 2. Formatting
- [x] Uses SCITEPRESS.sty template correctly
- [x] A4 paper size
- [x] Page count: 9 pages (within 8-12 regular paper range)
- [x] References use Harvard (author-date) format (apalike style)
- [ ] Some overfull hbox warnings remain (minor, in equations)

## 3. Content
- [x] Abstract: 86 words (within 70-200), ends with period
- [x] Keywords present (6 keywords)
- [x] All 5 contributions stated in introduction
- [x] All figures have captions, referenced in text (8 figures: fd, ablation, evac_width, traj, heatmap, risk, convergence, scaling)
- [x] All tables have captions, referenced in text (2 tables: params, bottleneck)
- [x] All equations numbered (8 equations)
- [x] Conclusions follow from results (5 quantitative claims, all supported)
- [x] Limitations discussed honestly (calibration gap, ORCA scalability, DT maturity L2)
- [x] Future work specific (sensors, learned ORCA, field validation)

## 4. References
- [x] All 30 \cite{} keys exist in references.bib (no undefined)
- [x] 6 orphan bib entries (Adrian24, Boltes10, FZJ09, FZJ13b, Lerner07, Pellegrini09) — acceptable
- [x] References include 2024-2026 papers (Lee24, Gaudou24, Gatta24, Mullick24, Lin25, Croatti26)
- [x] 30 references (need >= 25)
- [x] Gaudou24 cited (SIMULTECH keynote connection)

## 5. Figures
- [x] All figures are vector PDF
- [x] Colorblind-safe palette (Dark2 from ColorBrewer)
- [x] Error bars present in ablation and evac_vs_width
- [ ] Some figure fonts may be < 10pt (axis labels) — acceptable for SciTePress

## 6. Submission
- [x] PDF compiles cleanly with tectonic (no errors)
- [x] 9 pages (within SciTePress 8-12 page limit)
- [ ] PRIMORIS submission requires user action at insticc.org
