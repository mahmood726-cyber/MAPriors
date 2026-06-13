# MAPriors

A single-file, offline HTML tool for meta-analytic predictive (MAP) priors and
dynamic borrowing of historical control data.

`map-priors.html` runs entirely in the browser (no R, Stan, or server). It
implements:

- Bayesian hierarchical pooling of historical studies on the logit (binary) or
  raw (continuous) scale, with DErSimonian-Laird heterogeneity refined by REML.
- A MAP predictive prior and a robust (MAP + vague) mixture prior.
- Effective sample size (ESS) via the Morita method, including the mixture-mode
  curvature for the robust prior.
- Built-in example datasets (Crohn disease placebo arms, oncology,
  cardiovascular).

## Running

Open `map-priors.html` in any modern browser, or serve the folder and visit
`index.html`.

## Tests

Smoke tests run without a browser:

```
python -m pytest -q
```

The Selenium end-to-end suites in `tests/` and `selenium_map_priors_legacy.py`
exercise the live app in Chrome and are skipped during normal collection. To run
them:

```
RUN_BROWSER_TESTS=1 python -m pytest tests/test_mapriors.py -v
```

## Notes

The implementation uses approximate Gibbs-style estimation rather than full
Hamiltonian Monte Carlo. See `E156-PROTOCOL.md` for the accompanying micro-paper.
