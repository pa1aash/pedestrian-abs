# S19 anonymization checklist

## main.tex
- `\author{\authorname{Anonymous Authors}}` — PASS
- `\affiliation{}` empty — PASS
- `\email{}` empty — PASS
- `\hypersetup{pdfauthor={},pdftitle={},...}` empty — PASS
- Grep for "palaash|arjun|gang|veluri|pa1aash|juunnq|bennett|university|anthropic": 0 hits — PASS
- Grep for "github.com|@gmail|orcid|filled ORCID ID": 0 hits — PASS
- Code-release pointer: "Code, data, and reproduction scripts are released with the paper." — no URL, no personal repo — PASS
- Appendix A.1: `commit hash: [anonymized for review]` — PASS

## references.bib
- Grep for project team names: 0 hits — PASS (no self-citations)

## Figure PDF metadata
- All figures: Creator = `Matplotlib vX.Y.Z`, Producer = `Matplotlib pdf backend`. No Author field populated. PASS.

## Project nicknames in code
- CLAUDE.md mentions "CrowdSim Ablation Study" but is not included in the submission — internal only. PASS.

## Verdict
All anonymization checks PASS. No Phase B blocker.
