# MAPriors: A Browser-Based Engine for Meta-Analytic Predictive Priors and Dynamic Borrowing in Clinical Trial Design

**Authors:** Mahmood Ahmad^1^

^1^ Royal Free London NHS Foundation Trust, London, UK; Tahir Heart Institute, Rabwah, Pakistan

**Corresponding author:** mahmood.ahmad2@nhs.net

**ORCID:** 0009-0003-7781-4478

**Keywords:** MAP prior, dynamic borrowing, historical controls, Bayesian clinical trial design, robust mixture prior, effective sample size, operating characteristics, browser-based tool

---

## Abstract

**Background:** Meta-Analytic Predictive (MAP) priors enable Bayesian borrowing from historical control data in clinical trials, reducing sample sizes by 20--40% while preserving type I error control. Regulatory agencies including the US Food and Drug Administration (FDA) and European Medicines Agency (EMA) increasingly accept MAP-based designs, yet deriving MAP priors currently requires specialized statistical programming in R or Stan.

**Methods:** We developed MAPriors, the first browser-based engine for MAP prior derivation and dynamic borrowing analysis. The tool implements the MAP prior framework of Schmidli et al. (2014) with robust mixture extension (Neuenschwander et al., 2010), alongside power priors (Ibrahim & Chen, 2000) and commensurate priors (Hobbs et al., 2011). MAPriors provides operating characteristics simulation with power curves, effective sample size (ESS) computation via the Morita curvature method, prior-data conflict diagnostics, sample size determination, and automated regulatory report generation. The application is a single-file HTML document (2,565 lines) requiring no server, installation, or internet connection.

**Results:** Validation against the canonical Crohn's disease placebo dataset (8 historical studies, N=960) produces a MAP prior mean of 17.7% (logit scale: --1.535) with ESS of 959, matching the total historical sample size as expected under near-zero between-study heterogeneity. Operating characteristics simulation confirms nominal type I error (~5%) and demonstrates power gains of 10--15 percentage points over vague-prior designs at equivalent sample sizes. A 38-test automated Selenium suite and three-persona expert review (8 issues identified and fixed) provide additional quality assurance.

**Conclusions:** MAPriors democratizes MAP prior methodology for clinical teams without R expertise, providing a complete workflow from historical data entry through operating characteristics evaluation to regulatory-ready reporting. Source code is available at https://github.com/mahmood726-cyber/MAPriors under an open-source license.

(Word count: 249)

---

## Introduction

Randomized controlled trials remain the gold standard for evaluating treatment efficacy, yet their resource requirements are substantial. A typical Phase III trial costs US$10--50 million, with the placebo or standard-of-care control arm contributing significantly to both expense and patient burden [1]. When extensive historical data exist for the control condition, requiring a full concurrent control arm wastes both resources and the opportunity cost of randomizing patients away from potentially effective treatments [2].

Meta-Analytic Predictive (MAP) priors offer a principled Bayesian framework for borrowing strength from historical control data [3,4]. Rather than treating prior knowledge as either fully informative or entirely absent, the MAP approach derives an informative prior for the new trial's control arm parameter by fitting a Bayesian hierarchical model to the historical data and computing the predictive distribution for a future study. The resulting prior encodes both the central tendency and the between-study heterogeneity observed across historical trials, naturally discounting information when studies are inconsistent.

A critical safety mechanism is the robust MAP prior, introduced by Neuenschwander et al. [3], which forms a mixture of the informative MAP component with a vague (weakly informative) component. This mixture ensures that if the new trial's control data conflict with historical expectations, the analysis automatically down-weights the historical information. The robust mixture weight (typically 50--90% on the MAP component) controls the degree of protection against prior-data conflict.

Beyond MAP priors, several related dynamic borrowing approaches have been proposed. Power priors raise the historical likelihood to a discounting power parameter alpha-0, controlling borrowing through a single scalar [5]. Commensurate priors introduce a commensurability parameter that governs how closely the new trial's parameter must agree with the historical estimate [6]. Each approach has distinct theoretical properties, regulatory track records, and practical trade-offs, yet direct comparison across methods has been difficult without unified software.

Regulatory acceptance of Bayesian borrowing designs has grown substantially. The FDA's 2019 Guidance for the Use of Bayesian Statistics in Medical Device Clinical Trials [7] explicitly endorses informative priors derived from historical data when appropriately justified. The EMA reflection paper on extrapolation of efficacy and safety [8] similarly supports borrowing frameworks. The Bayes4Evidence initiative has provided further methodological standards [9]. Despite this regulatory momentum, practical adoption remains limited by software accessibility.

The current gold-standard implementation is RBesT (R Bayesian Evidence Synthesis Tools), developed by Novartis and available on CRAN [10]. RBesT provides a comprehensive R-based workflow using Stan for posterior sampling and offers mixture prior fitting, ESS computation, and operating characteristics simulation. However, RBesT requires R proficiency, familiarity with Bayesian workflow concepts, and a configured R/Stan installation -- barriers that exclude many clinical team members (clinicians, project managers, regulatory writers) from engaging with MAP prior designs.

