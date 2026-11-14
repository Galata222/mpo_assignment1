import random

import pytest
from conftest import job

from cosp.instance import generate_instance
from cosp.objective import Evaluator
from cosp.verify import verify_schedule


def test_verifier_gives_the_paper_value(example_instance):
    inst = example_instance
    schedule = [job(inst, *x) for x in [(2, 2), (2, 1), (2, 3), (1, 1), (1, 2), (1, 3)]]
    assert verify_schedule(inst, schedule) == 37


@pytest.mark.parametrize("shape", [(3, 2, 2), (5, 4, 6), (10, 5, 3), (20, 10, 6), (4, 3, 1)])
def test_evaluator_agrees_with_the_independent_verifier(shape):
    inst = generate_instance(*shape, seed=11)
    rng = random.Random(0)
    ev = Evaluator(inst)
    for _ in range(25):
        perm = list(range(inst.num_jobs))
        rng.shuffle(perm)
        assert ev.total(perm) == verify_schedule(inst, perm)


def test_verifier_rejects_incomplete_or_repeated_jobs(example_instance):
    with pytest.raises(ValueError):
        verify_schedule(example_instance, [0, 1, 2, 3, 4])
    with pytest.raises(ValueError):
        verify_schedule(example_instance, [0, 1, 2, 3, 4, 4])
