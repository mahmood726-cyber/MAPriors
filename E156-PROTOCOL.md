# E156 Protocol — `MAPriors`

This repository is the source code and dashboard backing an E156 micro-paper on the [E156 Student Board](https://mahmood726-cyber.github.io/e156/students.html).

---

## `[83]` MAPriors: Browser-Based Meta-Analytic Predictive Priors and Dynamic Borrowing Engine

**Type:** methods  |  ESTIMAND: Effective sample size  
**Data:** Crohn disease placebo (Neuenschwander 2010), oncology, cardiovascular (built-in)

### 156-word body

Can meta-analytic predictive priors and dynamic borrowing be made accessible through a browser-based tool without requiring R or Stan programming expertise? Eight historical Crohn disease placebo-arm studies totaling 960 patients from the Neuenschwander canonical dataset were analyzed alongside oncology and cardiovascular built-in examples. MAPriors, a single-file HTML application of 2,565 lines, implements Bayesian hierarchical modeling with robust mixture priors, power priors, and commensurate priors, along with effective sample size computation via the Morita method. The Crohn dataset produced a prevalence MAP prior mean of 17.7% (95% credible interval 11.2-25.8%) with an effective sample size of 959 patients under near-zero heterogeneity. Operating characteristics simulation confirmed nominal type I error near 5% and power gains of 10 to 15 percentage points over vague-prior designs. This is the first browser-based MAP prior engine, validated by 38 Selenium tests, democratizing regulatory-grade Bayesian borrowing. A limitation is that the implementation uses approximate Gibbs sampling rather than full Hamiltonian Monte Carlo inference.

### Submission metadata

```
Corresponding author: Mahmood Ahmad <mahmood.ahmad2@nhs.net>
ORCID: 0000-0001-9107-3704
Affiliation: Tahir Heart Institute, Rabwah, Pakistan

Links:
  Code:      https://github.com/mahmood726-cyber/MAPriors
  Protocol:  https://github.com/mahmood726-cyber/MAPriors/blob/main/E156-PROTOCOL.md
  Dashboard: https://mahmood726-cyber.github.io/mapriors/

References (topic pack: Bayesian meta-analysis):
  1. Röver C. 2020. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 93(6):1-51. doi:10.18637/jss.v093.i06
  2. Higgins JPT, Thompson SG, Spiegelhalter DJ. 2009. A re-evaluation of random-effects meta-analysis. J R Stat Soc A. 172(1):137-159. doi:10.1111/j.1467-985X.2008.00552.x

Data availability: No patient-level data used. Analysis derived exclusively
  from publicly available aggregate records. All source identifiers are in
  the protocol document linked above.

Ethics: Not required. Study uses only publicly available aggregate data; no
  human participants; no patient-identifiable information; no individual-
  participant data. No institutional review board approval sought or required
  under standard research-ethics guidelines for secondary methodological
  research on published literature.

Funding: None.

Competing interests: MA serves on the editorial board of Synthēsis (the
  target journal); MA had no role in editorial decisions on this
  manuscript, which was handled by an independent editor of the journal.

Author contributions (CRediT):
  [STUDENT REWRITER, first author] — Writing – original draft, Writing –
    review & editing, Validation.
  [SUPERVISING FACULTY, last/senior author] — Supervision, Validation,
    Writing – review & editing.
  Mahmood Ahmad (middle author, NOT first or last) — Conceptualization,
    Methodology, Software, Data curation, Formal analysis, Resources.

AI disclosure: Computational tooling (including AI-assisted coding via
  Claude Code [Anthropic]) was used to develop analysis scripts and assist
  with data extraction. The final manuscript was human-written, reviewed,
  and approved by the author; the submitted text is not AI-generated. All
  quantitative claims were verified against source data; cross-validation
  was performed where applicable. The author retains full responsibility for
  the final content.

Preprint: Not preprinted.

Reporting checklist: PRISMA 2020 (methods-paper variant — reports on review corpus).

Target journal: ◆ Synthēsis (https://www.synthesis-medicine.org/index.php/journal)
  Section: Methods Note — submit the 156-word E156 body verbatim as the main text.
  The journal caps main text at ≤400 words; E156's 156-word, 7-sentence
  contract sits well inside that ceiling. Do NOT pad to 400 — the
  micro-paper length is the point of the format.

Manuscript license: CC-BY-4.0.
Code license: MIT.

SUBMITTED: [ ]
```


---

_Auto-generated from the workbook by `C:/E156/scripts/create_missing_protocols.py`. If something is wrong, edit `rewrite-workbook.txt` and re-run the script — it will overwrite this file via the GitHub API._