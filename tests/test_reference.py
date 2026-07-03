"""Cross-validation + property tests for the Python reference port.

test_reference.py locks reference/mappriors_ref.py against ground-truth
numbers emitted by the ACTUAL browser code (reference/js_reference_harness.js,
frozen into reference/js_ground_truth.json). Any numeric drift between the
Python port and the HTML app fails here.

No scientific number is asserted by hand: the expected values come straight
from the app's own JS, so this test proves parity, not correctness of a
hand-typed constant.
"""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "reference"
sys.path.insert(0, str(REF_DIR))

import mappriors_ref as ref  # noqa: E402


GROUND_TRUTH_PATH = REF_DIR / "js_ground_truth.json"

# Fields present in every result; compared against the JS harness output.
COMMON_FIELDS = [
    "mu", "se_mu", "tau2", "tau", "map_mu", "map_se", "map_var",
    "robust_mu", "robust_se", "robust_var", "vague_mu", "vague_se",
    "ess_map", "ess_robust", "Q", "I2",
]
BINARY_ONLY = ["p_hat", "map_lower_logit", "map_upper_logit",
               "robust_lower_logit", "robust_upper_logit"]
CONTINUOUS_ONLY = ["map_lower", "map_upper", "robust_lower", "robust_upper"]

TOL = 1e-9


def _load_ground_truth():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _cases():
    gt = _load_ground_truth()
    for name, block in gt.items():
        for w_str, expected in block["weights"].items():
            yield name, float(w_str), expected


@pytest.mark.parametrize("name,w,expected", list(_cases()))
def test_python_port_matches_js_ground_truth(name, w, expected):
    res = ref.derive(name, w=w, conf_level=0.95).to_dict()
    fields = list(COMMON_FIELDS)
    fields += BINARY_ONLY if expected["type"] == "binary" else CONTINUOUS_ONLY
    for f in fields:
        assert f in res, f"{name} w={w}: missing field {f}"
        got, exp = res[f], expected[f]
        assert math.isclose(got, exp, rel_tol=TOL, abs_tol=TOL), \
            f"{name} w={w} field {f}: python={got!r} js={exp!r}"


# ---------------------------------------------------------------------------
# Property tests (encode the invariants stated in PLAN.md's testing strategy)
# ---------------------------------------------------------------------------
def test_robust_ess_decreases_as_vague_weight_increases():
    """More vague weight (smaller w) => not more borrowing => ESS non-increasing.

    PLAN.md success criterion: robust MAP ESS decreases monotonically as the
    vague weight increases (i.e. as w decreases from 1 to 0)."""
    prev = None
    for w in [1.0, 0.8, 0.5, 0.25, 0.0]:
        ess = ref.derive("crohns", w=w).ess_robust
        if prev is not None:
            assert ess <= prev + 1e-9, f"ESS not monotonically decreasing at w={w}"
        prev = ess


def test_pure_map_weight_one_uses_map_precision():
    r = ref.derive("crohns", w=1.0)
    # At w=1 the robust mixture is the MAP component, so robust ESS ~ pure MAP ESS.
    assert math.isclose(r.ess_robust, r.ess_map, rel_tol=1e-6)


def test_credible_interval_ordering():
    for name in ref.DATASETS:
        r = ref.derive(name, w=0.8)
        d = r.to_dict()
        lo = d.get("map_lower_logit", d.get("map_lower"))
        hi = d.get("map_upper_logit", d.get("map_upper"))
        assert lo < r.mu < hi


def test_higher_conf_widens_interval():
    r95 = ref.derive("crohns", w=1.0, conf_level=0.95)
    r99 = ref.derive("crohns", w=1.0, conf_level=0.99)
    w95 = r95.to_dict()["map_upper_logit"] - r95.to_dict()["map_lower_logit"]
    w99 = r99.to_dict()["map_upper_logit"] - r99.to_dict()["map_lower_logit"]
    assert w99 > w95


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
def test_requires_two_studies():
    with pytest.raises(ValueError):
        ref.derive_map_binary([{"events": 5, "n": 10}])


def test_rejects_events_exceeding_n():
    with pytest.raises(ValueError):
        ref.derive_map_binary([{"events": 20, "n": 10}, {"events": 3, "n": 10}])


def test_rejects_negative_sd():
    with pytest.raises(ValueError):
        ref.derive_map_continuous([{"mean": 1, "sd": -1, "n": 10},
                                   {"mean": 2, "sd": 1, "n": 10}])


def test_rejects_out_of_range_weight():
    with pytest.raises(ValueError):
        ref.derive("crohns", w=1.5)


def test_rejects_bad_conf_level():
    with pytest.raises(ValueError):
        ref.derive("crohns", w=0.5, conf_level=1.5)


def test_unknown_dataset_raises():
    with pytest.raises(KeyError):
        ref.derive("nonexistent")


# ---------------------------------------------------------------------------
# Numeric helper parity (quantile against known value)
# ---------------------------------------------------------------------------
def test_normal_quantile_symmetry():
    assert math.isclose(ref.normal_quantile(0.975), -ref.normal_quantile(0.025), rel_tol=1e-12)


def test_normal_quantile_median():
    assert ref.normal_quantile(0.5) == 0.0
