"""Browser-free numerical tests for the MAPriors statistical core.

The app is a single HTML file whose estimators live in an inline <script>.
`tests/js_harness.js` loads that script into a Node `vm` (with a minimal DOM
stub) and evaluates the pure statistical functions on fixed datasets. This
module:

  1. asserts a set of *independently derived* numerical identities (true unit
     tests with known-correct answers -- not just a snapshot), and
  2. pins the full harness output to the committed baseline
     `tests/baseline_map_priors.json` (the portfolio numerical-baseline
     contract) so any silent change to an estimator fails CI, and
  3. exercises the high-risk edge cases (events=0, events=n continuity
     correction; tau2=0; k=2; robust mixture at w in {0,1}).

These run under the default `python -m pytest -q` collection (no browser,
no RUN_BROWSER_TESTS gate). Node.js is required; the tests skip cleanly if it
is absent.

Regenerate the baseline after an intended estimator change:
    node tests/js_harness.js > tests/baseline_map_priors.json
(then re-indent/sort, or run the one-liner in the repo's test docs).
"""
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "js_harness.js"
BASELINE = ROOT / "tests" / "baseline_map_priors.json"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="Node.js not available for headless JS eval"
)

# Absolute tolerance for pinning the derive/ESS/power outputs to baseline.
ABS_TOL = 1e-9


