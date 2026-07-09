"""
compute_irr.py
--------------
Compare each model rater against the three human raters (robin, veronica, jana). Also
computes and prints the human-only baseline agreement as a Python constant dictionary.

Supported metrics (choose one or more via --metrics):
  krippendorff   Krippendorff's alpha (nominal)  [default]
  fleiss         Fleiss' kappa
  majority       Majority-agreement rate: fraction of samples where the model
                 agrees with the majority human vote (ties broken in favour of
                 agreement if the model's value is one of the tied majority values)

All metrics are bootstrapped (resample entire samples) to produce 95 % CIs.

Constant columns (no variability) are reported as "const" instead of being
left blank, so you can tell the difference from a genuine computation failure.

A "model" is uniquely identified by (rater, codebook, individual_questions).
Human raters (robin / veronica / jana) are pooled regardless of those fields.

Output columns per metric M (one row per model combo):
  rater, codebook, individual_questions
  <col>_<M>_mean / ci_low / ci_high   for every data column
  <macro>_<M>_mean / ci_low / ci_high for every multi-column macro group
  overall_<M>_mean / ci_low / ci_high

Usage:
  python compute_irr.py input.csv output.csv
  python compute_irr.py input.csv output.csv --metrics krippendorff fleiss majority
  python compute_irr.py input.csv output.csv --n-boot 5000 --ci 0.95 --seed 42
"""

import argparse
import pprint
import sys

import krippendorff
import numpy as np
import pandas as pd
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HUMAN_RATERS = {"robin", "veronica", "jana"}
META_COLUMNS  = {"text", "rater", "codebook", "individual_questions"}
ALL_METRICS   = ["krippendorff", "fleiss", "majority"]

CONST_SENTINEL = "const"   # written when a column has no variability

# ---------------------------------------------------------------------------
# Helpers: data layout
# ---------------------------------------------------------------------------


def data_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in META_COLUMNS]


