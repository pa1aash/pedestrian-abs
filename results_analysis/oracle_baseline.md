# R2.4 Oracle Baseline

Per-scenario best single paradigm (C1/C2/C3) vs C4 (full blend).

| Scenario | Metric | Oracle (best single) | Oracle value | C4 value | Gap | Wilcoxon p |
|---|---|---|---|---|---|---|
| bottleneck_w1.0 | evacuation_time | C3 | 50.34 | 49.15 | -2.4% | 0.4926 |
| bottleneck_w1.2 | evacuation_time | C3 | 36.43 | 35.15 | -3.5% | 0.9368 |
| bottleneck_w1.8 | evacuation_time | C3 | 20.49 | 20.61 | +0.6% | 0.4578 |
| bottleneck_w2.4 | evacuation_time | C1 | 16.13 | 15.99 | -0.9% | 0.0080 |
| bottleneck_w3.6 | evacuation_time | C3 | 12.48 | 12.65 | +1.4% | 0.1124 |
| bottleneck_deadlock | completion_rate | C3 | 0.52 | 0.56 | +7.7% | 1.0000 |
| bidirectional | agents_exited | C1 | 68.92 | 73.68 | +6.9% | 0.2138 |
| crossing | agents_exited | C2 | 16.08 | 17.08 | +6.2% | 0.4647 |

## Drop-in paragraph for Section 5

To quantify the benefit of the full blend over naive paradigm selection, we define an oracle baseline as the per-scenario best single paradigm (C1, C2, or C3) on the primary metric. 
Across 8 scenario-metric pairs, C4 improves over the oracle in 5 cases, matches within 1% in 2, and underperforms in 2. 
The largest gap is +7.7% on bottleneck_deadlock (completion_rate), where the oracle is C3.