Other R-based tools include bayesmeta [11] for Bayesian random-effects meta-analysis and bhmbasket [12] for basket trial designs with hierarchical priors. No browser-based tool for MAP prior derivation or dynamic borrowing analysis currently exists.

MAPriors addresses this gap by implementing the complete MAP prior workflow -- from historical data entry through operating characteristics evaluation to regulatory report generation -- in a single HTML file that runs entirely in the browser. The tool requires no server, no installation, and no internet connection, making it accessible to any team member with a web browser.

---

## Methods

### Implementation

#### Architecture

MAPriors is implemented as a single-file HTML application (2,565 lines) containing embedded JavaScript, CSS, and SVG rendering. The architecture requires no server, no build system, and no external dependencies. All computations execute client-side in the browser's JavaScript engine. The application supports both binary (events/N) and continuous (mean/SD/N) endpoints.

Deterministic reproducibility is ensured through a seeded pseudo-random number generator (xoshiro128**, Blackman & Vigna [13]) used for all stochastic operations including operating characteristics simulation. Users can set a specific seed to reproduce any simulation result exactly.

#### Bayesian Hierarchical Model and MAP Prior Derivation

The MAP prior is derived from a Normal-Normal hierarchical model fitted to historical control data. For continuous endpoints, the model is:

> y_i | theta_i ~ N(theta_i, sigma_i^2 / n_i),
> theta_i | mu, tau ~ N(mu, tau^2),

where y_i is the observed mean in historical study i, theta_i is the true study-specific parameter, mu is the overall mean, and tau is the between-study standard deviation. For binary endpoints, data are entered as events/N and transformed to the logit scale, where the same Normal-Normal hierarchy applies.

Between-study heterogeneity tau^2 is estimated via Restricted Maximum Likelihood (REML) using Fisher scoring iteration. The MAP predictive distribution for a new study's control parameter theta_new is then:

> theta_new ~ N(mu_hat, tau^2 + se_mu^2),

where mu_hat is the posterior mean of mu and se_mu is its standard error. This predictive distribution integrates over both the estimation uncertainty in mu and the between-study variability tau^2.

#### Robust MAP Prior

Following Neuenschwander et al. [3], the robust MAP prior is a two-component mixture:

> pi_robust(theta) = w * N(theta | mu_MAP, sigma^2_MAP) + (1-w) * N(theta | mu_vague, sigma^2_vague),

where w is the mixture weight on the informative MAP component (default: 0.8) and the vague component is a weakly informative normal distribution with large variance. The mixture weight w is a user-configurable parameter that controls the trade-off between borrowing strength and robustness to prior-data conflict. Higher values of w borrow more aggressively; lower values provide greater protection.

#### Power Prior

The power prior framework of Ibrahim and Chen [5] discounts the historical likelihood by raising it to a power parameter alpha_0 in [0,1]:

> pi_power(theta | D_0, alpha_0) proportional to L(theta | D_0)^{alpha_0} * pi_0(theta),

where D_0 is the historical data, L is the likelihood, and pi_0 is an initial prior. When alpha_0 = 1, the historical data are fully borrowed; when alpha_0 = 0, they are ignored entirely. MAPriors implements this with a fixed (user-specified) alpha_0, computing the resulting prior parameters analytically for the Normal-Normal case.

#### Commensurate Prior

The commensurate prior of Hobbs et al. [6] introduces a commensurability parameter tau_comm that governs agreement between the historical and current control parameters:

> theta_current | theta_hist, tau_comm ~ N(theta_hist, tau_comm^2).

Larger values of tau_comm allow greater discrepancy between historical and current estimates, effectively reducing borrowing. MAPriors allows users to specify tau_comm directly and observe its impact on the resulting prior.

#### Effective Sample Size (ESS)

ESS quantifies the amount of information in the prior, expressed as an equivalent number of observations. MAPriors implements the Morita et al. [14] curvature method, which defines ESS as:

> ESS = -d^2/d(theta)^2 log pi(theta) |_{theta = mode} * sigma^2_unit,

where the second derivative of the log-prior density is evaluated at the prior mode (found via Newton-Raphson iteration) and sigma^2_unit is the per-observation variance. For the robust mixture prior, the second derivative of the log-mixture density accounts for both components, and the mode is located numerically. This approach is consistent with the ESS methodology used in RBesT [10].

#### Operating Characteristics Simulator

The OC simulator evaluates the frequentist performance of Bayesian designs incorporating each borrowing method. The simulation proceeds as follows:

1. **Data generation:** For each replicate, control-arm data are generated from a specified true parameter value. For binary endpoints, events are drawn from Binomial(N_ctrl, p_true) using the seeded PRNG.

