"""Simulated annealing on the flat job permutation (own method, Variant B).

Differences from the paper's IGAs: one cheap random move per step instead of
destruction/construction, and a temperature that cools with the share of the
budget used instead of a fixed acceptance scale.
"""
from __future__ import annotations

import math
import random

from .budget import Budget, RunResult
from .neh import multiple_neh
from .objective import Evaluator


def _apply_move(perm: list[int], rng: random.Random, p_insert: float, p_swap: float,
                order_of: tuple[int, ...], n_orders: int) -> tuple:
    """Change perm in place by one random move and return what is needed to undo it."""
    size = len(perm)
    r = rng.random()
    if r < p_insert + p_swap:
        i = rng.randrange(size)
        j = rng.randrange(size - 1)
        if j >= i:
            j += 1  # two distinct positions
        if r < p_insert:  # job insertion: take the job at i, put it at j
            perm.insert(j, perm.pop(i))
            return ("insert", i, j)
        perm[i], perm[j] = perm[j], perm[i]  # job swap
        return ("swap", i, j)
    # order block: gather all jobs of one order and reinsert them as one block
    order = rng.randrange(n_orders)
    before = perm[:]
    block = [job for job in perm if order_of[job] == order]
    rest = [job for job in perm if order_of[job] != order]
    pos = rng.randrange(len(rest) + 1)
    perm[:] = rest[:pos] + block + rest[pos:]
    return ("block", before)


def _undo_move(perm: list[int], move: tuple) -> None:
    if move[0] == "insert":
        perm.insert(move[1], perm.pop(move[2]))
    elif move[0] == "swap":
        perm[move[1]], perm[move[2]] = perm[move[2]], perm[move[1]]
    else:
        perm[:] = move[1]


def simulated_annealing(ev: Evaluator, budget: Budget, rng: random.Random, *,
                        init: str = "neh", p0: float = 0.3, t_ratio: float = 1e-3,
                        p_insert: float = 0.6, p_swap: float = 0.3,
                        calibration_samples: int = 200) -> RunResult:
    """Minimise the total order completion time.

    init                 "neh" (MultipleNEH, as the paper's IGAs) or "random"
    p0                   probability of accepting an average worsening move at the start
    t_ratio              final temperature / initial temperature
    p_insert, p_swap     probabilities of the insertion and swap moves; the rest
                         (1 - p_insert - p_swap) goes to the order-block move
    calibration_samples  random moves sampled to set the initial temperature
    """
    if init not in ("neh", "random"):
        raise ValueError(f"unknown init {init!r}")
    if not 0.0 < p0 < 1.0:
        raise ValueError("p0 must be in (0, 1)")
    if not 0.0 < t_ratio <= 1.0:
        raise ValueError("t_ratio must be in (0, 1]")
    if p_insert < 0 or p_swap < 0 or p_insert + p_swap > 1.0 + 1e-12:
        raise ValueError("p_insert and p_swap must be >= 0 and sum to at most 1")

    inst = ev.inst
    order_of, n_orders = inst.order_of, inst.n

    if init == "neh":
        cur, _, _ = multiple_neh(ev)
    else:
        cur = list(range(inst.num_jobs))
        rng.shuffle(cur)
    f_cur = ev.total(cur)
    f_init = f_cur
    best, f_best = cur[:], f_cur
    trace = [(ev.full_evals, budget.elapsed(), f_best)]
    if inst.num_jobs < 2:
        return RunResult(best, f_best, f_init, 0, ev.full_evals, budget.elapsed(), trace)

    # Initial temperature: an average worsening move is accepted with probability p0.
    worsening = []
    for _ in range(calibration_samples):
        move = _apply_move(cur, rng, p_insert, p_swap, order_of, n_orders)
        delta = ev.total(cur) - f_cur
        _undo_move(cur, move)
        if delta > 0:
            worsening.append(delta)
    t_start = -(sum(worsening) / len(worsening)) / math.log(p0) if worsening else 1.0

    iterations = 0
    while True:
        used = budget.fraction()
        if used >= 1.0:
            break
        temperature = t_start * t_ratio ** used  # geometric cooling over the budget
        move = _apply_move(cur, rng, p_insert, p_swap, order_of, n_orders)
        f_new = ev.total(cur)
        delta = f_new - f_cur
        if delta <= 0 or rng.random() < math.exp(-delta / temperature):
            f_cur = f_new
            if f_cur < f_best:
                best, f_best = cur[:], f_cur
                trace.append((ev.full_evals, budget.elapsed(), f_best))
        else:
            _undo_move(cur, move)
        iterations += 1

    return RunResult(best, f_best, f_init, iterations, ev.full_evals, budget.elapsed(), trace)
