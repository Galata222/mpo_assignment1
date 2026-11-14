"""MultipleNEH initial solution (Algorithm 1 of the paper)."""
from __future__ import annotations

from collections.abc import Callable

from .objective import Evaluator


def insert_at_best(seq: list, item, cost: Callable[[list], float]) -> float:
    """Insert item into seq (in place) at the position with the lowest cost.

    Positions are tried from the last to the first, as in the paper's loops, and
    the first minimum found is kept. This tie rule reproduces the example
    schedule of the paper (Sec. 4, F = 37). Returns the cost after insertion.
    """
    best_cost = None
    best_pos = 0
    for pos in range(len(seq), -1, -1):
        seq.insert(pos, item)
        value = cost(seq)
        if best_cost is None or value < best_cost:
            best_cost, best_pos = value, pos
        del seq[pos]
    seq.insert(best_pos, item)
    return best_cost


def multiple_neh(ev: Evaluator) -> tuple[list[int], list[int], list[list[int]]]:
    """Return (schedule, order sequence, job sequence of each order).

    Part 1: NEH on the jobs of each order separately (jobs sorted by ascending
    total processing time, each inserted where the makespan of the order's own
    job sequence is lowest).
    Part 2: NEH on whole orders (sorted by ascending makespan of their job
    sequence, each inserted where the total completion time of the partial
    schedule is lowest). Jobs of an order stay consecutive.
    """
    inst = ev.inst
    job_seqs: list[list[int]] = []
    for order in range(inst.n):
        seq: list[int] = []
        for job in sorted(inst.jobs_of_order(order), key=lambda j: inst.total_time[j]):
            insert_at_best(seq, job, ev.makespan)
        job_seqs.append(seq)

    order_makespan = [ev.makespan(seq) for seq in job_seqs]

    def schedule_cost(orders: list[int]) -> int:
        return ev.total([job for order in orders for job in job_seqs[order]])

    order_seq: list[int] = []
    for order in sorted(range(inst.n), key=lambda i: order_makespan[i]):
        insert_at_best(order_seq, order, schedule_cost)

    perm = [job for order in order_seq for job in job_seqs[order]]
    return perm, order_seq, job_seqs
