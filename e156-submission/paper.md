Mahmood Ahmad
Tahir Heart Institute
author@example.com

MAPriors: Browser-Based Meta-Analytic Predictive Priors and Dynamic Borrowing Engine

Can meta-analytic predictive priors and dynamic borrowing be made accessible through a browser-based tool without requiring R or Stan programming expertise? Eight historical Crohn disease placebo-arm studies totaling 960 patients from the Neuenschwander canonical dataset were analyzed alongside oncology and cardiovascular built-in examples. MAPriors, a single-file HTML application of 2,565 lines, implements Bayesian hierarchical modeling with robust mixture priors, power priors, and commensurate priors, along with effective sample size computation via the Morita method. The Crohn dataset produced a prevalence MAP prior mean of 17.7% (95% credible interval 11.2-25.8%) with an effective sample size of 959 patients under near-zero heterogeneity. Operating characteristics simulation confirmed nominal type I error near 5% and power gains of 10 to 15 percentage points over vague-prior designs. This is the first browser-based MAP prior engine, validated by 38 Selenium tests, democratizing regulatory-grade Bayesian borrowing. A limitation is that the implementation uses approximate Gibbs sampling rather than full Hamiltonian Monte Carlo inference.

Outside Notes

Type: methods
Primary estimand: Effective sample size
App: MAPriors v1.0
Data: Crohn disease placebo (Neuenschwander 2010), oncology, cardiovascular (built-in)
Code: https://github.com/mahmood726-cyber/MAPriors
Version: 1.0
Validation: DRAFT

References

1. Roever C. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2020;93(6):1-51.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.

AI Disclosure

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI (Claude, Anthropic) was used as a constrained synthesis engine operating on structured inputs and predefined rules for infrastructure generation, not as an autonomous author. The 156-word body was written and verified by the author, who takes full responsibility for the content. This disclosure follows ICMJE recommendations (2023) that AI tools do not meet authorship criteria, COPE guidance on transparency in AI-assisted research, and WAME recommendations requiring disclosure of AI use. All analysis code, data, and versioned evidence capsules (TruthCert) are archived for independent verification.
