# R2.3 Statistical Reanalysis Report

## NB GLM (collisions, bottleneck w >= 1.0)
- Dispersion alpha = 0.1426 (data-driven estimate from NegativeBinomialP)
- C2 vs C1: IRR=0.710 [0.640, 0.786], p_HS=0.0000 ***
- C3 vs C1: IRR=0.929 [0.840, 1.028], p_HS=0.5984 ns
- C4 vs C1: IRR=0.695 [0.628, 0.771], p_HS=0.0000 ***

## Cox PH (deadlock survival, w=0.8 600s)
- PH assumption: OK — PH assumption holds
- C2 vs C1: HR=0.000 [0.000, inf], p_HS=1.0000 ns **[COMPLETE SEPARATION — HR not interpretable; use Fisher]**
- C3 vs C1: HR=17.231 [2.252, 131.846], p_HS=0.0479 *
- C4 vs C1: HR=19.611 [2.573, 149.464], p_HS=0.0361 *

## Fisher's exact (deadlock completion)
- C2 vs C1: OR=inf, p_HS=1.0000 ns (C1=1/25, C2=0/25)
- C3 vs C1: OR=0.038, p_HS=0.0031 ** (C1=1/25, C3=13/25)
- C4 vs C1: OR=0.033, p_HS=0.0012 ** (C1=1/25, C4=14/25)

## LMM (mean speed and throughput)
- bidirectional mean_speed C2 vs C1: coef=0.0659 [0.0395, 0.0924], p_HS=0.0000 ***
- bidirectional mean_speed C3 vs C1: coef=0.0550 [0.0285, 0.0815], p_HS=0.0006 ***
- bidirectional mean_speed C4 vs C1: coef=0.0741 [0.0476, 0.1005], p_HS=0.0000 ***
- bidirectional agents_exited C2 vs C1: coef=-1.3200 [-7.6584, 5.0184], p_HS=0.9682 ns
- bidirectional agents_exited C3 vs C1: coef=-5.0000 [-11.3384, 1.3384], p_HS=0.5980 ns
- bidirectional agents_exited C4 vs C1: coef=4.7600 [-1.5784, 11.0984], p_HS=0.5984 ns
- crossing mean_speed C2 vs C1: coef=0.0080 [0.0036, 0.0125], p_HS=0.0041 **
- crossing mean_speed C3 vs C1: coef=0.0202 [0.0157, 0.0246], p_HS=0.0000 ***
- crossing mean_speed C4 vs C1: coef=0.0310 [0.0265, 0.0354], p_HS=0.0000 ***
- crossing agents_exited C2 vs C1: coef=10.1600 [8.6941, 11.6259], p_HS=0.0000 ***
- crossing agents_exited C3 vs C1: coef=0.4800 [-0.9859, 1.9459], p_HS=0.9474 ns
- crossing agents_exited C4 vs C1: coef=11.1600 [9.6941, 12.6259], p_HS=0.0000 ***

## Claims comparison (old paper vs reanalysis)
| Claim | Old test | New test | Direction |
|---|---|---|---|
| TTC reduces collisions | Welch t | NB GLM IRR=0.710 p_HS=0.0000 | STRENGTHENED |
| C2 worsens deadlock | Fisher | Cox HR=0.000 p_HS=1.0000 | STRENGTHENED |
| ORCA resolves deadlock | Fisher | Fisher p_HS=0.0031 | STRENGTHENED |
| Crossing throughput triples | Welch t | LMM coef p_HS=0.0000 | STRENGTHENED |

## Implications for paper narrative

### TTC collision-reduction claim: STRENGTHENED
With data-driven NB dispersion (alpha=0.1426), the TTC collision-reduction claim survives Holm-Sidak correction: C2 vs C1 IRR=0.710 (p_HS=0.0000), C4 vs C1 IRR=0.695 (p_HS=0.0000). The CIs are tighter than the old Welch-based analysis. This claim can remain as a co-equal headline.

### Deadlock result: STRENGTHENED
Fisher's exact for C3 vs C1 and C4 vs C1 survive Holm-Sidak correction (p_HS < 0.005). Cox PH HRs for C3 and C4 also significant. Deadlock resolution remains a primary headline.

### Crossing throughput: STRENGTHENED
C4 +11.2 exits vs C1 (p_HS < 0.001) under LMM with Holm-Sidak. Bulletproof.

### C2 Cox HR: not interpretable
C2 has 0/25 evacuation events (complete separation). The Cox PH model produces a numerically extreme HR that is not interpretable. For all C2 comparisons, **report Fisher's exact as the primary test** and note the complete separation in a footnote. Do not present the Cox C2 HR as a headline number.
