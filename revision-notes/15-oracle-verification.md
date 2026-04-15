# S15 Oracle 1.4% verification

Source: results_analysis/oracle_baseline.md (8 scenario-metric pairs).

Counting C4-vs-oracle outcomes with metric direction:
- bottleneck_w1.0 evac: -2.4% (C4 faster) → improve
- bottleneck_w1.2 evac: -3.5% → improve
- bottleneck_w1.8 evac: +0.6% (C4 slower, within 1%) → match
- bottleneck_w2.4 evac: -0.9% → match (within 1%)
- bottleneck_w3.6 evac: +1.4% (C4 slower) → **underperform by 1.4%**
- bottleneck_deadlock completion: +7.7% (C4 higher) → improve
- bidirectional agents_exited: +6.9% → improve
- crossing agents_exited: +6.2% → improve

Summary: 5 improve, 2 match within 1%, **1 underperform by 1.4%**.

Arjun's "by 1.4%" fix is verified against data. Current paper says "by
less than 1%", which understates the gap. S15 cherry-picks: "1.4%" and
"paired Wilcoxon across seeds, n = 25 per scenario".

The drop-in paragraph in oracle_baseline.md says "underperforms in 2"
but that conflates the w1.8 +0.6% (within-1% match) with w3.6 +1.4%.
The current paper's 5/2/1 split is correct; only the "<1%" magnitude
needed fixing.
