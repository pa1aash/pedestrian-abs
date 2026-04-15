# S9 OOD per-paradigm decomposition

Source: results_new/ood_per_paradigm.csv (C1, C4) and results_new/table5_rerun_correct.csv (C2, C3); 50 agents per run, seeds 42-66 paired.

## Table

| Width (m) | Config | n | J_sim mean (ped/s) | J_sim sd | J_emp (ped/s) | rel err |
|---|---|---|---|---|---|---|
| 2.4 | C1 | 25 | 3.057 | 0.157 | 5.125 | -40.3% |
| 2.4 | C2 | 25 | 3.069 | 0.148 | 5.125 | -40.1% |
| 2.4 | C3 | 25 | 3.11 | 0.157 | 5.125 | -39.3% |
| 2.4 | C4 | 25 | 3.118 | 0.177 | 5.125 | -39.1% |
| 3.6 | C1 | 25 | 3.853 | 0.204 | 6.939 | -44.5% |
| 3.6 | C2 | 25 | 3.84 | 0.236 | 6.939 | -44.7% |
| 3.6 | C3 | 25 | 3.969 | 0.226 | 6.939 | -42.8% |
| 3.6 | C4 | 25 | 3.923 | 0.211 | 6.939 | -43.5% |

## Interpretation

- **w = 2.4 m**: C4 closes the bias most (|rel_err| = 39.1%); C1 is furthest from empirical (|rel_err| = 40.3%).
- **w = 3.6 m**: C3 closes the bias most (|rel_err| = 42.8%); C2 is furthest from empirical (|rel_err| = 44.7%).

## Does the bias narrow with width, per configuration?

- **C1**: |rel_err| goes from 40.3% at 2.4 m to 44.5% at 3.6 m — bias widens with width.
- **C2**: |rel_err| goes from 40.1% at 2.4 m to 44.7% at 3.6 m — bias widens with width.
- **C3**: |rel_err| goes from 39.3% at 2.4 m to 42.8% at 3.6 m — bias widens with width.
- **C4**: |rel_err| goes from 39.1% at 2.4 m to 43.5% at 3.6 m — bias widens with width.

## Protocol comparability note

The aggregate §4.3 OOD bias (-26% to -43% across 5 widths) uses n_agents = 100; this per-paradigm decomposition uses n_agents = 50 for consistency with the Table 5 protocol. Mixing cell counts is acceptable because we report *relative* errors per cell, not pooled counts. The per-cell J_sim will differ quantitatively between the two protocols (higher congestion at n=100 widens the empirical gap); the diagnostic we extract is *which configuration closes the bias most*, which is protocol-independent at the qualitative level.

## Paper edits triggered

- Extend Table 3 at rows w=2.4 and w=3.6 with J_sim for C1, C2, C3, C4; retain aggregate-only entries for w=3.0, 4.4, 5.0.
- Add §4.3 paragraph 2 summarising which paradigm closes the bias and whether the bias narrows with width.
- Add §5 Limitations sentence noting 3 of 5 widths remain at aggregate-only protocol.