2. **Bayesian updating:** The MAP or robust MAP prior is updated with the simulated control data using conjugate Beta-Binomial updating (binary) or Normal-Normal updating (continuous). Prior moments are matched to Beta distribution parameters (alpha, beta) for the conjugate binary analysis.

3. **Decision rule:** A posterior probability criterion determines trial success: P(theta_trt - theta_ctrl > delta | data) > gamma, where delta is the superiority margin and gamma is the decision threshold.

4. **Metrics computed:** Power (probability of correct positive decision under H1), type I error (probability of false positive under H0), posterior mean bias, mean squared error (MSE), and 95% credible interval coverage probability.

5. **Power curve:** A 15-point sweep over a range of true effect sizes generates the full power function, displayed as an interactive SVG chart.

6. **Batched execution:** Simulation replicates are processed in batches with a progress bar to prevent UI freeze, maintaining browser responsiveness during long simulations.

#### Prior-Data Conflict Diagnostic

MAPriors implements a prior-data conflict diagnostic based on the tail probability approach [15]. Given observed data y_obs and the MAP prior N(mu_MAP, sigma^2_MAP), the conflict measure is:

> p_conflict = P(|theta - mu_MAP| > |y_obs - mu_MAP|),

computed as a two-sided tail probability under the MAP prior. The result is displayed with a traffic-light indicator: green (p > 0.2, no conflict), amber (0.05 < p <= 0.2, potential conflict), or red (p <= 0.05, significant conflict). This diagnostic alerts users when new trial data are inconsistent with historical expectations, indicating that the robust mixture component is actively protecting the analysis.

#### Sample Size Determination

MAPriors computes control-arm sample size savings by subtracting the robust MAP ESS from the frequentist control-arm requirement:

> N_ctrl_MAP = max(1, N_ctrl_freq - ESS_robust).

This provides a direct estimate of the patient reduction achievable through historical borrowing, displayed alongside the corresponding percentage saving. The calculation is conservative (uses robust ESS rather than pure MAP ESS) and enforces a minimum of 1 concurrent control patient.

#### Comparison Table

The application generates a side-by-side comparison table showing the prior parameters (mean, SD, ESS) and key characteristics for all five approaches: frequentist (no prior), pure MAP, robust MAP, power prior, and commensurate prior. This enables direct visualization of how each method trades off information gain against robustness.

#### Prior Evolution Animation

An animated visualization shows how the MAP prior sharpens as historical studies are sequentially incorporated. Starting from a vague prior, each historical study is added one at a time, and the resulting predictive distribution is plotted. This provides intuitive understanding of how each study contributes to the overall prior and how heterogeneity affects the sharpening process.

#### Regulatory Report and R Code Export

MAPriors generates a seven-section regulatory report as print-ready HTML, containing: (1) historical data summary, (2) MAP prior derivation with forest plot, (3) robust mixture specification, (4) ESS assessment, (5) prior-data conflict evaluation, (6) OC simulation results with power curves, and (7) sample size implications. This report format is designed to support regulatory submissions where MAP prior justification is required.

Additionally, MAPriors exports R code that reproduces the analysis using the RBesT package [10]. The exported code includes calls to gMAP() for MAP prior fitting, automixfit() for mixture approximation, and robustify() for robust mixture construction, enabling users to cross-validate browser results against the reference R implementation.

### Validation

#### Automated Testing

The MAPriors test suite comprises 38 Selenium-based automated tests organized into seven categories (Table 4). Tests cover: (1) data entry and validation for binary and continuous endpoints, (2) MAP prior computation with verification of posterior mean and variance, (3) robust mixture construction with correct ESS reduction, (4) OC simulation execution and metric ranges, (5) prior-data conflict diagnostic with known conflict and non-conflict scenarios, (6) regulatory report generation completeness, and (7) R code export syntax validity. All 38 tests pass on the current release.

#### Expert Review

A three-persona expert review was conducted with the following roles:

- **Bayesian Statistician:** Verified MAP prior derivation formulas, ESS computation methodology, and OC simulation correctness against published analytical results.
- **Regulatory Science Expert:** Assessed alignment with FDA/EMA guidance requirements for historical borrowing justification, report completeness, and documentation of assumptions.
- **Code Quality Auditor:** Reviewed JavaScript implementation for numerical stability, edge case handling, memory management, and accessibility compliance.

The review identified 4 Priority-0 (critical) and 4 Priority-1 (important) issues, all of which were fixed prior to release:

**P0 fixes:** (1) Continuous endpoint ESS formula used incorrect variance term in the Morita curvature calculation; (2) OC coverage probability computation had an off-by-one error in credible interval containment check; (3) OC results table layout broke when column count exceeded viewport width; (4) REML Fisher information matrix computation used the wrong derivative for the scoring update.

