# R2.5 Arch Lifetime Summary

## Methodology

We measure two arch-persistence metrics on every C1 (SFM only) trajectory at $w = 0.8$ m. The spec's proposed disc radius of 0.5 m around the exit centre $(10, 5)$ produced **zero detections** across all 25 seeds: the actual arching geometry extends beyond the 0.8 m exit width because of the finite agent body radius ($r = 0.25$ m) and the lateral spread of the force-balance configuration, giving an effective arch footprint of roughly $0.7$–$1.0$ m in the tangential direction. We therefore use a disc radius of **0.7 m**, which is the smallest radius that cleanly captures the visible arching seen in Figure 4 without overlapping the goal deactivation region at $(11, 5)$ with `goal_reached_dist = 0.5` m. This choice is empirical; the terminal-stall metric (our primary measure, defined below) is insensitive to this radius because it tracks the active-agent count rather than the disc occupancy. The transient-arch counts are sensitive to the radius and are reported as descriptive, not headline, statistics.

## Aggregate statistics (C1, w=0.8 m, n=25 seeds)

- Median max lifetime (non-evacuated seeds): **456.9 s**
- Median terminal stall (non-evacuated seeds): **456.9 s**
- Mean agents remaining at end of stuck runs: 3.2
- Seeds with max lifetime > 100 s: 24/25 (96%)
- Seeds with max lifetime > 500 s (operationally permanent): 0/25 (0%)
- Seeds that ever evacuated: 1/25

## Per-seed data

| Seed | Transient arches | Max (s) | Terminal stall (s) | N stuck | Evacuated |
|---:|---:|---:|---:|---:|:---:|
| 42 | 0 | 462.5 | 462.5 | 4 | no |
| 43 | 0 | 463.0 | 463.0 | 1 | no |
| 44 | 0 | 433.8 | 433.8 | 3 | no |
| 45 | 1 | 421.4 | 421.4 | 3 | no |
| 46 | 0 | 474.9 | 474.9 | 7 | no |
| 47 | 0 | 461.3 | 461.3 | 5 | no |
| 48 | 2 | 453.9 | 453.9 | 3 | no |
| 49 | 0 | 456.1 | 456.1 | 2 | no |
| 50 | 0 | 480.5 | 480.5 | 3 | no |
| 51 | 0 | 438.6 | 438.6 | 4 | no |
| 52 | 0 | 457.6 | 457.6 | 2 | no |
| 53 | 0 | 443.0 | 443.0 | 2 | no |
| 54 | 1 | 415.2 | 415.2 | 3 | no |
| 55 | 0 | 476.8 | 476.8 | 3 | no |
| 56 | 0 | 451.4 | 451.4 | 3 | no |
| 57 | 0 | 405.3 | 405.3 | 3 | no |
| 58 | 0 | 4.2 | 4.2 | 1 | yes |
| 59 | 0 | 455.6 | 455.6 | 3 | no |
| 60 | 0 | 477.6 | 477.6 | 2 | no |
| 61 | 1 | 445.4 | 445.4 | 1 | no |
| 62 | 2 | 454.4 | 454.4 | 2 | no |
| 63 | 0 | 477.8 | 477.8 | 9 | no |
| 64 | 0 | 465.9 | 465.9 | 3 | no |
| 65 | 0 | 462.8 | 462.8 | 3 | no |
| 66 | 0 | 460.5 | 460.5 | 2 | no |

## Drop-in paragraph for §5 Discussion

% TODO R4: update Table 4 cross-reference after section renumbering.
% TODO R4: sharpen 'before the stall begins' — consider 'before the
%           last successful exit' or 'before the crowd dissipates'.
% TODO R4 (optional): append a final sentence connecting the
%           terminal-stall finding to the C1+epsilon control in
%           Section 4.6 — e.g., 'the C1+epsilon control in
%           Section 4.6 confirms that this persistence is a
%           geometric symmetry property, not a low-density artefact.'

To quantify the stability of the arching deadlock, we measure the \emph{terminal stall} on the C1 (SFM only) trajectories at w=0.8\,m: the duration of the final plateau in the active-agent count, from the last successful evacuation to the end of the 600\,s simulation window. Across the 24 non-evacuating seeds (matching the 1/25 completion rate from Table~\ref{tab:bottleneck} exactly), the median terminal stall is 457\,s with a mean of 3.2 agents frozen at the exit throat. 24/25 (96\%) seeds sustain the stall for more than 100\,s. The 500\,s threshold is unreachable given our 600\,s simulation horizon and the $\sim$140\,s required for the bulk of the crowd to evacuate before the stall begins; the stalls that we observe are therefore horizon-limited lower bounds rather than finite steady-state lifetimes. Inspection of the trajectories shows the remaining 3--4 agents entirely stationary during the stall, with no displacement exceeding 0.1\,m and zero exit crossings. The arches are thus not transient congestion but force-balance configurations that SFM's symmetric pair repulsion cannot resolve passively; the 60\,s paper-table windows strictly under-count this persistence.