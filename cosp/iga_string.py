"""IGA-String baseline, re-implemented from the paper's pseudocode (Algorithms 2-6).

Deviation from the pseudocode: the budget is also checked between single job
insertions, not only between iterations. One iteration can cost a large share
of the whole budget on big instances, so checking only between iterations
would let the baseline run well past its limit.
"""
from __future__ import annotations

import math
import random

from .budget import Budget, RunResult
from .neh import insert_at_best, multiple_neh
from .objective import Evaluator


def _multiple_insertion(ev: Evaluator, budget: Budget, rng: random.Random,
                        perm: list[int], count: int) -> int:
    """Local search (Algorithm 3): move `count` random jobs to their best position.

    Changes perm in place and returns its objective value. Stops early when the
    budget runs out; perm is a complete schedule at every point.
    """
    f = None
    for job in rng.sample(perm, min(count, len(perm))):
        if budget.exhausted():
            break
        perm.remove(job)
        f = insert_at_best(perm, job, ev.total)
    return ev.total(perm) if f is None else f


def _construction(ev: Evaluator, budget: Budget, partial: list[int], removed: list[int]) -> bool:
    """Algorithm 5: reinsert the removed jobs, shortest total processing time first.

    Returns False if the budget ran out before the schedule was complete.
    """
    for job in sorted(removed, key=lambda j: ev.inst.total_time[j]):
        if budget.exhausted():
            return False
        insert_at_best(partial, job, ev.total)
    return True


def iga_string(ev: Evaluator, budget: Budget, rng: random.Random, *,
               gamma: float = 20000.0, z: float = 2.0,
               d_min: int = 1, d_max: int | None = None) -> RunResult:
    """Iterated greedy on the sequence of all jobs.

    gamma, z   acceptance and local-search parameters (paper, Table 8: 20000 and 2)
    d_min      smallest destruction size (paper: 1)
    d_max      largest destruction size (paper: floor(n*o/2), used when None)
    """
    inst = ev.inst
    if d_max is None:
        d_max = max(d_min, inst.num_jobs // 2)

    cur, _, _ = multiple_neh(ev)
    f_init = ev.total(cur)
    d = d_min
    f_cur = _multiple_insertion(ev, budget, rng, cur, int(z * d / d_min))
    best, f_best = cur[:], f_cur
    trace = [(ev.full_evals, budget.elapsed(), f_best)]

    iterations = 0
    while not budget.exhausted():
        cand = cur[:]
        removed = rng.sample(cand, d)  # destruction (Algorithm 4)
        for job in removed:
            cand.remove(job)
        if not _construction(ev, budget, cand, removed):
            break
        f_cand = _multiple_insertion(ev, budget, rng, cand, int(z * d / d_min))
        iterations += 1

        # acceptance (Algorithm 6)
        if f_cand < f_cur:
            cur, f_cur, d = cand, f_cand, d_min
            if f_cand < f_best:
                best, f_best = cand[:], f_cand
                trace.append((ev.full_evals, budget.elapsed(), f_best))
        else:
            if f_cand == f_cur:
                cur = cand
            elif rng.random() <= math.exp(-gamma * (d_min / d) * (f_cand - f_cur) / f_cur):
                cur, f_cur = cand, f_cand
            if d < d_max:
                d += 1

    return RunResult(best, f_best, f_init, iterations, ev.full_evals, budget.elapsed(), trace)
