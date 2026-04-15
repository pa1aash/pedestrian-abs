
## For Session 15 (Discussion + "does not claim")

The sigmoid-gate-is-decorative admission now exists in three places:
§3.1 (ρ₀ literature-motivated), §4.4 (density range below transition),
§5 Limitations (no sweep, acts as fixed blend). Session 10 will add a
fourth (gate-occupancy percentages).

Session 15's "What this paper does not claim" paragraph should
consolidate these into ONE bullet pointing to the evidence locations,
not restate the same caveat four separate times.

Added: 2026-04-14, Session 5.

## For Session 16 (Conclusion rewrite)

Session 13 grep found a residual "validates" in §6 Conclusion at line 453.
Out of scope for §4.7-only Session 13. Session 16 must scrub it as part
of the broader §6 rewrite per Option B framing.

Added: 2026-04-14, Session 13.

## For Session 16 (Conclusion rewrite) — Option B residuals

Session 12 rewrote §4.6 and §5 per Option B but did not touch §6.
The current §6 (line ~452) still says "resolves arching deadlocks in
56% of trials versus 4% for SFM alone" and "0/25 versus 1/25 for
plain SFM". Both are Option-B stale: C1 is 0/25 at n=25 (not 1/25),
and the contrast should be "neither plain SFM nor SFM+TTC evacuates
any of 25 trials while ORCA-enabled configurations evacuate 52–56%".
§6 also still mentions "digital twin pipelines for real-time venue
monitoring" which S14 deliberately removed from §4.8 and should live
only in §6 Future Work — S16 decides whether to retain there or
drop entirely.

Added: 2026-04-15, Session 12.

## For Session 15 (Discussion + admissions)

Gate-occupancy admission (S10) added to §4.4 as a fourth evidence
location alongside the three S5 flagged. S15 should still consolidate
into one "does not claim" bullet; now pointing at §3.1, §4.4 (density
range), §4.4 (gate occupancy) and §5 Limitations (fixed-blend).
Crossing and bidirectional gate-occupancy are a documented data gap
(density-per-agent-timestep logs were not archived); S15 may want to
frame this as "our sigmoid analysis is limited to the bottleneck
scenario because that is the only scenario with archived density
logs".

Added: 2026-04-15, Session 10.

## For Session 19 (final peer-review pass)

S11 skipped the optional 120 s crossing stability rerun due to compute
budget (estimated ~13 hours for a full 3-seed × 4-config stability
check at 120 s each, based on S14's cProfile extrapolation). If S19
wall-clock budget has slack, run C1 and C4 only at 120 s × 3 seeds
(~8 min each = ~48 min total) and add a robustness sentence to
§4.5. Skip otherwise.

S11 also used a ratio-of-means IRR derivation for crossing throughput
rather than a full NB GLM refit, because per-seed count vectors were
not archived. S19 should grep the final PDF for "ratio-of-means"
to verify the footnote survives into the submitted version.

Added: 2026-04-15, Session 11.
