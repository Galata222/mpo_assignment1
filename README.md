# Customer order scheduling in a permutation flow shop: simulated annealing vs. IGA-String

Code for Assignment 1 (Variant B, own solution method). The optimisation problem and the
baseline come from:

> J. Hoffmann, J. S. Neufeld, U. Buscher: *Customer order scheduling in a permutation flow
> shop environment*. Operations Research Perspectives 15 (2025) 100362.
> https://doi.org/10.1016/j.orp.2025.100362

**Problem.** `n` customer orders with `o` jobs each are processed on `m` machines. All jobs
visit the machines in the same sequence and in the same job order (permutation flow shop).
An order is complete when its last job leaves the last machine. The goal is a job sequence
that minimises the sum of the order completion times. Every permutation of the `n*o` jobs
is a feasible solution.

**What is compared.**

- `SA`: simulated annealing on the job permutation (our method, `cosp/sa.py`).
- `IGA-String`: the first of the paper's four iterated greedy algorithms, re-implemented
  from its pseudocode (`cosp/iga_string.py`), run on the same objective function, instances
  and budget.
- The RPD values published in the paper for all four IGAs (`reference/paper_rpd.csv`).

## Setup

Developed and tested with Python 3.12.10 on Windows.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/fetch_instances.py     # downloads the authors' instances into data/
python -m pytest                      # 43 tests, a few seconds
```

Run all commands from the project root.

## Running experiments

```powershell
python -m cosp.run_experiment --config configs/smoke.yaml            # run
python -m cosp.run_experiment --config configs/big.yaml --dry-run    # only show the plan
python -m cosp.analyze results/smoke                                 # tables and plots
```

| Config | Purpose | Budget per run | Runs | Time |
|---|---|---|---|---|
| `configs/smoke.yaml` | check that everything works | paper's time limit | 32 | 2 min, one worker |
| `configs/tuning_sa.yaml` | choose SA parameters on the tuning instances (ids 0-4 of three sizes) | paper's time limit | 405 | 20 min, 4 workers |
| `configs/small.yaml` | Small testbed, 20 instances per size | 190 000 evaluations | 5400 | 1 h, 4 workers |
| `configs/big.yaml` | Big testbed, 5 instances per size | 190 000 evaluations | 1350 | 2.4 h, 4 workers |
| `configs/extra_ablation_init.yaml` | SA from NEH vs random start | 190 000 evaluations | 250 | 42 min, 4 workers |
| `configs/extra_long_budget.yaml` | 500-job instances at 4× budget | 760 000 evaluations | 150 | 4.3 h, 4 workers |

`--workers N` runs N runs in parallel. An interrupted experiment continues where it stopped
when the same command is started again. The runner refuses to add runs to an output folder
that already holds runs of the same label with other parameters or another budget.

### Budget

Both algorithms get the same budget per run, set in the config:

- `time_factor`: time limit in seconds = `n * o * m / 2 * time_factor`. The paper uses 0.12
  (0.72 s for the smallest, 180 s for the largest instances).
- `max_full_evals`: limit on the work done, counted in evaluations of one complete schedule.
  Evaluating a partial sequence of `k` jobs counts as `k / (n*o)` evaluations.

A time limit depends on the computer and on what else is running, so two runs with the same
seed can give different results. With `max_full_evals` alone, the same seed always gives the
same result, also with several workers. If both are given, the run stops at whichever is
reached first.

The main experiments (`small.yaml`, `big.yaml`) use 190 000 evaluations per run for every
problem size. On the development laptop (Intel Core i7-9750H) the paper's time limit bought
about that many evaluations per run when four runs ran in parallel, and roughly twice as many
for a run on its own; under other load it was half. The parameter setting was run with the
time limit before this was known: the laptop went to sleep during it, and the affected runs
had to be repeated (kept in `results/tuning_sa/*_backup/`).

## Output files

In the config's `output_dir`:

| File | Content |
|---|---|
| `runs.csv` | one row per run: algorithm, parameters, instance, seed, initial and best objective value, evaluations, time |
| `solutions.csv` | the best schedule of every run (job number = `order * o + index`, counted from 0) |
| `traces.csv` | best value over the course of each run (for convergence plots) |
| `config.yaml` | the configuration that was used |
| `analysis/summary.csv` | per algorithm: mean, median, standard deviation, minimum and maximum RPD, share of runs that reached the best known value |
| `analysis/rpd_by_size.csv` | mean RPD per problem size, next to the values published in the paper |
| `analysis/wilcoxon.csv` | one-sided Wilcoxon signed-rank tests (alpha = 0.05) on per-instance mean RPD |
| `analysis/new_best_known.csv` | instances where a run beat the value in the authors' file |
| `analysis/*.png` | RPD box plot, RPD by number of orders / jobs / machines, convergence |

RPD is the relative percentage deviation from the best known solution (Eq. 9 of the paper).
The best known value of an instance is the lower of the value in the authors' file and the
best value of any run in the experiment being analysed. When a run beats the authors' value,
the reference changes, and RPDs are then not directly comparable with the published ones.

## Algorithms and parameters

**SA** (`type: sa`)

| Parameter | Default | Meaning |
|---|---|---|
| `init` | `neh` | start from MultipleNEH (as the IGAs do) or from a `random` permutation |
| `p0` | 0.3 | probability of accepting an average worsening move at the start; sets the initial temperature from 200 sampled moves |
| `t_ratio` | 0.001 | final temperature divided by initial temperature |
| `p_insert` | 0.6 | probability of the move "take one job out and insert it elsewhere" |
| `p_swap` | 0.3 | probability of the move "swap two jobs" |
| (rest) | 0.1 | move "collect all jobs of one order and reinsert them as one block" |

The temperature falls geometrically with the share of the budget used:
`T = T0 * t_ratio ^ (budget used)`. In the parameter setting (`configs/tuning_sa.yaml`, 9
combinations of `p0` and `t_ratio`) the defaults had the lowest mean RPD, without a
significant difference to three other combinations.

**IGA-String** (`type: iga_string`): `gamma: 20000` and `z: 2` (paper, Table 8), `d_min: 1`,
`d_max: floor(n*o/2)`.

## Relation to the paper

Taken from the paper: the problem, MultipleNEH (Algorithm 1), IGA-String (Algorithms 2-6),
the time limit formula, five runs per instance, RPD, the Wilcoxon test, the instances
(ids 0-9 for parameter setting, ids 10-29 for the comparison).

Choices where the paper leaves room, and deviations:

- The main experiments stop after 190 000 schedule evaluations per run instead of a time
  limit (see "Budget"). IGA-String needs less computing time per counted evaluation than SA,
  so compared with an equal time limit this gives SA more computing time: on the Small
  testbed an SA run took 2.99 s on average and an IGA-String run 2.45 s (Big testbed:
  26.0 s and 25.0 s).
- The Big testbed uses 5 of the 20 comparison instances per size (ids 10-14).
- SA parameters were set on 5 tuning instances of three sizes, not on all sizes.
- Two follow-up experiments (`extra_ablation_init.yaml`, `extra_long_budget.yaml`)
  test the random start and a longer budget on the 500-job instances.
- Ties between equally good insertion positions go to the position tried first, scanning
  from the last position to the first. This reproduces the paper's example schedule
  (F = 37), which a test checks.
- IGA-String checks the budget between single job insertions as well, not only between
  iterations. On large instances one iteration can take a large part of the whole budget.
- The clock starts before the initial solution is built, for both algorithms.
- IGA-Matrix1-3 and the MINLP model are not implemented. Their published results are in
  `reference/paper_rpd.csv`, transcribed from Tables 9 and 10; a test checks the column
  means against the totals printed in the paper.
- Our runs use another computer and Python version than the authors (Xeon E5-2630 v2,
  Python 3.10.9), so the same time limit does not mean the same amount of computation.

## Correctness checks

- The objective function returns the values printed in the paper (Fig. 3, Table 5, and the
  optimum 79 of the counter example).
- On all 90 instances with 3 orders and 2 jobs per order, the optimum found by enumerating
  all schedules equals the best known value in the authors' files.
- The experiment runner recomputes the result of every run with a separately written
  function (`cosp/verify.py`) and stops if the two values differ.

## Project layout

```
cosp/                   algorithms, runner, analysis
configs/                experiment configurations
reference/              RPD values published in the paper
results/                experiment outputs and analysis tables/plots
report/                 final Word report and figures
scripts/                download of the instances; build_report.py
tests/                  unit tests
Zadanie1_Report.docx    Slovak report
Assignment1_Report_EN.docx  English report
```

Rebuild the report after changing results:

```powershell
python scripts/build_report.py
```

## Sources

- Paper authors: problem definition, MultipleNEH and IGA-String (pseudocode), published
  results, and the instances from https://github.com/Julius2627/COSP_Flow_Shop (commit
  `c3d1a47`, not included here; the repository states no licence).
- Own work: the simulated annealing method, the experiment and analysis code.
- Generative AI: the first version of this code and README was written with an AI coding
  assistant (Cursor) on 2026-11-12. Update this section so that it describes how the
  submitted version was produced.

