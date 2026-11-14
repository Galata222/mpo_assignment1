"""Instances taken from the paper's worked examples, plus a brute-force optimum."""
import itertools

import pytest

from cosp.instance import Instance
from cosp.objective import Evaluator


@pytest.fixture
def example_instance() -> Instance:
    """Table 3 of the paper: 2 orders, 3 jobs per order, 2 machines."""
    p = ((2, 3), (5, 3), (6, 2),  # order 1: jobs (1,1), (1,2), (1,3)
         (3, 4), (3, 3), (4, 2))  # order 2: jobs (2,1), (2,2), (2,3)
    return Instance("paper-table3", 2, 3, 2, p)


@pytest.fixture
def counter_example_instance() -> Instance:
    """Table 4 of the paper: 2 orders, 2 jobs per order, 2 machines."""
    p = ((10, 11), (7, 2),  # order 1: jobs (1,1), (1,2)
         (11, 17), (1, 17))  # order 2: jobs (2,1), (2,2)
    return Instance("paper-table4", 2, 2, 2, p)


def job(inst: Instance, order: int, index: int) -> int:
    """Job number of the paper's job (order, index), both counted from 1."""
    return (order - 1) * inst.o + (index - 1)


def brute_force_optimum(inst: Instance) -> int:
    ev = Evaluator(inst)
    return min(ev.total(perm) for perm in itertools.permutations(range(inst.num_jobs)))
