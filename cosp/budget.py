"""Computational budget shared by all algorithms, and the result of one run."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .objective import Evaluator


class Budget:
    """Stops a run after a time limit and/or a number of schedule evaluations.

    max_full_evals is counted in equivalents of one complete schedule evaluation
    (see Evaluator.full_evals), which makes it independent of the machine and of
    how many runs execute in parallel. The clock starts when the Budget is
    created, i.e. before the initial solution is built.
    """

    def __init__(self, evaluator: Evaluator, time_limit: float | None = None,
                 max_full_evals: float | None = None) -> None:
        if time_limit is None and max_full_evals is None:
            raise ValueError("give a time limit, an evaluation limit, or both")
        self._ev = evaluator
        self.time_limit = time_limit
        self.max_full_evals = max_full_evals
        self._max_steps = None if max_full_evals is None else max_full_evals * evaluator.inst.num_jobs
        self._start = time.perf_counter()

    def elapsed(self) -> float:
        return time.perf_counter() - self._start

    def fraction(self) -> float:
        """Share of the budget used so far; the run must stop once it reaches 1."""
        used = 0.0
        if self._max_steps is not None:
            used = self._ev.job_steps / self._max_steps
        if self.time_limit is not None:
            used = max(used, (time.perf_counter() - self._start) / self.time_limit)
        return used

    def exhausted(self) -> bool:
        return self.fraction() >= 1.0


@dataclass
class RunResult:
    perm: list[int]  # best schedule found
    f_best: int
    f_init: int  # objective value of the initial solution
    iterations: int
    full_evals: float
    elapsed: float
    # (full_evals, elapsed seconds, best objective) at the start and at every improvement
    trace: list[tuple[float, float, int]] = field(default_factory=list)
