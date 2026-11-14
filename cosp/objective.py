"""Objective function with evaluation accounting.

Every algorithm evaluates schedules only through an Evaluator, so the work done
by different algorithms is counted in the same unit.
"""
from __future__ import annotations

from collections.abc import Sequence

from .instance import Instance


class Evaluator:
    def __init__(self, inst: Instance) -> None:
        self.inst = inst
        self._p = inst.p
        self._order_of = inst.order_of
        self._n = inst.n
        self._m = inst.m
        self.job_steps = 0  # jobs pushed through the flow shop over all evaluations

    @property
    def full_evals(self) -> float:
        """Work done so far, in equivalents of evaluating one complete schedule."""
        return self.job_steps / self.inst.num_jobs

    def total(self, seq: Sequence[int]) -> int:
        """Total order completion time F of a (possibly partial) job sequence.

        Completion times on the last machine increase along the sequence, so the
        value written last for an order is the completion time of that order.
        Orders with no job in seq contribute 0.
        """
        p = self._p
        order_of = self._order_of
        m = self._m
        c = [0] * m  # completion time of the latest job on each machine
        c_order = [0] * self._n
        for job in seq:
            pj = p[job]
            c[0] += pj[0]
            for k in range(1, m):
                if c[k - 1] > c[k]:
                    c[k] = c[k - 1]
                c[k] += pj[k]
            c_order[order_of[job]] = c[m - 1]
        self.job_steps += len(seq)
        return sum(c_order)

    def makespan(self, seq: Sequence[int]) -> int:
        """Completion time of the last job of seq on the last machine."""
        p = self._p
        m = self._m
        c = [0] * m
        for job in seq:
            pj = p[job]
            c[0] += pj[0]
            for k in range(1, m):
                if c[k - 1] > c[k]:
                    c[k] = c[k - 1]
                c[k] += pj[k]
        self.job_steps += len(seq)
        return c[m - 1]
