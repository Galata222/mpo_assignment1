"""Run the experiment described by a YAML config file.

Usage (from the project root):  python -m cosp.run_experiment --config configs/smoke.yaml

Writes runs.csv (one row per run), solutions.csv (best schedule of each run)
and traces.csv (best value over the run) to the config's output_dir. Runs
already present in runs.csv are skipped, so an interrupted experiment
continues where it stopped.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import itertools
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import yaml

from .budget import Budget
from .iga_string import iga_string
from .instance import instance_path, load_instance
from .objective import Evaluator
from .sa import simulated_annealing
from .verify import verify_schedule

ALGORITHMS = {"sa": simulated_annealing, "iga_string": iga_string}

RUN_FIELDS = ["label", "algorithm", "params", "instance", "n", "o", "m", "instance_id", "seed",
              "best_known", "f_init", "f_best", "iterations", "full_evals", "time_s",
              "time_limit_s", "time_factor", "max_full_evals"]
SOLUTION_FIELDS = ["label", "instance", "seed", "f_best", "schedule"]  # job = order * o + index, 0-based
TRACE_FIELDS = ["label", "instance", "seed", "full_evals", "time_s", "f_best"]
TRACE_POINTS = 200  # at most this many trace rows are stored per run


def _variants(label: str, spec: dict) -> list[tuple[str, str, dict]]:
    """Variants of one `algorithms` entry; a `grid` yields one variant per combination."""
    if spec["type"] not in ALGORITHMS:
        raise ValueError(f"{label}: unknown algorithm type {spec['type']!r}, use one of {sorted(ALGORITHMS)}")
    base = dict(spec.get("params") or {})
    grid = spec.get("grid") or {}
    if not grid:
        return [(label, spec["type"], base)]
    variants = []
    for combo in itertools.product(*grid.values()):
        chosen = dict(zip(grid.keys(), combo))
        name = ", ".join(f"{key}={value}" for key, value in chosen.items())
        variants.append((f"{label}[{name}]", spec["type"], {**base, **chosen}))
    return variants


def expand_algorithms(config: dict) -> list[tuple[str, str, dict]]:
    """Return (label, algorithm type, parameters) for every variant in the config."""
    return [variant for label, spec in config["algorithms"].items() for variant in _variants(label, spec)]


def budgeted_algorithms(config: dict) -> list[tuple[str, str, dict, float | None, float | None]]:
    """Return (label, type, parameters, time_factor, max_full_evals) for every variant.

    An algorithm entry may carry its own `budget`, which then replaces the
    experiment-wide `budget` for that entry.
    """
    default = config.get("budget") or {}
    result = []
    for label, spec in config["algorithms"].items():
        budget = spec.get("budget") or default
        time_factor, max_full_evals = budget.get("time_factor"), budget.get("max_full_evals")
        if time_factor is None and max_full_evals is None:
            raise ValueError(f"{label}: budget needs time_factor, max_full_evals, or both")
        result += [(*variant, time_factor, max_full_evals) for variant in _variants(label, spec)]
    return result


def build_tasks(config: dict) -> list[dict]:
    spec = config["instances"]
    algorithms = budgeted_algorithms(config)

    if not Path(spec["dir"]).is_dir():
        raise FileNotFoundError(
            f"instance folder {spec['dir']} not found. Download the data set with:  python scripts/fetch_instances.py")
    paths = [instance_path(spec["dir"], n, o, m, i)
             for group in spec["groups"]
             for n, o, m, i in itertools.product(group["n"], group["o"], group["m"], spec["ids"])]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} instance files not found (first: {missing[0]}). The data set has "
            "n in 3, 4, 5 with o in 2, 3, 4 and n in 10, 20, 50 with o in 2, 5, 10; m in 2, 3, 6; ids 0-29.")

    tasks = []
    for path in paths:
        for label, kind, params, time_factor, max_full_evals in algorithms:
            for seed in config["seeds"]:
                tasks.append({"path": str(path), "instance": path.stem, "label": label, "algorithm": kind,
                              "params": params, "seed": seed, "time_factor": time_factor,
                              "max_full_evals": max_full_evals})
    return tasks


def time_limit_of(n: int, o: int, m: int, time_factor: float | None) -> float | None:
    """Time limit of the paper (Sec. 5.1): n * o * m / 2 * t seconds, with t = 0.12 there."""
    return None if time_factor is None else n * o * m / 2 * time_factor


def thin_trace(trace: list[tuple[float, float, int]], time_limit: float | None,
               max_full_evals: float | None) -> list[tuple[float, float, int]]:
    """Keep the last improvement in each of TRACE_POINTS equal slices of the budget."""
    kept: dict[int, tuple[float, float, int]] = {}
    for point in trace:
        used = point[1] / time_limit if time_limit is not None else point[0] / max_full_evals
        kept[min(int(used * TRACE_POINTS), TRACE_POINTS)] = point
    return [kept[key] for key in sorted(kept)]


def run_single(task: dict) -> tuple[dict, list[dict]]:
    inst = load_instance(task["path"])
    ev = Evaluator(inst)
    time_limit = time_limit_of(inst.n, inst.o, inst.m, task["time_factor"])
    budget = Budget(ev, time_limit, task["max_full_evals"])
    result = ALGORITHMS[task["algorithm"]](ev, budget, random.Random(task["seed"]), **task["params"])
    if verify_schedule(inst, result.perm) != result.f_best:
        raise RuntimeError(f"{task['label']} on {inst.name}, seed {task['seed']}: reported objective "
                           f"{result.f_best} does not match the independent check")

    row = {
        "label": task["label"], "algorithm": task["algorithm"],
        "params": json.dumps(task["params"], sort_keys=True),
        "instance": inst.name, "n": inst.n, "o": inst.o, "m": inst.m, "instance_id": inst.instance_id,
        "seed": task["seed"], "best_known": inst.best_known, "f_init": result.f_init,
        "f_best": result.f_best, "iterations": result.iterations,
        "full_evals": round(result.full_evals, 2), "time_s": round(result.elapsed, 4),
        "time_limit_s": time_limit, "time_factor": task["time_factor"],
        "max_full_evals": task["max_full_evals"],
        "schedule": " ".join(str(job) for job in result.perm),
    }
    trace = [{"label": task["label"], "instance": inst.name, "seed": task["seed"],
              "full_evals": round(evals, 2), "time_s": round(elapsed, 4), "f_best": f}
             for evals, elapsed, f in thin_trace(result.trace, time_limit, task["max_full_evals"])]
    return row, trace


def _settings(row: dict) -> tuple:
    """What must stay the same for all runs stored under one label."""
    def number(value):
        return None if value in ("", None) else float(value)
    params = row["params"] if isinstance(row["params"], str) else json.dumps(row["params"], sort_keys=True)
    return row["algorithm"], params, number(row["time_factor"]), number(row["max_full_evals"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--workers", type=int, help="parallel runs (overrides the config)")
    parser.add_argument("--dry-run", action="store_true", help="show the plan and the time estimate, run nothing")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    workers = args.workers or config.get("workers", 1)
    out_dir = Path(config["output_dir"])
    runs_path, solutions_path, traces_path = (out_dir / name for name in ("runs.csv", "solutions.csv", "traces.csv"))

    tasks = build_tasks(config)

    done: set[tuple[str, str, str]] = set()
    stored_settings: dict[str, tuple] = {}
    if runs_path.exists():
        with runs_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                done.add((row["label"], row["instance"], row["seed"]))
                stored_settings.setdefault(row["label"], _settings(row))
    for task in tasks:
        if task["label"] in stored_settings and _settings(task) != stored_settings[task["label"]]:
            print(f"error: {runs_path} already holds runs of '{task['label']}' with different parameters or "
                  "budget. Use another output_dir or another label.", file=sys.stderr)
            return 1
    todo = [t for t in tasks if (t["label"], t["instance"], str(t["seed"])) not in done]

    print(f"{len(tasks)} runs planned, {len(tasks) - len(todo)} already done, {len(todo)} to run, {workers} worker(s)")
    timed = [task for task in todo if task["time_factor"] is not None]
    if timed:
        total = 0.0
        for task in timed:
            n, o, m = (int(x) for x in task["instance"].split("-")[1:4])
            total += time_limit_of(n, o, m, task["time_factor"])
        print(f"time limits add up to {total / 3600:.2f} h, about {total / 3600 / workers:.2f} h with {workers} worker(s)")
        if workers > max(1, (os.cpu_count() or 2) // 2):
            print(f"note: {workers} workers on {os.cpu_count()} logical CPUs. Runs that share a physical core "
                  "slow each other down, so each gets less work done within its time limit.")
    if not todo or args.dry_run:
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    config["workers"] = workers  # record the value actually used
    (out_dir / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    outputs = [(runs_path, RUN_FIELDS), (solutions_path, SOLUTION_FIELDS), (traces_path, TRACE_FIELDS)]
    with contextlib.ExitStack() as stack:
        files, writers = [], []
        for path, fields in outputs:
            is_new = not path.exists()
            handle = stack.enter_context(path.open("a", newline="", encoding="utf-8"))
            writer = csv.DictWriter(handle, fields, extrasaction="ignore")
            if is_new:
                writer.writeheader()
            files.append(handle)
            writers.append(writer)
        runs_writer, solutions_writer, traces_writer = writers

        def store(count: int, row: dict, trace: list[dict]) -> None:
            runs_writer.writerow(row)  # each writer picks its own columns from the row
            solutions_writer.writerow(row)
            traces_writer.writerows(trace)
            for handle in files:
                handle.flush()
            gap = ""
            if row["best_known"]:
                gap = f"  gap to best known {100 * (row['f_best'] - row['best_known']) / row['best_known']:+.3f}%"
            print(f"[{count}/{len(todo)}] {row['label']}  {row['instance']}  seed {row['seed']}  "
                  f"F={row['f_best']}{gap}  {row['time_s']:.1f}s", flush=True)

        if workers <= 1:
            for count, task in enumerate(todo, 1):
                store(count, *run_single(task))
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(run_single, task) for task in todo]
                for count, future in enumerate(as_completed(futures), 1):
                    store(count, *future.result())

    print(f"results written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
