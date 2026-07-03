"""benchmark.py — reproducible MAPriors reference benchmark.

Runs the Python reference (reference/mappriors_ref.py) over every built-in
dataset across a grid of robust-mixture weights and prints a table of the key
regulatory quantities (tau^2, I^2, MAP mean, MAP SE, ESS pure, ESS robust).

It ALSO cross-checks each row against the frozen JS ground truth
(reference/js_ground_truth.json) and reports the maximum absolute deviation,
so the benchmark doubles as a parity audit between the browser app and this
reference port.

Run:
    python reference/benchmark.py                 # table to stdout
    python reference/benchmark.py --csv out.csv   # also write a CSV

No randomness, no external dependencies — output is fully deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

REF_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REF_DIR))

import mappriors_ref as ref  # noqa: E402

WEIGHTS = [0.0, 0.25, 0.5, 0.8, 1.0]
GROUND_TRUTH = REF_DIR / "js_ground_truth.json"


def _max_dev_vs_js(name: str, w: float, res_dict: dict) -> float | None:
    """Max abs deviation of this row's numeric fields vs frozen JS ground truth."""
    if not GROUND_TRUTH.exists():
        return None
    gt = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    block = gt.get(name, {}).get("weights", {}).get(f"{w:.2f}")
    if block is None:
        return None
    worst = 0.0
    for k, v in block.items():
        if isinstance(v, (int, float)) and k in res_dict and isinstance(res_dict[k], (int, float)):
            worst = max(worst, abs(res_dict[k] - v))
    return worst


def run(csv_path: str | None = None) -> int:
    rows = []
    header = ["dataset", "endpoint", "k", "w", "tau2", "I2_pct",
              "map_mean", "map_se", "ess_pure_map", "ess_robust", "max_dev_vs_js"]
    worst_overall = 0.0
    for name in ref.DATASETS:
        for w in WEIGHTS:
            r = ref.derive(name, w=w, conf_level=0.95)
            d = r.to_dict()
            dev = _max_dev_vs_js(name, w, d)
            if dev is not None:
                worst_overall = max(worst_overall, dev)
            rows.append({
                "dataset": name, "endpoint": r.type, "k": r.k, "w": w,
                "tau2": r.tau2, "I2_pct": r.I2, "map_mean": r.mu,
                "map_se": r.map_se, "ess_pure_map": r.ess_map,
                "ess_robust": r.ess_robust,
                "max_dev_vs_js": dev if dev is not None else float("nan"),
            })

    # Pretty table
    print(f"{'dataset':<8} {'endp':<10} {'k':>2} {'w':>5} {'tau2':>9} "
          f"{'I2%':>6} {'map_mean':>10} {'map_se':>8} {'ESS_MAP':>9} "
          f"{'ESS_rob':>9} {'devVsJS':>9}")
    print("-" * 100)
    for row in rows:
        dev = row["max_dev_vs_js"]
        dev_s = "n/a" if math.isnan(dev) else f"{dev:.2e}"
        print(f"{row['dataset']:<8} {row['endpoint']:<10} {row['k']:>2} "
              f"{row['w']:>5.2f} {row['tau2']:>9.5f} {row['I2_pct']:>6.1f} "
              f"{row['map_mean']:>10.5f} {row['map_se']:>8.5f} "
              f"{row['ess_pure_map']:>9.2f} {row['ess_robust']:>9.2f} {dev_s:>9}")
    print("-" * 100)
    if GROUND_TRUTH.exists():
        status = "PASS" if worst_overall < 1e-9 else "FAIL"
        print(f"Parity vs browser JS ground truth: max abs deviation = "
              f"{worst_overall:.2e}  [{status} @ 1e-9]")
    else:
        print("Ground-truth file not found; skipping parity audit. "
              "(Run: node reference/js_reference_harness.js > reference/js_ground_truth.json)")

    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=header)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        print(f"Wrote CSV: {csv_path}")

    return 0 if (not GROUND_TRUTH.exists() or worst_overall < 1e-9) else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Reproducible MAPriors reference benchmark.")
    p.add_argument("--csv", default=None, help="Optional path to also write results as CSV.")
    raise SystemExit(run(p.parse_args().csv))
