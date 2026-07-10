# MAPriors

A single-file, offline HTML tool for meta-analytic predictive (MAP) priors and
dynamic borrowing of historical control data.

The core engine runs entirely in the browser (no R, Stan, or server) and needs
no network access for any pooling, prior, ESS, or simulation feature. It
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

Install the test dependencies first:

```
pip install -r requirements-dev.txt
```

The default suite runs without a browser and covers both the packaging smoke
tests and a numerical suite that exercises the statistical core (pooling, MAP /
robust-mixture / power priors, Morita ESS, TTE conversion) against a
version-controlled baseline (`tests/baseline_map_priors.json`):

```
python -m pytest -q
```

The numerical suite (`tests/test_numerical.py`) evaluates the app's inline JS
estimators headlessly and therefore needs **Node.js** on `PATH`; those tests
skip cleanly if `node` is not installed.

The Selenium end-to-end suites in `tests/` and `selenium_map_priors_legacy.py`
exercise the live app in Chrome and are skipped during normal collection. They
additionally require a local Chrome/Chromium install (Selenium 4.6+ auto-manages
chromedriver). To run them:

```
RUN_BROWSER_TESTS=1 python -m pytest tests/test_mapriors.py -v
```

## Optional online feature: R cross-validation (WebR)

The app ships one **optional** button, "Validate with R (WebR)", that is the
sole exception to the offline claim above. When (and only when) it is clicked it
dynamically imports the WebR runtime and installs the `metafor` package from
`webr.r-wasm.org` to cross-check the JS estimates against R. This step requires
network access and downloads an R/WebAssembly runtime; every other feature works
fully offline. Do not use this button in an air-gapped deployment.

## Notes

The implementation uses approximate Gibbs-style estimation rather than full
Hamiltonian Monte Carlo. See `E156-PROTOCOL.md` for the accompanying micro-paper.
