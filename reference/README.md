# MAPriors — Python reference implementation & benchmark

The MAPriors engine (`../map-priors.html`) is a single-file browser app. This
directory adds a small, dependency-free **Python reference port** of its core
numeric routines plus a **reproducible benchmark**, so the method can be run,
inspected, and cross-validated outside a browser.

Everything here mirrors the JS in `map-priors.html`. It does **not** introduce
any new statistical method or change any of the app's numbers — it reproduces
them and proves parity.

## Files

| File | Purpose |
|------|---------|
| `mappriors_ref.py` | Python port of `deriveMAPBinary` / `deriveMAPContinuous` / `moritaESSMixture` / `normalQuantile`, the three built-in datasets, input validation, and a CLI. |
| `js_reference_harness.js` | Node harness containing the **verbatim** JS functions from `map-priors.html`. Emits ground-truth results. |
| `js_ground_truth.json` | Frozen output of the harness (3 datasets × 5 mixture weights). The Python port is locked against this. |
| `benchmark.py` | Runs the reference over all datasets × a weight grid, prints a results table, and audits parity against the frozen ground truth. |

## Method (unchanged from the app)

Binary endpoints are analysed on the logit scale (0.5 continuity correction for
empty/full cells); between-study heterogeneity `tau^2` is initialised by
DerSimonian–Laird and refined by a Newton step on the (RE)ML score. The MAP
predictive is `N(mu_post, tau^2 + se_mu^2)`. The robust MAP prior is a
`w : (1-w)` mixture of the MAP component and a vague component, and its
effective sample size (ESS) uses the Morita et al. (2008) curvature-at-the-mode
method.

> Note: the app reports ESS on a per-patient-Fisher-information basis; the
> reference reproduces that convention exactly rather than re-deriving it.

## Usage

Derive a MAP prior for a built-in dataset:

```bash
python reference/mappriors_ref.py crohns -w 1.0        # pure MAP
python reference/mappriors_ref.py uc -w 0.8            # robust MAP, 80% weight
python reference/mappriors_ref.py onco -w 0.5 --json   # full result as JSON
```

Load your own studies from a JSON file (list of `{trial, events, n}` for
binary, or `{trial, mean, sd, n}` for continuous):

```bash
python reference/mappriors_ref.py my_studies.json --endpoint binary
```

As a library:

```python
import sys; sys.path.insert(0, "reference")
import mappriors_ref as ref
res = ref.derive("crohns", w=1.0)
print(res.ess_map, res.mu, res.tau2)
```

## Reproducible benchmark

```bash
python reference/benchmark.py                 # table to stdout
python reference/benchmark.py --csv out.csv   # also write CSV
```

The benchmark prints tau^2, I^2, MAP mean/SE, and ESS (pure + robust) for each
dataset and mixture weight, then reports the **maximum absolute deviation from
the browser JS ground truth**. Current parity: `< 5e-14` across all rows.

## Regenerating the ground truth

Only needed if the numeric code in `map-priors.html` changes. Re-copy the
changed function(s) verbatim into `js_reference_harness.js`, then:

```bash
node reference/js_reference_harness.js > reference/js_ground_truth.json
python -m pytest tests/test_reference.py -q
```

Never hand-edit the numbers in `js_ground_truth.json`.

## Tests

`../tests/test_reference.py` asserts:
* the Python port matches the frozen JS ground truth to `1e-9` for every
  dataset × weight;
* property invariants from `../PLAN.md` (robust ESS non-increasing as vague
  weight grows; wider credible interval at higher confidence; CI ordering);
* input validation (≥2 studies, `0 ≤ events ≤ n`, positive SD, `w ∈ [0,1]`,
  `conf ∈ (0,1)`, known dataset).

## Key references

Neuenschwander et al. (2010, *Pharm Stat*); Morita et al. (2008,
*Biometrics*); Schmidli et al. (2014, *Biometrics*); Weber et al. (2021,
RBesT, *JSS*).