def _run_harness():
    proc = subprocess.run(
        ["node", str(HARNESS)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"harness failed: {proc.stderr}"
    assert proc.stdout.strip(), "harness produced no output"
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def out():
    return _run_harness()


def _all_finite(o, path=""):
    bad = []
    if isinstance(o, dict):
        for k, v in o.items():
            bad += _all_finite(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            bad += _all_finite(v, f"{path}[{i}]")
    elif isinstance(o, bool):
        pass
    elif isinstance(o, (int, float)):
        if not math.isfinite(o):
            bad.append(f"{path}={o}")
    return bad


# ---------------------------------------------------------------------------
# 1. Independently-derived identities (known-correct answers)
# ---------------------------------------------------------------------------

def test_normalcdf_known_points(out):
    assert out["normalCDF_0"] == pytest.approx(0.5, abs=1e-12)
    # Abramowitz-Stegun 7.1.26 rational approx: accurate to ~1e-4
    assert out["normalCDF_196"] == pytest.approx(0.975, abs=5e-4)
    assert out["normalCDF_neg196"] == pytest.approx(0.025, abs=5e-4)


def test_normalquantile_known_points(out):
    # 97.5th percentile of the standard normal.
    assert out["normalQuantile_975"] == pytest.approx(1.959963984540054, abs=1e-6)
    assert out["normalQuantile_5"] == 0
    assert out["normalPDF_std0"] == pytest.approx(1 / math.sqrt(2 * math.pi), abs=1e-12)


def test_morita_ess_reduces_to_normal_precision_at_w1(out):
    # A 2-component mixture with w=1 is a pure normal with variance 0.25;
    # the Morita curvature (effective precision) must equal 1/0.25 = 4 exactly.
    assert out["morita_w1"] == pytest.approx(4.0, abs=1e-9)
    # w=0 -> pure vague normal, precision 1/100 = 0.01.
    assert out["morita_w0"] == pytest.approx(0.01, abs=1e-9)


def test_tte_to_loghr_exact(out):
    # Exponential: log(lambda) = log(ln2 / median); Parmar SE = 1/sqrt(events).
    expected_yi = math.log(math.log(2) / 12)
    assert out["tte"]["yi"] == pytest.approx(expected_yi, abs=1e-12)
    assert out["tte"]["se"] == pytest.approx(0.1, abs=1e-12)
    assert out["tte"]["vi"] == pytest.approx(0.01, abs=1e-12)
    # events=0 must be floored by Math.max(1, events) -> se=1, not Infinity.
    assert out["tte_events0"]["se"] == 1.0
    assert math.isfinite(out["tte_events0"]["vi"])


def test_chi2cdf_sanity(out):
    assert out["chi2CDF_df1_x0"] == 0
    # chi-square(1) 0.95 critical value is 3.8415; Wilson-Hilferty approx ~1e-2.
    assert out["chi2CDF_df1_x384"] == pytest.approx(0.95, abs=1e-2)


def test_continuous_homogeneous_matches_inverse_variance(out):
    # Two identical studies (mean 5, sd 2, n 100): Q=0 so tau2=0, and the
    # posterior mean must equal the common mean with se = sqrt(1/sum(1/vi)).
    r = out["cont_homog"]
    assert r["tau2"] == pytest.approx(0.0, abs=1e-12)
    assert r["mu"] == pytest.approx(5.0, abs=1e-9)
    vi = (2.0 ** 2) / 100  # 0.04 per study
    se = math.sqrt(1.0 / (2 * (1.0 / vi)))
    assert r["se_mu"] == pytest.approx(se, abs=1e-9)
    assert r["map_var"] == pytest.approx(vi / 2, abs=1e-9)  # tau2 + se_mu^2 = se_mu^2


def test_power_prior_ess_is_alpha0_times_total_n(out):
    # ESS of the power prior is alpha0 * sum(historical n). DS_BIN totals 448,
    # alpha0 = 0.5 -> 224.
    assert out["power_bin"]["ess"] == pytest.approx(0.5 * 448, abs=1e-9)


# ---------------------------------------------------------------------------
# 2. Edge cases (high-risk untested paths)
# ---------------------------------------------------------------------------

def test_binary_zero_events_continuity(out):
    # events=0 gets 0.5 continuity correction -> finite logit, no NaN/Inf.
    r = out["bin_zero"]
    assert not _all_finite(r), "unexpected non-finite value in events=0 result"
    assert 0 < r["p_hat"] < 1


def test_binary_full_events_continuity(out):
    # events=n gets (n-0.5) continuity correction -> finite, p_hat < 1.
    r = out["bin_full"]
    assert not _all_finite(r)
    assert 0 < r["p_hat"] < 1


def test_k2_dataset_runs(out):
    # k=2 is the minimum RunMAP allows; it must produce a finite result.
    r = out["cont_homog"]
    assert r["k"] == 2
    assert not _all_finite(r)


def test_robust_mixture_boundaries(out):
    # w=1 -> robust prior collapses onto the MAP mean; w=0 -> onto the vague
    # mean (0). Both must stay finite.
    w1 = out["cont_het_w1"]
    w0 = out["cont_het_w0"]
    assert w1["robust_mu"] == pytest.approx(w1["map_mu"], abs=1e-9)
    assert w0["robust_mu"] == pytest.approx(0.0, abs=1e-9)
    assert not _all_finite(w1)
    assert not _all_finite(w0)


# ---------------------------------------------------------------------------
# 3. Regression baseline (pins every estimator output)
# ---------------------------------------------------------------------------

def _compare(expected, actual, path=""):
    diffs = []
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: type changed to {type(actual)}"
        assert set(expected) == set(actual), (
            f"{path}: key set changed "
            f"(missing={set(expected) - set(actual)}, extra={set(actual) - set(expected)})"
        )
        for k in expected:
            diffs += _compare(expected[k], actual[k], f"{path}.{k}")
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(expected) == len(actual), (
            f"{path}: list length changed"
        )
        for i in range(len(expected)):
            diffs += _compare(expected[i], actual[i], f"{path}[{i}]")
    elif isinstance(expected, bool) or isinstance(actual, bool):
        if expected != actual:
            diffs.append(f"{path}: {expected} != {actual}")
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if not math.isclose(expected, actual, abs_tol=ABS_TOL, rel_tol=1e-9):
            diffs.append(f"{path}: baseline {expected} != {actual}")
    else:
        if expected != actual:
            diffs.append(f"{path}: {expected!r} != {actual!r}")
    return diffs


def test_matches_committed_baseline(out):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    diffs = _compare(baseline, out)
    assert not diffs, "estimator output drifted from baseline:\n" + "\n".join(diffs[:40])
