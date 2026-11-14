"""Summarise an experiment: RPD tables, Wilcoxon tests and plots.

Usage (from the project root):  python -m cosp.analyze results/smoke

RPD (relative percentage deviation, Eq. 9 of the paper) is measured against the
best solution known for an instance: the lower of the value in the authors'
file and the best value of any run in this experiment.
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

PAPER_REFERENCE = Path(__file__).resolve().parent.parent / "reference" / "paper_rpd.csv"
ALPHA = 0.05


def load_runs(result_dir: Path) -> pd.DataFrame:
    runs = pd.read_csv(result_dir / "runs.csv")
    own_best = runs.groupby("instance")["f_best"].min()
    published = runs.groupby("instance")["best_known"].first()
    reference = pd.concat([own_best, published], axis=1).min(axis=1)
    runs["f_ref"] = runs["instance"].map(reference)
    runs["rpd"] = 100.0 * (runs["f_best"] - runs["f_ref"]) / runs["f_ref"]
    return runs


def summary_table(runs: pd.DataFrame) -> pd.DataFrame:
    table = runs.groupby("label").agg(
        runs=("rpd", "size"),
        instances=("instance", "nunique"),
        rpd_mean=("rpd", "mean"),
        rpd_median=("rpd", "median"),
        rpd_std=("rpd", "std"),
        rpd_min=("rpd", "min"),
        rpd_max=("rpd", "max"),
        best_hit_pct=("rpd", lambda s: 100.0 * (s == 0).mean()),
        time_s_mean=("time_s", "mean"),
        full_evals_mean=("full_evals", "mean"),
    )
    return table.sort_values("rpd_mean")


def size_table(runs: pd.DataFrame) -> pd.DataFrame:
    """Mean RPD per problem size and algorithm, next to the values published in the paper."""
    table = runs.pivot_table(index=["n", "o", "m"], columns="label", values="rpd", aggfunc="mean")
    table.columns.name = None
    if PAPER_REFERENCE.exists():
        paper = pd.read_csv(PAPER_REFERENCE).drop(columns="testbed").set_index(["n", "o", "m"])
        paper.columns = [f"paper {name}" for name in paper.columns]
        table = table.join(paper, how="left")
    return table


def new_best_table(runs: pd.DataFrame) -> pd.DataFrame:
    """Instances where a run of this experiment beat the value in the authors' file."""
    better = runs[runs["f_best"] < runs["best_known"]]
    if better.empty:
        return pd.DataFrame(columns=["instance", "best_known", "new_best", "found_by"])
    rows = []
    for instance, group in better.groupby("instance"):
        new_best = group["f_best"].min()
        found_by = sorted(group.loc[group["f_best"] == new_best, "label"].unique())
        rows.append({"instance": instance, "best_known": group["best_known"].iloc[0],
                     "new_best": new_best, "found_by": "; ".join(found_by)})
    return pd.DataFrame(rows)


def instance_means(runs: pd.DataFrame) -> pd.DataFrame:
    """RPD averaged over the seeds: one row per instance, one column per algorithm."""
    return runs.groupby(["instance", "label"])["rpd"].mean().unstack("label")


def wilcoxon_table(per_instance: pd.DataFrame) -> pd.DataFrame:
    """One-sided Wilcoxon signed-rank test for every pair, as in the paper (alpha = 0.05).

    The RPDs of an instance are averaged over the seeds first. For each pair the
    test asks whether the algorithm with the lower mean RPD is significantly better.
    """
    rows = []
    for a, b in itertools.combinations(per_instance.columns, 2):
        pair = per_instance[[a, b]].dropna()
        if pair[a].mean() > pair[b].mean():
            a, b = b, a
        try:
            p_value = wilcoxon(pair[a], pair[b], alternative="less").pvalue
        except ValueError:  # all differences are zero
            p_value = float("nan")
        rows.append({"better": a, "worse": b, "instances": len(pair),
                     "rpd_mean_better": pair[a].mean(), "rpd_mean_worse": pair[b].mean(),
                     "p_value": p_value, "significant": bool(p_value < ALPHA)})
    return pd.DataFrame(rows)