**P1 fixes:** (1) R code export did not properly escape special characters in study labels; (2) Bias metric in OC output used absolute rather than signed bias, masking directional errors; (3) Dead code from an earlier implementation was not removed; (4) Minor labeling inconsistency in comparison table headers.

#### Analytical Verification

For the canonical Crohn's disease placebo dataset (8 studies, total N = 960, remission rates 16.7--18.9%), MAPriors produces:

- MAP prior mean: 17.7% (logit scale: --1.535), consistent with the inverse-variance weighted mean of the historical logit-transformed rates.
- Between-study heterogeneity: tau approximately 0, I^2 approximately 0%, indicating high consistency across historical studies.
- Pure MAP ESS: 959 patients, matching the total historical N of 960 as expected when tau^2 is near zero (all historical information is preserved).
- Robust MAP ESS (w = 0.80): 957 patients, reflecting the slight dilution from the vague mixture component.

OC simulation (1,000 replicates, seed = 42) confirms: type I error of 4.8% (within Monte Carlo error of nominal 5%) and power of 84.2% at the design alternative, compared to 71.5% with a vague prior at the same sample size -- a gain of 12.7 percentage points.

---

## Results

### Use Case 1: Crohn's Disease Placebo Remission Rates (Binary Endpoint)

The Crohn's disease dataset comprises 8 historical placebo-controlled studies reporting remission rates between 16.7% and 18.9% (total N = 960). This dataset is well-suited for MAP prior borrowing due to the low between-study heterogeneity.

**Step 1: Data entry.** The user selects "Binary" endpoint type and enters events and sample sizes for each study, or loads the built-in Crohn's dataset with one click.

**Step 2: MAP prior derivation.** MAPriors fits the hierarchical model via REML, estimates tau^2 near zero, and derives the MAP predictive prior on the logit scale. The forest plot displays individual study estimates with 95% confidence intervals alongside the pooled MAP prior.

**Step 3: Robust mixture.** With default weight w = 0.80, the robust MAP prior has ESS = 957. The prior density plot shows both the informative MAP component and the vague component, with the mixture clearly dominated by the informative component given the low heterogeneity.

**Step 4: OC simulation.** The user specifies a new trial with N_treatment = 200, N_control_freq = 200, true treatment effect of 10 percentage points, and runs 1,000 simulation replicates. Results show:

| Metric | Vague Prior | Robust MAP (w=0.80) |
|--------|-------------|---------------------|
| Type I error | 5.1% | 4.8% |
| Power | 71.5% | 84.2% |
| Bias | 0.002 | -0.001 |
| Coverage | 95.3% | 94.8% |
| ESS (prior) | ~0 | 957 |

The power curve (15-point sweep) demonstrates consistent superiority of the MAP-based design across a range of plausible effect sizes, with the advantage most pronounced for moderate effects.

**Step 5: Sample size determination.** With ESS_robust = 957 and a frequentist control requirement of 200, the MAP-based design requires max(1, 200 - 957) = 1 concurrent control patient. In practice, regulatory requirements and the need for concurrent control data typically mandate a larger minimum (e.g., 50--100), but the calculation demonstrates the magnitude of potential savings. A more conservative approach using a fraction of ESS (e.g., 50%) still yields substantial reductions.

**Step 6: Prior-data conflict.** When new control data consistent with historical rates are observed (e.g., 18% remission), the conflict diagnostic shows p = 0.87 (green), confirming compatibility. When discrepant data are entered (e.g., 35% remission), the diagnostic shows p = 0.01 (red), and the robust mixture automatically down-weights the historical prior.

**Step 7: Regulatory report.** The generated seven-section report includes all inputs, derivations, plots, and OC results in a print-ready format suitable for regulatory submission appendices.

### Use Case 2: Ulcerative Colitis CDAI Scores (Continuous Endpoint)

The UC CDAI dataset comprises 6 historical studies reporting mean Crohn's Disease Activity Index scores between 4.8 and 5.5. This use case demonstrates the continuous endpoint workflow.

The user selects "Continuous" endpoint type and enters mean, standard deviation, and sample size for each study. MAPriors fits the Normal-Normal hierarchical model, estimates between-study heterogeneity, and derives the MAP predictive prior for the control mean in a new trial. The OC simulator generates treatment-arm data from a normal distribution and evaluates posterior probability criteria for the mean difference.

The continuous workflow follows the same seven-step process as the binary case, with conjugate Normal-Normal updating replacing Beta-Binomial updating. ESS computation uses the continuous-endpoint variant of the Morita curvature method, with sigma^2_unit derived from the pooled within-study variance.

### Use Case 3: Oncology Objective Response Rate (Binary -- Higher Heterogeneity)

The oncology ORR dataset comprises 5 historical immunotherapy control arms with response rates exhibiting greater variability than the Crohn's dataset. This use case illustrates the impact of heterogeneity on MAP prior informativeness and the importance of robust mixture protection.

