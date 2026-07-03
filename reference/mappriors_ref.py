"""
mappriors_ref.py — Python reference implementation of the MAPriors engine.

This is a faithful, dependency-free port of the core numeric routines in
``map-priors.html`` (the browser-based Meta-Analytic Predictive prior and
dynamic-borrowing engine). It exists so the JS-only tool has a runnable,
inspectable, and *cross-validated* reference: ``tests/test_reference.py``
locks this port against ground-truth numbers emitted by the actual browser
code (``reference/js_reference_harness.js``) to a tolerance of 1e-9.

Method (mirrors the HTML exactly — see PLAN.md and the cited references):
  * Binary endpoints are analysed on the logit scale with a 0.5 continuity
    correction for empty / full cells.
  * Between-study heterogeneity tau^2 is initialised by DerSimonian-Laird and
    refined by a Newton step on the (RE)ML score.
  * The MAP predictive is N(mu_post, tau^2 + se_mu^2).
  * The robust MAP prior is a w:(1-w) mixture of the MAP component and a vague
    component; its effective sample size uses the Morita et al. (2008)
    curvature-at-the-mode method (``morita_ess_mixture``).

References (unchanged — do not edit):
  Neuenschwander et al. (2010) Pharm Stat; Morita et al. (2008) Biometrics;
  Schmidli et al. (2014) Biometrics; Weber et al. (2021) RBesT (JSS).

IMPORTANT: This file must never diverge numerically from map-priors.html.
If the HTML math changes, re-run the harness, re-freeze the ground truth, and
update this port so the reference test stays green. Never hand-tune numbers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Sequence


# --------------------------------------------------------------------------
# Built-in datasets (verbatim from DEMO_DATASETS in map-priors.html)
# --------------------------------------------------------------------------
DATASETS: Dict[str, Dict[str, Any]] = {
    "crohns": {
        "type": "binary",
        "description": "Crohn's disease placebo response rates (Neuenschwander et al. 2010).",
        "data": [
            {"trial": "Study A (2002)", "events": 15, "n": 80},
            {"trial": "Study B (2004)", "events": 22, "n": 120},
            {"trial": "Study C (2005)", "events": 18, "n": 95},
            {"trial": "Study D (2007)", "events": 25, "n": 150},
            {"trial": "Study E (2008)", "events": 12, "n": 70},
            {"trial": "Study F (2010)", "events": 30, "n": 175},
            {"trial": "Study G (2011)", "events": 20, "n": 110},
            {"trial": "Study H (2013)", "events": 28, "n": 160},
        ],
    },
    "uc": {
        "type": "continuous",
        "description": "Ulcerative colitis CDAI score improvements (historical controls).",
        "data": [
            {"trial": "ACT-1 (2005)", "mean": 5.2, "sd": 2.1, "n": 121},
            {"trial": "ACT-2 (2005)", "mean": 4.8, "sd": 2.3, "n": 123},
            {"trial": "GEMINI 1 (2013)", "mean": 5.5, "sd": 1.9, "n": 149},
            {"trial": "OCTAVE 1 (2018)", "mean": 5.1, "sd": 2.0, "n": 112},
            {"trial": "UNIFI (2019)", "mean": 4.9, "sd": 2.2, "n": 189},
            {"trial": "ELEVATE (2022)", "mean": 5.3, "sd": 1.8, "n": 158},
        ],
    },
    "onco": {
        "type": "binary",
        "description": "Oncology ORR historical controls (lung cancer immunotherapy).",
        "data": [
            {"trial": "Keynote-024 ctrl (2016)", "events": 31, "n": 154},
            {"trial": "Checkmate-078 ctrl (2018)", "events": 18, "n": 131},
            {"trial": "Impower-110 ctrl (2020)", "events": 28, "n": 163},
            {"trial": "Rationale-301 ctrl (2022)", "events": 24, "n": 152},
            {"trial": "JUPITER-02 ctrl (2021)", "events": 21, "n": 140},
        ],
    },
}


# --------------------------------------------------------------------------
# Numeric helpers (ports of normalPDF / normalQuantile in map-priors.html)
# --------------------------------------------------------------------------
def normal_pdf(x: float, mu: float, sigma: float) -> float:
    z = (x - mu) / sigma
    return math.exp(-0.5 * z * z) / (sigma * math.sqrt(2 * math.pi))


def normal_quantile(p: float) -> float:
    """Acklam rational approximation to the standard-normal inverse CDF.

    Byte-for-byte port of ``normalQuantile`` in map-priors.html so quantiles
    (and hence credible-interval endpoints) match the app to machine epsilon.
    """
    if p <= 0:
        return -math.inf
    if p >= 1:
        return math.inf
    if p == 0.5:
        return 0.0
    a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0]
    b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1]
    c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838e0,
         -2.549732539343734e0, 4.374664141464968e0, 2.938163982698783e0]
    d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0,
         3.754408661907416e0]
    p_low = 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= 1 - p_low:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def morita_ess_mixture(mu_map: float, var_map: float, w: float,
                       mu_vague: float, var_vague: float) -> float:
    """Effective precision of a 2-component normal mixture at its mode.

    Port of ``moritaESSMixture``: Newton-Raphson to the mode, then the negative
    second derivative of the log-density (Morita et al. 2008 curvature method).
    """
    se_map = math.sqrt(var_map)
    se_vague = math.sqrt(var_vague)
    mode = mu_map
    for _ in range(30):
        f1 = w * normal_pdf(mode, mu_map, se_map)
        f2 = (1 - w) * normal_pdf(mode, mu_vague, se_vague)
        f = f1 + f2
        if f < 1e-300:
            break
        fp = -f1 * (mode - mu_map) / var_map - f2 * (mode - mu_vague) / var_vague
        # (fpp computed in JS but unused for the Newton step; kept faithfully)
        _fpp = (f1 * ((mode - mu_map) ** 2 / var_map - 1) / var_map
                + f2 * ((mode - mu_vague) ** 2 / var_vague - 1) / var_vague)
        wfpp = (-f1 / var_map + f1 * (mode - mu_map) ** 2 / (var_map * var_map)
                - f2 / var_vague + f2 * (mode - mu_vague) ** 2 / (var_vague * var_vague))
        if abs(wfpp) < 1e-300:
            break
        step = fp / wfpp
        mode -= step
        if abs(step) < 1e-12:
            break
    f1 = w * normal_pdf(mode, mu_map, se_map)
    f2 = (1 - w) * normal_pdf(mode, mu_vague, se_vague)
    f = f1 + f2
    if f < 1e-300:
        return 1 / var_map
    fpp = (f1 * ((mode - mu_map) ** 2 / (var_map * var_map) - 1 / var_map)
           + f2 * ((mode - mu_vague) ** 2 / (var_vague * var_vague) - 1 / var_vague))
    fp = -f1 * (mode - mu_map) / var_map - f2 * (mode - mu_vague) / var_vague
    neg_curv = -fpp / f + (fp / f) ** 2
    return max(0.0, neg_curv)


# --------------------------------------------------------------------------
# Input validation
# --------------------------------------------------------------------------
def _validate_binary(studies: Sequence[dict]) -> None:
    if len(studies) < 2:
        raise ValueError("At least 2 historical studies are required to derive a MAP prior.")
    for i, s in enumerate(studies):
        if "events" not in s or "n" not in s:
            raise ValueError(f"Study {i} is missing required binary fields 'events'/'n': {s!r}")
        e, n = s["events"], s["n"]
        if not (isinstance(n, (int, float)) and n > 0):
            raise ValueError(f"Study {i} has non-positive N: {n!r}")
        if not (isinstance(e, (int, float)) and 0 <= e <= n):
            raise ValueError(f"Study {i} events must satisfy 0 <= events <= n (got events={e!r}, n={n!r})")


def _validate_continuous(studies: Sequence[dict]) -> None:
    if len(studies) < 2:
        raise ValueError("At least 2 historical studies are required to derive a MAP prior.")
    for i, s in enumerate(studies):
        for f in ("mean", "sd", "n"):
            if f not in s:
                raise ValueError(f"Study {i} is missing required continuous field {f!r}: {s!r}")
        if not (isinstance(s["sd"], (int, float)) and s["sd"] > 0):
            raise ValueError(f"Study {i} has non-positive SD: {s['sd']!r}")
        if not (isinstance(s["n"], (int, float)) and s["n"] > 0):
            raise ValueError(f"Study {i} has non-positive N: {s['n']!r}")


def _validate_weight_conf(w: float, conf_level: float) -> None:
    if not (0.0 <= w <= 1.0):
        raise ValueError(f"Robust mixture weight w must be in [0, 1] (got {w!r}).")
    if not (0.0 < conf_level < 1.0):
        raise ValueError(f"conf_level must be in (0, 1) (got {conf_level!r}).")


# --------------------------------------------------------------------------
# Result container
# --------------------------------------------------------------------------
@dataclass
class MAPResult:
    type: str
    mu: float
    se_mu: float
    tau2: float
    tau: float
    map_mu: float
    map_se: float
    map_var: float
    robust_mu: float
    robust_se: float
    robust_var: float
    vague_mu: float
    vague_se: float
    ess_map: float
    ess_robust: float
    k: int
    Q: float
    I2: float
    w: float
    confLevel: float
    # binary-only
    p_hat: float | None = None
    map_lower_logit: float | None = None
    map_upper_logit: float | None = None
    robust_lower_logit: float | None = None
    robust_upper_logit: float | None = None
    # continuous-only
    map_lower: float | None = None
    map_upper: float | None = None
    robust_lower: float | None = None
    robust_upper: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


# --------------------------------------------------------------------------
# Core derivations (ports of deriveMAPBinary / deriveMAPContinuous)
# --------------------------------------------------------------------------
def derive_map_binary(studies: Sequence[dict], w: float = 0.5,
                      conf_level: float = 0.95) -> MAPResult:
    _validate_binary(studies)
    _validate_weight_conf(w, conf_level)
    k = len(studies)
    yi: List[float] = []
    vi: List[float] = []
    for s in studies:
        e = 0.5 if s["events"] == 0 else (s["n"] - 0.5 if s["events"] == s["n"] else s["events"])
        p = e / s["n"]
        yi.append(math.log(p / (1 - p)))
        vi.append(1 / (s["n"] * p * (1 - p)))

    wi = [1 / v for v in vi]
    sum_w = sum(wi)
    mu_fe = sum(w_ * yi[i] for i, w_ in enumerate(wi)) / sum_w
    Q = sum(w_ * (yi[i] - mu_fe) ** 2 for i, w_ in enumerate(wi))
    C = sum_w - sum(w_ * w_ for w_ in wi) / sum_w
    tau2 = max(0.0, (Q - (k - 1)) / C)

    tau2 = _reml_refine(yi, vi, tau2)

    wi_final = [1 / (v + tau2) for v in vi]
    sw_final = sum(wi_final)
    mu_post = sum(w_ * yi[i] for i, w_ in enumerate(wi_final)) / sw_final
    se_mu = math.sqrt(1 / sw_final)
    map_var = tau2 + se_mu * se_mu
    map_se = math.sqrt(map_var)

    vague_mu = 0.0
    vague_var = 100.0
    robust_mu = w * mu_post + (1 - w) * vague_mu
    robust_var = (w * (map_var + mu_post * mu_post)
                  + (1 - w) * (vague_var + vague_mu * vague_mu)
                  - robust_mu * robust_mu)
    robust_se = math.sqrt(max(0.001, robust_var))

    p_hat = 1 / (1 + math.exp(-mu_post))
    single_info = p_hat * (1 - p_hat)
    ess_map = (1 / map_var) / single_info
    ess_robust = morita_ess_mixture(mu_post, map_var, w, vague_mu, vague_var) / single_info

    z = normal_quantile(1 - (1 - conf_level) / 2)
    return MAPResult(
        type="binary", mu=mu_post, se_mu=se_mu, tau2=tau2, tau=math.sqrt(tau2),
        map_mu=mu_post, map_se=map_se, map_var=map_var,
        robust_mu=robust_mu, robust_se=robust_se, robust_var=robust_var,
        vague_mu=vague_mu, vague_se=math.sqrt(vague_var), p_hat=p_hat,
        map_lower_logit=mu_post - z * map_se, map_upper_logit=mu_post + z * map_se,
        robust_lower_logit=robust_mu - z * robust_se,
        robust_upper_logit=robust_mu + z * robust_se,
        ess_map=ess_map, ess_robust=ess_robust,
        k=k, Q=Q, I2=(max(0.0, (Q - (k - 1)) / Q * 100) if Q > (k - 1) else 0.0),
        w=w, confLevel=conf_level,
    )


def derive_map_continuous(studies: Sequence[dict], w: float = 0.5,
                          conf_level: float = 0.95) -> MAPResult:
    _validate_continuous(studies)
    _validate_weight_conf(w, conf_level)
    k = len(studies)
    yi = [s["mean"] for s in studies]
    vi = [(s["sd"] * s["sd"]) / s["n"] for s in studies]

    wi = [1 / v for v in vi]
    sum_w = sum(wi)
    mu_fe = sum(w_ * yi[i] for i, w_ in enumerate(wi)) / sum_w
    Q = sum(w_ * (yi[i] - mu_fe) ** 2 for i, w_ in enumerate(wi))
    C = sum_w - sum(w_ * w_ for w_ in wi) / sum_w
    tau2 = max(0.0, (Q - (k - 1)) / C)

    tau2 = _reml_refine(yi, vi, tau2)

    wi_f = [1 / (v + tau2) for v in vi]
    sw_f = sum(wi_f)
    mu_post = sum(w_ * yi[i] for i, w_ in enumerate(wi_f)) / sw_f
    se_mu = math.sqrt(1 / sw_f)
    map_var = tau2 + se_mu * se_mu
    map_se = math.sqrt(map_var)

    grand_sd = math.sqrt(sum(vi) / k) * 10
    vague_mu = 0.0
    vague_var = grand_sd * grand_sd
    robust_mu = w * mu_post + (1 - w) * vague_mu
    robust_var = (w * (map_var + mu_post * mu_post)
                  + (1 - w) * (vague_var + vague_mu * vague_mu)
                  - robust_mu * robust_mu)
    robust_se = math.sqrt(max(0.001, robust_var))

    avg_sigma2 = sum(s["sd"] * s["sd"] for s in studies) / k
    single_info_cont = 1 / avg_sigma2
    ess_map = (1 / map_var) / single_info_cont
    ess_robust = morita_ess_mixture(mu_post, map_var, w, vague_mu, vague_var) / single_info_cont

    z = normal_quantile(1 - (1 - conf_level) / 2)
    return MAPResult(
        type="continuous", mu=mu_post, se_mu=se_mu, tau2=tau2, tau=math.sqrt(tau2),
        map_mu=mu_post, map_se=map_se, map_var=map_var,
        robust_mu=robust_mu, robust_se=robust_se, robust_var=robust_var,
        vague_mu=vague_mu, vague_se=math.sqrt(vague_var),
        map_lower=mu_post - z * map_se, map_upper=mu_post + z * map_se,
        robust_lower=robust_mu - z * robust_se, robust_upper=robust_mu + z * robust_se,
        ess_map=ess_map, ess_robust=ess_robust,
        k=k, Q=Q, I2=(max(0.0, (Q - (k - 1)) / Q * 100) if Q > (k - 1) else 0.0),
        w=w, confLevel=conf_level,
    )


def _reml_refine(yi: Sequence[float], vi: Sequence[float], tau2: float) -> float:
    """Newton refinement of tau^2 on the (RE)ML score — port of the shared
    50-iteration loop in deriveMAPBinary / deriveMAPContinuous."""
    for _ in range(50):
        wi2 = [1 / (v + tau2) for v in vi]
        sw2 = sum(wi2)
        mu = sum(w_ * yi[i] for i, w_ in enumerate(wi2)) / sw2
        wi3 = [w_ * w_ for w_ in wi2]
        r2 = [(y - mu) ** 2 for y in yi]
        dL = (-0.5 * sum(wi2) + 0.5 * sum(wi3) / sw2
              + 0.5 * sum(w_ * r2[i] for i, w_ in enumerate(wi3)))
        sum_w2 = sum(wi3)
        sum_w3 = sum(w_ * w_ * w_ for w_ in wi2)
        ddL = 0.5 * sum_w2 - sum_w3 / sw2 + 0.5 * (sum_w2 * sum_w2) / (sw2 * sw2)
        if abs(ddL) < 1e-15:
            break
        step = dL / ddL
        tau2 = max(0.0, tau2 + step)
        if abs(step) < 1e-10:
            break
    return tau2


def derive(dataset_or_studies, w: float = 0.5, conf_level: float = 0.95,
           endpoint: str | None = None) -> MAPResult:
    """Convenience entry point.

    ``dataset_or_studies`` may be a built-in dataset name (a key of DATASETS),
    or a list of study dicts (in which case ``endpoint`` selects binary /
    continuous, defaulting to binary if 'events' present else continuous).
    """
    if isinstance(dataset_or_studies, str):
        if dataset_or_studies not in DATASETS:
            raise KeyError(f"Unknown dataset {dataset_or_studies!r}. "
                           f"Available: {sorted(DATASETS)}")
        ds = DATASETS[dataset_or_studies]
        studies, etype = ds["data"], ds["type"]
    else:
        studies = list(dataset_or_studies)
        if not studies:
            raise ValueError("No studies provided.")
        etype = endpoint or ("binary" if "events" in studies[0] else "continuous")
    if etype == "binary":
        return derive_map_binary(studies, w, conf_level)
    if etype == "continuous":
        return derive_map_continuous(studies, w, conf_level)
    raise ValueError(f"Unsupported endpoint {etype!r} (expected 'binary' or 'continuous').")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _main(argv: Sequence[str] | None = None) -> int:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        prog="mappriors_ref",
        description="Reference MAP-prior / robust-MAP derivation (mirrors map-priors.html).")
    parser.add_argument("dataset", nargs="?", default="crohns",
                        help="Built-in dataset name (crohns/uc/onco) or path to a "
                             "JSON file with a list of study dicts.")
    parser.add_argument("-w", "--weight", type=float, default=1.0,
                        help="Robust mixture weight in [0,1] (1.0 = pure MAP).")
    parser.add_argument("-c", "--conf", type=float, default=0.95,
                        help="Credible-interval level (default 0.95).")
    parser.add_argument("--endpoint", choices=["binary", "continuous"], default=None,
                        help="Endpoint type when loading a JSON file.")
    parser.add_argument("--json", action="store_true", help="Emit full result as JSON.")
    args = parser.parse_args(argv)

    if args.dataset in DATASETS:
        res = derive(args.dataset, args.weight, args.conf)
        label = args.dataset
    else:
        with open(args.dataset, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        studies = payload if isinstance(payload, list) else payload.get("studies", payload.get("data", []))
        res = derive(studies, args.weight, args.conf, endpoint=args.endpoint)
        label = args.dataset

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    d = res.to_dict()
    print(f"Dataset: {label}   endpoint={res.type}   k={res.k}   w={res.w}   conf={res.confLevel}")
    print(f"  tau^2            = {res.tau2:.6f}   (I^2 = {res.I2:.1f}%)")
    print(f"  MAP mean (mu)    = {res.mu:.6f}   SE = {res.map_se:.6f}")
    if res.type == "binary":
        print(f"  MAP mean (prob)  = {res.p_hat*100:.2f}%")
    print(f"  ESS (pure MAP)   = {res.ess_map:.2f} patients")
    print(f"  ESS (robust MAP) = {res.ess_robust:.2f} patients")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
