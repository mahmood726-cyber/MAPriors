# MAP Priors & Dynamic Borrowing Engine — Implementation Plan

## Vision
The world's first browser-based tool for **Meta-Analytic Predictive (MAP) priors** and **dynamic borrowing** in clinical trial design. Currently, RBesT (Novartis, R-only) is the gold standard, used in FDA/EMA regulatory submissions. This tool democratizes MAP priors for clinical teams without R expertise, enabling them to derive informative priors from historical data, simulate operating characteristics, and produce regulatory-ready outputs.

**No browser tool exists.** RBesT is R-only. This fills a critical gap in regulatory science.

## Why This Matters
- MAP priors are increasingly used in regulatory submissions (FDA, EMA, PMDA)
- Can reduce sample sizes by 20-40% when historical data is consistent
- Dynamic borrowing automatically discounts inconsistent historical data (safety valve)
- Industry demand is massive: every pharma company doing Bayesian clinical trials needs this
- Builds naturally on user's HTA expertise (41 engines) and Bayesian MA experience

## Core Concepts

### 1. Meta-Analytic Predictive (MAP) Prior
- Pool historical control arm data using Bayesian hierarchical model
- Derive a **predictive distribution** for the control arm response in a NEW trial
- This predictive distribution becomes the **informative prior** for the new trial's control arm
- Effect: borrows information from historical controls → smaller control arm needed

### 2. Robust MAP Prior (Mixture)
- Pure MAP prior is dangerous if new trial's control rate differs from history
- Solution: MAP prior mixed with a **vague/non-informative component**
  - E.g., 80% MAP + 20% vague
  - The vague component acts as a safety valve
- Tuning the mixture weight is a key design decision

### 3. Dynamic Borrowing
- Instead of fixed mixture weight, let the DATA determine how much to borrow
- Methods:
  - **Power prior** (Ibrahim & Chen): discount historical data by weight α₀
  - **Commensurate prior** (Hobbs et al.): shrinkage depends on prior-data conflict
  - **Empirical Bayes**: estimate borrowing weight from data
- More consistent history → more borrowing → smaller effective sample size
- Inconsistent history → less borrowing → falls back to non-informative

### 4. Effective Sample Size (ESS)
- Key regulatory metric: "How many patients is this prior worth?"
- ESS = Morita et al. (2008) method or Neuenschwander et al. (2020)
- Regulator wants to see: "Your prior contributes ESS=25 patients to the control arm"

## Architecture

### Single-file HTML app (`map-priors.html`)
- Target: ~18K-25K lines (mature)
- Seeded PRNG (xoshiro128**) for reproducibility
- WebR for RBesT cross-validation
- TruthCert integration for regulatory provenance

### Core Modules

#### 1. Historical Data Input
- Input historical control arm data:
  - **Binary**: events / N per study
  - **Continuous**: mean, SD, N per study
  - **Time-to-event**: median survival, HR, events, N per study
- CSV import, manual entry table
- Metadata: trial name, year, region, population, inclusion criteria
- Built-in datasets:
  - Crohn's disease (Neuenschwander 2010 classic example)
  - Oncology historical controls
  - Cardiovascular event rates

#### 2. Bayesian Hierarchical Model (MAP Prior Derivation)
**Normal-Normal model (continuous endpoints)**:
```
yᵢ | θᵢ ~ N(θᵢ, σᵢ²/nᵢ)     [likelihood]
θᵢ | μ, τ ~ N(μ, τ²)           [between-study]
μ ~ N(m₀, s₀²)                  [hyperprior on mean]
τ ~ HalfCauchy(0, scale)        [hyperprior on heterogeneity]
```

**Beta-Binomial model (binary endpoints)**:
```
xᵢ | pᵢ ~ Binomial(nᵢ, pᵢ)    [likelihood]
logit(pᵢ) | μ, τ ~ N(μ, τ²)   [between-study on logit scale]
```

**MAP predictive distribution**:
```
θ_new | data ~ ∫ N(μ, τ² + σ²_new) × p(μ, τ | data) dμ dτ
```

- MCMC sampling (Gibbs/Metropolis-Hastings in JS)
- OR: grid approximation for conjugate cases
- OR: WebR backend for JAGS/Stan-quality posterior

**Mixture approximation**: Fit the MAP predictive as a mixture of 2-4 conjugate components:
- Normal mixture: Σ wⱼ × N(μⱼ, σⱼ²)
- Beta mixture (binary): Σ wⱼ × Beta(aⱼ, bⱼ)
- EM algorithm for component fitting

#### 3. Robust MAP Prior Constructor
- Slider: informative weight (w) from 0% to 100%
  - w=100%: pure MAP prior (maximum borrowing)
  - w=0%: pure vague prior (no borrowing)
  - Default: w=50-80% (conservative robustification)
- Vague component specification:
  - Normal: N(0, 100²) or user-defined
  - Beta: Beta(1, 1) = Uniform(0,1)
- Real-time visualization: prior density updates as slider moves
- ESS displayed for each weight setting

#### 4. Dynamic Borrowing Module
Three methods, user selects:

**A. Power Prior (Ibrahim & Chen)**
- Historical likelihood raised to power α₀ ∈ [0, 1]
- α₀ = 1: full borrowing; α₀ = 0: no borrowing
- Can be fixed or treated as random (calibrated power prior)

**B. Commensurate Prior (Hobbs et al.)**
- θ_new | θ_hist ~ N(θ_hist, τ²_comm)
- τ²_comm controls commensurability
- Small τ²_comm → tight borrowing; large → loose
- Prior on τ²_comm: InvGamma or HalfCauchy