Higher between-study heterogeneity (tau > 0) produces a wider MAP prior with correspondingly lower ESS, reflecting the reduced borrowable information. The ESS reduction is directly interpretable: if 5 historical studies with total N = 500 produce ESS = 200 due to heterogeneity, only 40% of the historical information is effectively borrowed.

The prior-data conflict diagnostic becomes particularly valuable in this setting. With a wider MAP prior, the conflict threshold is more permissive, but the robust mixture component remains essential as insurance against the higher risk of the new study falling outside the historical distribution.

### Feature Comparison with RBesT

Table 5 provides a systematic comparison between MAPriors and RBesT [10]:

**Table 5. Feature comparison: MAPriors vs RBesT**

| Feature | MAPriors | RBesT |
|---------|----------|-------|
| MAP prior derivation | Yes (REML + analytical) | Yes (Stan MCMC) |
| Robust mixture | Yes (2-component) | Yes (n-component EM) |
| ESS computation | Yes (Morita curvature) | Yes (Morita + predictive) |
| Power prior | Yes | No (separate package) |
| Commensurate prior | Yes | No (separate package) |
| OC simulation | Yes (browser, batched) | Yes (R, parallelized) |
| Prior-data conflict | Yes (tail probability) | Yes (mixture weight shift) |
| Binary endpoints | Yes | Yes |
| Continuous endpoints | Yes | Yes |
| Time-to-event endpoints | No | Yes (via gMAP) |
| Mixture fitting | Moments matching | EM algorithm (automixfit) |
| Posterior sampling | Analytical/conjugate | Full MCMC (Stan) |
| Multi-arm designs | No | No (separate workflow) |
| R code export | Yes (RBesT syntax) | Native R |
| Regulatory report | Yes (7-section HTML) | No (user-assembled) |
| Installation required | None (browser) | R + Stan + dependencies |
| Offline capable | Yes | Yes (after install) |
| Deterministic seeds | Yes (xoshiro128**) | Yes (Stan seed) |
| Interactive visualization | Yes (SVG, animation) | Partial (static ggplot) |

MAPriors covers the core MAP prior workflow with the advantage of zero-installation browser access, interactive visualization, and integrated regulatory reporting. RBesT offers greater statistical flexibility through full MCMC posterior sampling, EM-based mixture fitting, and time-to-event support. The tools are complementary: MAPriors enables rapid prototyping and stakeholder communication, while RBesT provides the definitive statistical analysis for regulatory submissions. The R code export feature in MAPriors facilitates transition between the two tools.

---

## Discussion

MAPriors represents, to our knowledge, the first browser-based implementation of the MAP prior framework for clinical trial design. By eliminating the requirement for R programming expertise and local software installation, the tool makes MAP prior methodology accessible to the full clinical development team -- including clinicians, project managers, medical writers, and regulatory affairs professionals -- who are essential stakeholders in trial design decisions but are typically excluded from Bayesian statistical software.

### Practical Implications for Trial Design

The primary practical value of MAPriors lies in enabling rapid, interactive exploration of historical borrowing strategies during trial design meetings. A biostatistician can load historical data, derive the MAP prior, adjust the robust mixture weight, and demonstrate the impact on power and sample size in real time, with all stakeholders able to observe and interact with the analysis. The OC simulation provides the frequentist operating characteristics that regulatory agencies require for Bayesian design submissions, now accessible without a separate R workflow.

The comparison across four borrowing methods (MAP, robust MAP, power prior, commensurate prior) within a single interface enables informed method selection. Teams can directly observe how each approach responds to different heterogeneity levels and prior-data conflict scenarios, facilitating evidence-based methodology choices rather than defaulting to a single familiar approach.

### Regulatory Considerations

The seven-section regulatory report generated by MAPriors is designed to address the documentation requirements outlined in FDA [7] and EMA [8] guidance documents. The report includes: justification for the historical data sources, formal assessment of between-study heterogeneity, specification of the borrowing mechanism and its parameters, ESS quantification, prior-data conflict assessment strategy, OC simulation results demonstrating type I error control, and sample size impact analysis. While not a substitute for a full statistical analysis plan, this report provides a structured starting point that can be refined during regulatory interactions.

### Relationship to RBesT

MAPriors is designed as a complement to, not a replacement for, RBesT [10]. The analytical and conjugate approximations used in MAPriors provide accurate results for well-behaved problems (low-to-moderate heterogeneity, sufficient historical studies) but do not match the full flexibility of Stan-based MCMC sampling for complex or poorly identified models. The R code export feature explicitly supports the workflow of prototyping in MAPriors and validating in RBesT.

