# HALT — Figure 1 regen cannot proceed Path A

Date: 2026-04-15 (post-revert, Path A attempt).

## Reason

Rule 8 of the prompt fires: **the new figure's simulated points differ materially from the pre-revert figure**. Specifically the C3 and C4 panels in my regenerated candidate are essentially empty, while the pre-revert (HEAD) Figure 1 shows dense coloured column-scatter for both.

## Evidence

Rendered both PDFs at 300 dpi to `/tmp/fd_orig_hi-1.png` (HEAD) and `/tmp/fd_cand_hi-1.png` (my Path A candidate):

- **C1 (SFM only)**: original = dense green columns to ρ ≈ 5; candidate = identical. ✓
- **C2 (SFM+TTC)**: original = dense orange columns to ρ ≈ 5; candidate = identical. ✓
- **C3 (SFM+ORCA)**: original = dense purple columns to ρ ≈ 5; candidate = **empty** (only 15 rows exist in `results_backup/fd_C3.csv`, all at ρ < 1, alpha=0.3 renders invisibly).
- **C4 (Full hybrid)**: original = dense pink columns to ρ ≈ 5; candidate = **a tiny pink smudge at ρ ≈ 0.8** (only 6 rows in `results_backup/fd_C4.csv`, all at ρ < 1).

## Git archaeology

Searched every commit that ever touched `fd_C3.csv` or `fd_C4.csv`:

```
9762177 pre-rerun snapshot: backup old results, update figures and paper audit
890d059 add fd_C4, Crush D3, Bottleneck C3 results
b935620 logic audit: continuous injection FD, empirical FD fix, ...
```

Blob sizes at every recorded version:

| Commit | results/fd_C3.csv | results/fd_C4.csv | results_backup/fd_C3.csv | results_backup/fd_C4.csv |
|---|---|---|---|---|
| 9762177^ (pre-snapshot) | 16 lines (15 rows) | 16 lines (15 rows) | — | — |
| 9762177 | — | — | 16 lines (15 rows) | 7 lines (6 rows) |
| 2be7d43 (= current HEAD) | — | — | 16 lines (15 rows) | 7 lines (6 rows) |

**fd_C3 has never been larger than 15 rows in any commit; fd_C4 has never been larger than 15 rows in any commit** (and was trimmed to 6 in the snapshot). Yet the pre-revert PDF shows C3 and C4 scatter at comparable density to C1/C2 (which have 360 rows each), spanning ρ ∈ [0, 5].

Conclusion: the C3/C4 data that produced the pre-revert Figure 1 was generated at some point, plotted into the PDF, **then never committed to git** — neither to `results/` nor to `results_backup/`. The PDF persists as a binary artefact but its source CSVs are not reachable from HEAD.

## Why Path A is blocked

Path A ("keep the original CSVs, change only the Weidmann overlay") requires the original CSVs to be loadable. They are not. Using the 15-row / 6-row backup files as substitutes produces the visually different result shown in the candidate PNG (C3 and C4 panels empty). That violates rule 8.

## Decision requested

Three ways forward, user's call:

1. **Locate the lost CSVs** — are they on a backup disk, in a stash, in a branch not yet merged, or in an un-git-tracked directory on this machine? If yes, restore them to `results/` (or a `results_new/fd/` subfolder) and rerun Path A.
2. **Rerun the FD sweep for C3 and C4** — the code exists (`scripts/generate_figures.py → fig1_fd`, which loads from CSV but the original FD sim lived in `scripts/run_experiments.py` / `sim/experiments/`). This violates the "no new sims" constraint in this prompt but is what the data loss requires.
3. **Keep the existing pre-revert Figure 1 unchanged** — accept that the Weidmann overlay on the figure remains at textbook values while the paper text now describes the α-light calibration, and flag the discrepancy in a caption / §4.2 footnote. The figure's main claim (C1–C4 are FD-identical) is independent of which Weidmann curve is overlaid.

Did not commit. Working tree is back to HEAD (reset state).

## Artefacts preserved for review

- `/tmp/fd_orig_hi-1.png` — pre-revert Figure 1 at 300 dpi
- `/tmp/fd_cand_hi-1.png` — Path A candidate at 300 dpi

Both PNGs are in /tmp only (not committed); delete at will.
