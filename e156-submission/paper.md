Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

MAPriors: Browser-Based Meta-Analytic Predictive Priors and Dynamic Borrowing Engine

Can meta-analytic predictive priors and dynamic borrowing be made accessible through a browser-based tool without requiring R or Stan expertise? Eight historical Crohn disease placebo-arm studies totaling 960 patients from the Neuenschwander canonical dataset were analyzed alongside oncology ORR and ulcerative colitis CDAI built-in examples. MAPriors, a single-file HTML application of 3,925 lines, implements Bayesian hierarchical modeling with robust mixture priors, power priors, commensurate priors, prior evolution animation, and operating characteristics simulation, with TruthCert SHA-256 audit provenance. The Crohn dataset produced a MAP prior mean of 17.7% (95% credible interval 11.2-25.8%) with Morita effective sample size of 959 patients under near-zero heterogeneity. Operating characteristics confirmed nominal type I error near 5% and power gains of 10-15 percentage points over vague-prior designs, with sample size savings of 20-35% in the control arm. This is the first browser-based MAP prior engine, validated by 40 Selenium tests with WebR cross-validation and regulatory reporting. A limitation is the approximate REML inference rather than full Hamiltonian Monte Carlo.

Outside Notes

Type: methods
Primary estimand: Effective sample size
App: MAPriors v2.0
Data: Crohn disease placebo (Neuenschwander 2010), UC CDAI, oncology ORR (built-in)
Code: https://github.com/mahmood726-cyber/MAPriors
Version: 2.0
Validation: PASS (40/40 tests, WebR, 3-round review clean)

References

1. Neuenschwander B, Capkun-Niggli G, Branson M, Spiegelhalter DJ. Summarizing historical information on controls in clinical trials. Clin Trials. 2010;7(1):5-18.
2. Morita S, Thall PF, Muller P. Determining the effective sample size of a parametric prior. Biometrics. 2008;64(2):595-602.
3. Schmidli H, Gsteiger S, Roychoudhury S, et al. Robust meta-analytic-predictive priors in clinical trials with historical control information. Biometrics. 2014;70(4):1023-1032.