**C. Mixture Weight Dynamic (Schmidli et al.)**
- Posterior model weight: p(MAP | data) vs p(vague | data)
- Automatically upweights MAP when consistent, downweights when conflict
- No user tuning needed

#### 5. Operating Characteristics Simulator
**The regulatory-critical module.** Simulate trial performance under the designed prior.

Inputs:
- New trial design: N_treatment, N_control, endpoint type
- True treatment effect (range for sensitivity)
- True control rate (range: consistent with history, slightly different, very different)
- Decision criterion (e.g., P(δ > 0 | data) > 0.975)

Simulations (1,000-10,000 Monte Carlo):
- For each scenario:
  1. Generate new trial data under true parameters
  2. Analyze with MAP prior (Bayesian)
  3. Analyze with vague prior (Bayesian comparator)
  4. Analyze with frequentist (MLE comparator)
  5. Record: decision (success/fail), posterior mean, CI width

Outputs:
- **Type I error** (power at null) vs α level
- **Power** at target effect size
- **Bias** of posterior mean
- **MSE** of posterior estimate
- **Coverage** of credible intervals
- **ESS** (effective sample size of prior)
- **Borrowing fraction** (how much was actually borrowed)

Visualization:
- Operating characteristics curves (power vs true effect)
- OC table (scenarios × metrics)
- Prior-data conflict detection plots
- Comparison: MAP vs vague vs frequentist

#### 6. Sample Size Determination
- Given: target power, significance level, expected effect, MAP prior
- Compute: minimum N per arm with MAP prior
- Compare: N with MAP vs N without MAP (the "savings")
- Regulatory table: "MAP prior saves X patients (Y% reduction)"

#### 7. Prior-Data Conflict Diagnostics
- Tail probability: P(θ_new ∈ extreme tail of MAP prior | data)
- Bayesian p-value for conflict
- Box's conflict measure
- Visual: observed data overlaid on MAP prior → does it fall in a reasonable region?
- Traffic light: Green (consistent) / Yellow (borderline) / Red (conflict, borrowing reduced)

#### 8. Regulatory Reporting Module
- **FDA/EMA-ready output package**:
  - Prior specification document (mathematical notation)
  - OC tables with required scenarios
  - ESS justification
  - Sensitivity analyses (robustness to prior-data conflict)
  - Comparison with frequentist analysis
- Export: PDF report, Word-compatible table, CSV data
- TruthCert bundle: prior derivation provenance chain

#### 9. Visualization Suite
- **Prior evolution plot**: vague → MAP → robust MAP → posterior (animated)
- **Forest plot**: historical studies + MAP predictive band
- **Borrowing fraction plot**: how much was borrowed across scenarios
- **ESS curve**: ESS as function of mixture weight
- **OC curves**: power/type I error across effect sizes
- **Conflict diagnostic**: observed data vs prior density

## Implementation Phases

### Phase 1: MAP Prior Derivation (MVP)
- Historical data input (binary + continuous)
- Normal-Normal hierarchical model (grid approximation)
- MAP predictive distribution
- Mixture approximation (EM)
- ESS calculation
- Prior density plot
- 1 built-in dataset (Crohn's)
- **Target: ~5K lines**

### Phase 2: Robust MAP + Dynamic Borrowing
- Robust MAP constructor (mixture weight slider)
- Power prior implementation
- Commensurate prior
- Prior-data conflict diagnostics
- Forest plot with MAP predictive band
- **Target: ~12K lines**

### Phase 3: Operating Characteristics
- Full OC simulator (Web Worker)
- Power/type I error/bias/coverage/MSE
- Sample size determination
- Comparison: MAP vs vague vs frequentist
- OC curves + tables
- **Target: ~18K lines**

### Phase 4: Regulatory-Ready
- Regulatory reporting module (FDA/EMA templates)
- TruthCert integration
- WebR validation (RBesT parity)
- Time-to-event endpoint support
- 3+ built-in datasets
- Dark mode, accessibility, PDF export
- Multi-persona review + manuscript
- **Target: ~22K-25K lines**

## Testing Strategy
- Unit: hierarchical model posterior matches analytic solutions for conjugate cases
- Unit: MAP predictive matches RBesT output (via WebR, tolerance 1e-4)
- Integration: data input → MAP derivation → OC simulation pipeline
- Property: more historical studies → narrower MAP prior (if consistent)
- Property: higher heterogeneity → wider MAP prior
- Property: prior-data conflict → reduced borrowing
- Edge cases: k=1 historical study, k=0 (vague prior only), all identical studies
- Performance: 10,000 MC simulations in <30 seconds
- Selenium: 200+ tests

## Key References
- Schmidli et al. (2014) Robust MAP priors. Biometrics.
- Neuenschwander et al. (2010) MAP priors for binary data. Pharm Stat.
- Weber et al. (2021) RBesT R package. JSS.
- Ibrahim & Chen (2000) Power priors. Statistical Science.
- Hobbs et al. (2011) Commensurate priors. Biometrics.
- Morita et al. (2008) Effective sample size. Biometrics.
- FDA (2019) Guidance on use of Bayesian statistics in medical device trials.
- Viele et al. (2014) Use of historical controls. Pharm Stat.

## Success Criteria
- [ ] MAP prior matches RBesT within 1e-4 for Crohn's dataset
- [ ] Robust MAP ESS decreases monotonically as vague weight increases
- [ ] OC curves show correct type I error control under prior-data conflict
- [ ] Dynamic borrowing reduces borrowing when conflict detected
- [ ] Sample size savings correctly computed and displayed
- [ ] Regulatory report exports clean PDF
- [ ] 200+ Selenium tests pass
- [ ] Publishable paper: real-world example showing 30%+ sample size reduction