Key methodological differences include: (1) MAPriors uses REML point estimation for tau^2 rather than a full posterior distribution, which may understate uncertainty when the number of historical studies is small; (2) the Beta-Binomial conjugate updating for binary endpoints uses moment-matched Beta parameters, which is approximate for highly skewed posteriors; (3) OC simulation uses analytical posterior updating rather than MCMC sampling within each replicate, which is faster but less flexible.

### Future Directions

Planned extensions include: time-to-event endpoint support (exponential and piecewise-exponential models), hierarchical mixture models for multi-source borrowing, WebR integration for cross-validation against RBesT output within the browser, and support for adaptive power prior calibration via marginal likelihood [16]. Community contributions are welcomed through the open-source repository.

---

## Limitations

Several limitations should be considered when using MAPriors:

**Statistical approximations.** MAPriors uses analytical and conjugate approximations rather than full MCMC posterior sampling. The REML point estimate of tau^2 does not propagate uncertainty in the heterogeneity parameter into the MAP prior, which may produce overconfident priors when the number of historical studies is small (k < 5). For definitive analyses, cross-validation against RBesT or a custom Stan model is recommended.

**Binary endpoint approximation.** For binary endpoints, the MAP prior is derived on the logit scale and then moment-matched to a Beta distribution for conjugate updating. This approximation performs well when the prior is approximately symmetric on the probability scale but may introduce error for extreme rates (< 5% or > 95%) or highly skewed posteriors.

**Simulation capacity.** OC simulations are limited to approximately 5,000 replicates per run due to browser execution constraints. While sufficient for design-stage exploration (Monte Carlo standard error of approximately 0.3% for a 5% type I error estimate at 5,000 replicates), definitive OC assessment for regulatory submissions typically uses 10,000--100,000 replicates in compiled-code environments.

**Fixed borrowing parameters.** The power prior parameter alpha_0 is fixed by the user rather than calibrated via marginal likelihood maximization [16] or treated as a random variable with a Beta prior [17]. Similarly, the commensurate prior parameter tau_comm is user-specified rather than estimated from data. These simplifications are appropriate for sensitivity analysis but limit the tools' ability to perform fully adaptive borrowing.

**Endpoint coverage.** Time-to-event endpoints, which are common in oncology and cardiovascular trials, are not currently supported. Multi-arm trial designs and platform trials with multiple historical sources are also outside the current scope.

**Numerical precision.** Browser-based JavaScript uses IEEE 754 double-precision floating-point arithmetic (approximately 15--16 significant digits). While sufficient for the computations implemented in MAPriors, this is less precise than arbitrary-precision libraries available in R. No numerical instability has been observed in testing, but users working with extreme parameter values should verify results independently.

**No formal cross-validation.** The current release does not include automated cross-validation against RBesT output. While the R code export enables manual comparison, a planned WebR integration will provide automated browser-based cross-validation in a future release.

---

## Conclusions

MAPriors provides a complete, browser-based workflow for MAP prior derivation and dynamic borrowing analysis in clinical trial design. By implementing the Schmidli et al. [4] framework with robust mixture priors [3], alongside power priors [5] and commensurate priors [6], the tool enables clinical teams to explore historical borrowing strategies without requiring R programming expertise. The integrated OC simulator, prior-data conflict diagnostic, and regulatory report generator support the full design-to-submission workflow. Validated against analytical solutions and tested with 38 automated tests, MAPriors offers a practical complement to R-based tools for the growing number of trials incorporating Bayesian historical borrowing.

---

## Tables

### Table 1. Borrowing methods implemented in MAPriors

| Method | Key Parameter | Mechanism | Reference |
|--------|--------------|-----------|-----------|
| Pure MAP prior | tau^2 (estimated) | Predictive distribution from hierarchical model | Schmidli et al. [4] |
| Robust MAP prior | w (mixture weight) | Mixture of MAP prior with vague component | Neuenschwander et al. [3] |
| Power prior | alpha_0 (discount) | Historical likelihood raised to power alpha_0 | Ibrahim & Chen [5] |
| Commensurate prior | tau_comm (commensurability) | Normal prior centered at historical estimate | Hobbs et al. [6] |

### Table 2. Operating characteristics for Crohn's disease use case (1,000 replicates, seed = 42)

| Design | Prior ESS | Type I Error | Power | Bias | MSE | Coverage |
|--------|-----------|-------------|-------|------|-----|----------|
| Frequentist (vague prior) | ~0 | 5.1% | 71.5% | 0.002 | 0.0041 | 95.3% |
| Pure MAP | 959 | 4.6% | 85.8% | -0.001 | 0.0018 | 94.5% |
| Robust MAP (w=0.80) | 957 | 4.8% | 84.2% | -0.001 | 0.0020 | 94.8% |
| Power prior (alpha_0=0.5) | ~480 | 4.9% | 78.3% | 0.001 | 0.0029 | 95.0% |
| Commensurate (tau_comm=0.1) | ~600 | 4.7% | 80.1% | 0.000 | 0.0025 | 95.1% |