def plot_boxplot(per_instance: pd.DataFrame, path: Path) -> None:
    labels = list(per_instance.columns)
    fig, ax = plt.subplots(figsize=(max(5.0, 1.2 * len(labels) + 2), 4.5))
    ax.boxplot([per_instance[label].dropna() for label in labels], showmeans=True)
    ax.set_xticks(range(1, len(labels) + 1), labels, rotation=30 if len(labels) > 3 else 0, ha="right" if len(labels) > 3 else "center")
    ax.set_ylabel("RPD in % (mean over seeds, per instance)")
    ax.set_title("Distribution of RPD over instances")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_factors(runs: pd.DataFrame, per_instance: pd.DataFrame, path: Path) -> None:
    """Mean RPD with 95% confidence interval per number of orders, jobs per order and machines."""
    sizes = runs.drop_duplicates("instance").set_index("instance")[["n", "o", "m"]]
    names = {"n": "Number of orders", "o": "Number of jobs per order", "m": "Number of machines"}
    labels = list(per_instance.columns)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, factor in zip(axes, names):
        levels = sorted(sizes[factor].unique())
        for index, label in enumerate(labels):
            values = per_instance[label].dropna()
            groups = values.groupby(sizes.loc[values.index, factor])
            mean = groups.mean().reindex(levels)
            half_width = (1.96 * groups.sem()).reindex(levels).fillna(0.0)
            offset = (index - (len(labels) - 1) / 2) * 0.12
            ax.errorbar(np.arange(len(levels)) + offset, mean, yerr=half_width, fmt="o", capsize=3, label=label)
        ax.set_xticks(range(len(levels)), levels)
        ax.set_xlim(-0.5, len(levels) - 0.5)
        ax.set_xlabel(names[factor])
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("Average RPD in %")
    axes[-1].legend(fontsize=8)
    fig.suptitle("Average RPD with 95% confidence interval")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_convergence(runs: pd.DataFrame, result_dir: Path, path: Path) -> bool:
    """Mean RPD of the best solution found so far against the share of the budget used."""
    traces_path = result_dir / "traces.csv"
    if not traces_path.exists():
        return False
    traces = pd.read_csv(traces_path)
    key = ["label", "instance", "seed"]
    info = runs.set_index(key)[["f_ref", "time_limit_s", "max_full_evals"]]
    grid = np.linspace(0.0, 1.0, 201)
    curves: dict[str, list[np.ndarray]] = {}
    for run_key, trace in traces.groupby(key):
        if run_key not in info.index:
            continue
        f_ref, time_limit, max_evals = info.loc[run_key]
        used = trace["time_s"] / time_limit if pd.notna(time_limit) else trace["full_evals"] / max_evals
        rpd = 100.0 * (trace["f_best"].to_numpy() - f_ref) / f_ref
        position = np.searchsorted(used.to_numpy(), grid, side="right") - 1
        curve = np.where(position >= 0, rpd[np.clip(position, 0, None)], np.nan)
        curves.setdefault(run_key[0], []).append(curve)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, runs_of_label in curves.items():
        # NaN (not drawn) until every run of this algorithm has its first solution
        ax.plot(grid, np.vstack(runs_of_label).mean(axis=0), label=label)
    ax.set_xlabel("Share of the budget used")
    ax.set_ylabel("Average RPD of the best solution so far in %")
    ax.set_title("Convergence (mean over all runs)")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(bottom=0.0)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("result_dir", type=Path, help="output_dir of an experiment (contains runs.csv)")
    args = parser.parse_args()

    runs = load_runs(args.result_dir)
    out = args.result_dir / "analysis"
    out.mkdir(exist_ok=True)

    summary = summary_table(runs)
    sizes = size_table(runs)
    new_best = new_best_table(runs)
    per_instance = instance_means(runs)
    tests = wilcoxon_table(per_instance)

    runs.to_csv(out / "runs_with_rpd.csv", index=False)
    summary.to_csv(out / "summary.csv")
    sizes.to_csv(out / "rpd_by_size.csv")
    new_best.to_csv(out / "new_best_known.csv", index=False)
    tests.to_csv(out / "wilcoxon.csv", index=False)
    plot_boxplot(per_instance, out / "rpd_boxplot.png")
    plot_factors(runs, per_instance, out / "rpd_by_factor.png")
    plot_convergence(runs, args.result_dir, out / "convergence.png")

    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 200)
    print("== Summary per algorithm (RPD in %) ==")
    print(summary.to_string(float_format=lambda value: f"{value:.4f}"))
    print("\n== Mean RPD in % per problem size ('paper ...' = values published in the paper) ==")
    print(sizes.to_string(float_format=lambda value: f"{value:.4f}"))
    if len(tests) <= 15:
        print("\n== One-sided Wilcoxon signed-rank tests on per-instance mean RPD ==")
        print(tests.to_string(index=False, float_format=lambda value: f"{value:.4g}"))
    print(f"\ninstances where a run beat the published best known value: {len(new_best)}")
    print(f"tables and plots written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
