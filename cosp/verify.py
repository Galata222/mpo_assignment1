"""Independent check of a schedule, written separately from Evaluator on purpose.

Builds explicit start and end times for every job on every machine and derives
the objective from the definition C_i = max over the jobs of order i of their
completion time on the last machine. The experiment runner applies it to the
result of every run.
"""
from __future__ import annotations

from collections.abc import Sequence

from .instance import Instance


def verify_schedule(inst: Instance, perm: Sequence[int]) -> int:
    """Return the total order completion time of perm; raise if perm is not a full permutation."""
    if sorted(perm) != list(range(inst.num_jobs)):
        raise ValueError("schedule is not a permutation of all jobs")

    end: dict[tuple[int, int], int] = {}
    for position, job in enumerate(perm):
        for machine in range(inst.m):
            machine_free = end[(perm[position - 1], machine)] if position > 0 else 0
            job_arrives = end[(job, machine - 1)] if machine > 0 else 0
            end[(job, machine)] = max(machine_free, job_arrives) + inst.p[job][machine]

    last = inst.m - 1
    return sum(max(end[(job, last)] for job in inst.jobs_of_order(order)) for order in range(inst.n))