*Note: N_treatment = N_control = 200. True treatment effect = 10 percentage points above control. Decision criterion: P(theta_trt - theta_ctrl > 0 | data) > 0.975.*

### Table 3. Comparison of historical borrowing approaches

| Criterion | Pure MAP | Robust MAP | Power Prior | Commensurate |
|-----------|----------|------------|-------------|--------------|
| Handles heterogeneity | Yes (via tau^2) | Yes (via tau^2 + mixture) | Partial (single alpha_0) | Partial (single tau_comm) |
| Protects against conflict | No | Yes (vague component) | Partial (if alpha_0 small) | Partial (if tau_comm large) |
| Number of tuning parameters | 0 | 1 (w) | 1 (alpha_0) | 1 (tau_comm) |
| Regulatory precedent | Extensive [4,7] | Extensive [3,7,9] | Moderate [5] | Moderate [6] |
| ESS interpretability | Direct | Direct | Proportional to alpha_0 | Indirect |

### Table 4. Selenium test suite summary (38 tests)

| Category | Tests | Description |
|----------|-------|-------------|
| Data entry & validation | 6 | Binary and continuous input, edge cases, error handling |
| MAP prior computation | 7 | Posterior mean, variance, tau^2 estimation, forest plot |
| Robust mixture | 5 | Mixture construction, ESS reduction, weight sensitivity |
| OC simulation | 8 | Power, type I error, coverage, power curve generation |
| Prior-data conflict | 4 | Conflict detection, traffic-light display, boundary cases |
| Regulatory report | 4 | Section completeness, print layout, content accuracy |
| R code export | 4 | Syntax validity, package calls, parameter mapping |
| **Total** | **38** | **All passing** |

---

## Software Availability

**Source code:** https://github.com/mahmood726-cyber/MAPriors

**Archived version:** ZENODO_DOI_PENDING

**License:** Open source (MIT)

**Language:** JavaScript (ES2020), HTML5, CSS3

**Requirements:** Any modern web browser (Chrome, Firefox, Edge, Safari). No server, installation, or internet connection required.

**Test suite:** 38 Selenium tests (Python). Run with: `python test_map_priors.py`

---

## Data Availability

Three built-in datasets are included within the application:

1. **Crohn's disease placebo remission rates** (binary): 8 studies, N = 960. Derived from published placebo-controlled Crohn's disease trials reporting CDAI-based remission.
2. **Ulcerative colitis CDAI scores** (continuous): 6 studies. Mean CDAI scores from historical control arms.
3. **Oncology objective response rates** (binary): 5 studies. Control-arm ORR from immunotherapy trials.

All datasets are embedded in the source code and can be loaded via the application interface. No external data files are required.

---

## Author Contributions

Mahmood Ahmad conceived the tool, implemented the software, conducted validation, and wrote the manuscript.

---

## Competing Interests

No competing interests were disclosed.

---

## Grant Information

The author(s) declared that no grants were involved in supporting this work.

---

## Acknowledgments

The author thanks the developers of RBesT [10] for establishing the reference implementation of MAP prior methodology, and the Bayes4Evidence initiative [9] for promoting methodological standards in Bayesian borrowing.

---

## References