def macro_groups(cols: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for c in cols:
        key = c.split("-")[0] if "-" in c else c
        groups.setdefault(key, []).append(c)
    return groups


def build_reliability_matrix(
    samples: list[str],
    rater_dfs: dict[str, pd.DataFrame],
    column: str,
) -> np.ndarray:
    """Returns a (n_raters × n_samples) float matrix; missing → nan."""
    matrix = np.full((len(rater_dfs), len(samples)), np.nan)
    for r_idx, rdf in enumerate(rater_dfs.values()):
        for s_idx, sample in enumerate(samples):
            if sample in rdf.index:
                val = rdf.at[sample, column]
                if not isinstance(val, (float, int, np.floating, np.integer)):
                    val = float(val) if pd.notna(val) else np.nan
                if pd.notna(val):
                    matrix[r_idx, s_idx] = float(val)
    return matrix


def is_constant(matrix: np.ndarray) -> bool:
    """True when every non-nan cell has the same value."""
    vals = matrix[~np.isnan(matrix)]
    return len(vals) == 0 or np.all(vals == vals[0])


# ---------------------------------------------------------------------------
# Metric functions  (each takes a raters×units matrix, returns float | nan)
# ---------------------------------------------------------------------------


def metric_krippendorff(matrix: np.ndarray) -> float:
    valid = np.sum(~np.isnan(matrix), axis=0) >= 2
    m = matrix[:, valid]
    if m.shape[1] < 2:
        return np.nan
    try:
        return float(krippendorff.alpha(m, level_of_measurement="nominal"))
    except Exception:
        return np.nan


def metric_fleiss(matrix: np.ndarray) -> float:
    """
    Fleiss' kappa.  Requires every unit to have ratings from all raters — units
    with any nan are dropped.  Returns nan if fewer than 2 units remain or if
    the column is constant.
    """
    complete = ~np.any(np.isnan(matrix), axis=0)
    m = matrix[:, complete].T.astype(int)   # shape: (n_units, n_raters)
    if m.shape[0] < 2:
        return np.nan
    try:
        table, _ = aggregate_raters(m)
        return float(fleiss_kappa(table))
    except Exception:
        return np.nan


def metric_majority(matrix: np.ndarray) -> float:
    """
    Majority-agreement rate: fraction of samples where the model (first row)
    agrees with the majority vote of the human raters (remaining rows).
    Majority = the value chosen by strictly more than half the humans.
    If humans are evenly split, the sample is counted as agreement when the
    model's value equals any of the tied values (lenient tie-breaking).
    Returns nan if no valid samples exist.
    """
    model_row  = matrix[0]       # first rater = model  (see pool construction)
    human_rows = matrix[1:]      # remaining = humans

    agreements = []
    for s_idx in range(matrix.shape[1]):
        m_val = model_row[s_idx]
        if np.isnan(m_val):
            continue
        h_vals = human_rows[:, s_idx]
        h_vals = h_vals[~np.isnan(h_vals)]
        if len(h_vals) == 0:
            continue
        # majority vote
        unique, counts = np.unique(h_vals, return_counts=True)
        max_count = counts.max()
        majority_vals = unique[counts == max_count]
        agreements.append(float(m_val in majority_vals))

    if not agreements:
        return np.nan
    return float(np.mean(agreements))


METRIC_FN = {
    "krippendorff": metric_krippendorff,
    "fleiss":        metric_fleiss,
    "majority":      metric_majority,
}

# ---------------------------------------------------------------------------
# Bootstrapping
# ---------------------------------------------------------------------------


def bootstrap_metric(
    samples: list[str],
    rater_dfs: dict[str, pd.DataFrame],
    columns: list[str],
    metric: str,
    n_boot: int,
    ci: float,
    rng: np.random.Generator,
) -> tuple[float | str, float | str, float | str]:
    """
    Returns (mean, ci_low, ci_high) or (CONST_SENTINEL, ...) for constant cols.
    Empty string signals a genuine computation failure.
    """
    fn = METRIC_FN[metric]
    n  = len(samples)

    matrices = {col: build_reliability_matrix(samples, rater_dfs, col) for col in columns}

    # Check for constant columns (only meaningful for single-column calls)
    if len(columns) == 1:
        mat = next(iter(matrices.values()))
        if is_constant(mat):
            return CONST_SENTINEL, CONST_SENTINEL, CONST_SENTINEL

    boot_vals: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        col_vals = []
        for mat in matrices.values():
            v = fn(mat[:, idx])
            if not np.isnan(v):
                col_vals.append(v)
        if col_vals:
            boot_vals.append(float(np.mean(col_vals)))

    if not boot_vals:
        return "", "", ""

    arr  = np.array(boot_vals)
    lo_p = (1.0 - ci) / 2.0 * 100
    hi_p = (1.0 + ci) / 2.0 * 100
    return (
        round(float(np.mean(arr)),              4),
        round(float(np.percentile(arr, lo_p)), 4),
        round(float(np.percentile(arr, hi_p)), 4),
    )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def record_metric(
    row: dict,
    prefix: str,
    metric: str,
    result: tuple,
) -> None:
    mean, lo, hi = result
    row[f"{prefix}_{metric}_mean"]    = mean
    row[f"{prefix}_{metric}_ci_low"]  = lo
    row[f"{prefix}_{metric}_ci_high"] = hi


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute inter-rater reliability (model vs humans) with bootstrap CIs."
    )
    parser.add_argument("input_csv",  help="Combined input CSV")
    parser.add_argument("output_csv", help="Output CSV with results")
    parser.add_argument(
        "--metrics", nargs="+", choices=ALL_METRICS, default=["krippendorff"],
        metavar="METRIC",
        help=f"Metrics to compute (default: krippendorff). Choices: {ALL_METRICS}",
    )
    parser.add_argument("--n-boot", type=int,   default=1000, help="Bootstrap iterations (default: 1000)")
    parser.add_argument("--ci",     type=float, default=0.95, help="CI level (default: 0.95)")
    parser.add_argument("--seed",   type=int,   default=42,   help="Random seed (default: 42)")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # ------------------------------------------------------------------
    # Load & normalise
    # ------------------------------------------------------------------
    df = pd.read_csv(args.input_csv, dtype=str)
    for col in ("text", "rater", "codebook", "individual_questions"):
        df[col] = df[col].str.strip()
    df["rater"] = df["rater"].str.lower()

    ann_cols = data_columns(df)
    macros   = macro_groups(ann_cols)

    for c in ann_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # ------------------------------------------------------------------
    # Split into per-identity DataFrames
    # ------------------------------------------------------------------
    human_dfs: dict[str, pd.DataFrame] = {}
    model_dfs: dict[tuple, pd.DataFrame] = {}

    for rater_name, grp in df.groupby("rater"):
        if rater_name in HUMAN_RATERS:
            human_dfs[rater_name] = (
                grp.drop_duplicates(subset="text").set_index("text")[ann_cols]
            )
        else:
            for (cb, iq), sub in grp.groupby(["codebook", "individual_questions"]):
                model_dfs[(rater_name, cb, iq)] = (
                    sub.drop_duplicates(subset="text").set_index("text")[ann_cols]
                )

    if not human_dfs:
        sys.exit("Error: no human raters found (expected: robin, veronica, jana).")
    if not model_dfs:
        sys.exit("Error: no model raters found.")

    multi_macros = {k: v for k, v in macros.items() if len(v) > 1}

    print(f"Human raters : {sorted(human_dfs)}")
    print(f"Model combos : {len(model_dfs)}")
    print(f"Data columns : {len(ann_cols)}")
    print(f"Macro groups : {list(multi_macros)}")
    print(f"Metrics      : {args.metrics}")
    print(f"Bootstrap    : {args.n_boot} iterations, {args.ci*100:.0f}% CI")
    print()

    # ------------------------------------------------------------------
    # Compute Human-Only Baseline Agreement
    # ------------------------------------------------------------------
    print("Computing human-only agreement baseline...")
    human_sample_counts: dict[str, int] = {}
    for rdf in human_dfs.values():
        for s in rdf.index:
            human_sample_counts[s] = human_sample_counts.get(s, 0) + 1
    valid_human_samples = [s for s, cnt in human_sample_counts.items() if cnt >= 2]

    if valid_human_samples:
        human_results: dict = {}
        # Use an independent generator with the same seed so model bootstrapping is unaffected
        rng_human = np.random.default_rng(args.seed)

        for metric in args.metrics:
            if metric == "majority":
                continue  # Majority metric requires a reference model, skip for human-only calculation

            human_results[metric] = {}

            # Per data column
            for col in ann_cols:
                res = bootstrap_metric(valid_human_samples, human_dfs, [col], metric, args.n_boot, args.ci, rng_human)
                human_results[metric][col] = {"mean": res[0], "ci_low": res[1], "ci_high": res[2]}

            # Per macro-category
            for macro, cols in macros.items():
                if len(cols) < 2:
                    continue
                res = bootstrap_metric(valid_human_samples, human_dfs, cols, metric, args.n_boot, args.ci, rng_human)
                human_results[metric][macro] = {"mean": res[0], "ci_low": res[1], "ci_high": res[2]}

            # Overall
            res = bootstrap_metric(valid_human_samples, human_dfs, ann_cols, metric, args.n_boot, args.ci, rng_human)
            human_results[metric]["overall"] = {"mean": res[0], "ci_low": res[1], "ci_high": res[2]}

        print("\n" + "=" * 70)
        print("HUMAN-ONLY AGREEMENT CONSTANT")
        print("=" * 70)
        print("HUMAN_AGREEMENT = " + pprint.pformat(human_results, compact=False, sort_dicts=False))
        print("=" * 70 + "\n")
    else:
        print("WARNING: No overlapping samples among humans to compute standalone baseline.\n")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    rows = []

    for m_idx, (model_key, model_df) in enumerate(model_dfs.items(), 1):
        rater_name, codebook, iq = model_key
        print(f"[{m_idx}/{len(model_dfs)}] rater={rater_name}  codebook={codebook}  iq={iq}")

        # Model goes FIRST so majority metric can rely on row-0 = model
        pool: dict[str, pd.DataFrame] = {"__model__": model_df, **human_dfs}

        sample_counts: dict[str, int] = {}
        for rdf in pool.values():
            for s in rdf.index:
                sample_counts[s] = sample_counts.get(s, 0) + 1
        valid_samples = [s for s, cnt in sample_counts.items() if cnt >= 2]

        if not valid_samples:
            print("  WARNING: no overlapping samples — skipping.")
            continue

        row: dict = {"rater": rater_name, "codebook": codebook, "individual_questions": iq}

        for metric in args.metrics:
            # Per data column
            for col in ann_cols:
                result = bootstrap_metric(valid_samples, pool, [col], metric, args.n_boot, args.ci, rng)
                record_metric(row, col, metric, result)

            # Per macro-category
            for macro, cols in macros.items():
                if len(cols) < 2:
                    continue
                result = bootstrap_metric(valid_samples, pool, cols, metric, args.n_boot, args.ci, rng)
                record_metric(row, macro, metric, result)

            # Overall
            result = bootstrap_metric(valid_samples, pool, ann_cols, metric, args.n_boot, args.ci, rng)
            record_metric(row, "overall", metric, result)

        rows.append(row)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.output_csv, index=False)
    print(f"\nSaved → {args.output_csv}  ({len(out_df)} rows)")


if __name__ == "__main__":
    main()