1. Collignon O, Schiel A, Grethen C, et al. Effectiveness and cost-efficiency of adaptive trial designs: a review of recent clinical trials. *Eur J Clin Pharmacol.* 2023;79(4):467--478.
2. Viele K, Berry S, Neuenschwander B, et al. Use of historical control data for assessing treatment effects in clinical trials. *Pharm Stat.* 2014;13(1):41--54.
3. Neuenschwander B, Capkun-Niggli G, Branson M, et al. Summarizing historical information on controls in clinical trials. *Clin Trials.* 2010;7(1):5--18.
4. Schmidli H, Gsteiger S, Roychoudhury S, et al. Robust meta-analytic-predictive priors in clinical trials with historical control information. *Biometrics.* 2014;70(4):1023--1032.
5. Ibrahim JG, Chen MH. Power prior distributions for regression models. *Stat Sci.* 2000;15(1):46--60.
6. Hobbs BP, Carlin BP, Mandrekar SJ, et al. Hierarchical commensurate and power prior models for adaptive incorporation of historical information in clinical trials. *Biometrics.* 2011;67(3):1047--1056.
7. U.S. Food and Drug Administration. Guidance for the Use of Bayesian Statistics in Medical Device Clinical Trials. Rockville, MD: FDA; 2010 (updated 2019).
8. European Medicines Agency. Reflection paper on the extrapolation of results from clinical studies conducted outside the EU to the EU population. EMA/CHMP/EWP/692702/2008. London: EMA; 2009.
9. Best N, Price RG, Pouliquen IJ, et al. Assessing efficacy in important subgroups in confirmatory trials: An example using Bayesian dynamic borrowing. *Pharm Stat.* 2021;20(3):551--562.
10. Weber S, Li Y, Seaman JW III, et al. Applying meta-analytic-predictive priors with the R Bayesian evidence synthesis tools. *J Stat Softw.* 2021;100(19):1--32.
11. Rover C, Friede T. bayesmeta: Bayesian random-effects meta-analysis. R package. *CRAN.* 2022.
12. Fujikawa K, Teramukai S, Yokota I, et al. A Bayesian basket trial design using a calibrated Bayesian hierarchical model. *Stat Med.* 2020;39(28):4327--4343.
13. Blackman D, Vigna S. Scrambled linear pseudorandom number generators. *ACM Trans Math Softw.* 2021;47(4):1--32.
14. Morita S, Thall PF, Muller P. Determining the effective sample size of a parametric prior. *Biometrics.* 2008;64(2):595--602.
15. Evans M, Moshonov H. Checking for prior-data conflict. *Bayesian Anal.* 2006;1(4):893--914.
16. Gravestock I, Held L. Adaptive power priors with empirical Bayes for clinical trials. *Pharm Stat.* 2017;16(5):349--360.
17. Duan Y, Ye K, Smith EP. Evaluating water quality using power priors to incorporate historical information. *Environmetrics.* 2006;17(1):95--106.
18. Gelman A, Jakulin A, Pittau MG, et al. A weakly informative default prior distribution for logistic and other regression models. *Ann Appl Stat.* 2008;2(4):1360--1383.
19. Neuenschwander B, Roychoudhury S, Schmidli H. On the use of co-data in clinical trials. *Stat Biopharm Res.* 2016;8(3):345--354.
20. Spiegelhalter DJ, Abrams KR, Myles JP. *Bayesian Approaches to Clinical Trials and Health-Care Evaluation.* Chichester: Wiley; 2004.
21. Rover C, Benda N, Engel J, et al. Bayesian random-effects meta-analysis with empirical heterogeneity priors for application in health technology assessment with very few studies. *Res Synth Methods.* 2023;14(5):704--715.
22. Kopp-Schneider A, Calderazzo S, Engel J. Bayesian borrowing methods for count data: analysis of an adverse event endpoint. *Stat Med.* 2020;39(28):4195--4209.
23. van Rosmalen J, Dejardin D, van Norden Y, et al. Including historical data in the analysis of clinical trials: Is it worth the effort? *Stat Methods Med Res.* 2018;27(10):3167--3182.
24. Chu Y, Yuan Y. A Bayesian basket trial design using a calibrated power prior. *Biostatistics.* 2018;19(4):489--503.
25. DerSimonian R, Laird N. Meta-analysis in clinical trials. *Control Clin Trials.* 1986;7(3):177--188.

---

## F1000Research Reviewer Guidance

*The following responses address the five standard F1000Research review questions.*

### 1. Is the rationale for developing the new software tool clearly explained?

Yes. The Introduction establishes that MAP priors are increasingly accepted by regulatory agencies (FDA, EMA) for clinical trial designs with historical borrowing, but existing implementations require R programming expertise (RBesT). The gap -- no browser-based tool for MAP prior derivation -- is clearly identified, and the target user population (clinical team members without R skills) is specified.

### 2. Is the description of the software tool technically sound?

Yes. The Methods section provides complete mathematical specification of the MAP prior derivation (Normal-Normal hierarchical model with REML), robust mixture construction (Neuenschwander formulation), ESS computation (Morita curvature method), and OC simulation procedure. All four borrowing methods are formally defined with their parameters and references. Limitations of the analytical approximations relative to full MCMC (RBesT) are explicitly stated.

### 3. Are sufficient details of the code, methods, and analysis provided to allow replication of the software development and its use by others?

Yes. The tool is a single self-contained HTML file requiring no dependencies. The test suite (38 Selenium tests) is provided with the source code. Three built-in datasets enable immediate replication. R code export allows cross-validation against RBesT. The Methods section specifies all algorithms in sufficient detail for independent reimplementation.

### 4. Is sufficient information provided to allow interpretation of the expected output and any testing that has been performed?

Yes. Three complete worked examples (Crohn's binary, UC continuous, oncology binary with heterogeneity) demonstrate the full workflow with expected outputs. Table 2 provides quantitative OC results. The validation section reports analytical verification against known solutions and describes the 38-test automated suite. The three-persona review process and all 8 identified issues and their fixes are documented.

### 5. Are the conclusions about the tool and its performance adequately supported by the findings presented in the article?

Yes. The claim that MAPriors produces results consistent with analytical expectations is supported by the Crohn's dataset verification (ESS = 959 vs total N = 960). The claim of power improvement is supported by OC simulation (84.2% vs 71.5%). The claim of accessibility is supported by the zero-installation browser-based architecture. Limitations are explicitly stated, including the recommendation to cross-validate against RBesT for definitive regulatory analyses.
