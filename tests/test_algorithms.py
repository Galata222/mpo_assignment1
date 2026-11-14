import random

import pytest
from conftest import brute_force_optimum, job

from cosp.budget import Budget
from cosp.iga_string import iga_string
from cosp.instance import generate_instance
from cosp.neh import multiple_neh
from cosp.objective import Evaluator
from cosp.sa import simulated_annealing

ALGORITHMS = {"sa": simulated_annealing, "iga_string": iga_string}


def run(algorithm, inst, seed, max_full_evals, **params):
    ev = Evaluator(inst)
    budget = Budget(ev, max_full_evals=max_full_evals)
    return ALGORITHMS[algorithm](ev, budget, random.Random(seed), **params)


def test_multiple_neh_reproduces_the_paper_example(example_instance):
    inst = example_instance
    perm, order_seq, job_seqs = multiple_neh(Evaluator(inst))
    assert job_seqs[0] == [job(inst, 1, 1), job(inst, 1, 2), job(inst, 1, 3)]
    assert job_seqs[1] == [job(inst, 2, 2), job(inst, 2, 1), job(inst, 2, 3)]
    assert order_seq == [1, 0]  # the paper's order sequence {2, 1}
    assert Evaluator(inst).total(perm) == 37


def test_multiple_neh_keeps_orders_consecutive():
    inst = generate_instance(6, 4, 3, seed=1)
    perm, order_seq, _ = multiple_neh(Evaluator(inst))
    assert sorted(perm) == list(range(inst.num_jobs))
    orders_in_schedule = [inst.order_of[j] for j in perm]
    assert orders_in_schedule == [order for order in order_seq for _ in range(inst.o)]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_result_is_a_consistent_permutation(algorithm):
    inst = generate_instance(8, 3, 3, seed=2)
    result = run(algorithm, inst, seed=0, max_full_evals=3000)
    assert sorted(result.perm) == list(range(inst.num_jobs))
    assert Evaluator(inst).total(result.perm) == result.f_best
    assert result.f_best <= result.f_init
    assert result.trace[-1][2] == result.f_best
    assert result.iterations > 0


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_evaluation_budget_is_respected(algorithm):
    inst = generate_instance(8, 3, 3, seed=2)
    result = run(algorithm, inst, seed=0, max_full_evals=3000)
    # an insertion scan in progress is finished, so allow a small overshoot
    assert result.full_evals <= 3000 + inst.num_jobs + 2


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_same_seed_gives_same_result_under_an_evaluation_budget(algorithm):
    inst = generate_instance(6, 3, 2, seed=3)
    first = run(algorithm, inst, seed=7, max_full_evals=2000)
    second = run(algorithm, inst, seed=7, max_full_evals=2000)
    assert first.perm == second.perm
    assert first.f_best == second.f_best


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("shape", [(3, 2, 2), (4, 2, 3)])
def test_tiny_instances_are_solved_to_optimality(algorithm, shape):
    for instance_seed in range(3):
        inst = generate_instance(*shape, seed=100 + instance_seed)
        optimum = brute_force_optimum(inst)
        result = run(algorithm, inst, seed=instance_seed, max_full_evals=20000)
        assert result.f_best == optimum


def test_counter_example_optimum_is_found_by_sa(counter_example_instance):
    result = run("sa", counter_example_instance, seed=0, max_full_evals=5000)
    assert result.f_best == 79


@pytest.mark.parametrize("params", [
    {"init": "random"},
    {"p_insert": 1.0, "p_swap": 0.0},
    {"p_insert": 0.0, "p_swap": 1.0},
    {"p_insert": 0.0, "p_swap": 0.0},  # order-block move only
])
def test_sa_variants_return_valid_schedules(params):
    inst = generate_instance(6, 3, 3, seed=4)
    result = run("sa", inst, seed=1, max_full_evals=2000, **params)
    assert sorted(result.perm) == list(range(inst.num_jobs))
    assert Evaluator(inst).total(result.perm) == result.f_best


def test_sa_rejects_invalid_parameters():
    inst = generate_instance(3, 2, 2, seed=0)
    with pytest.raises(ValueError):
        run("sa", inst, seed=0, max_full_evals=100, p0=1.5)
    with pytest.raises(ValueError):
        run("sa", inst, seed=0, max_full_evals=100, p_insert=0.8, p_swap=0.5)
    with pytest.raises(ValueError):
        run("sa", inst, seed=0, max_full_evals=100, init="best")


def test_time_budget_stops_the_run():
    inst = generate_instance(10, 5, 3, seed=5)
    ev = Evaluator(inst)
    result = simulated_annealing(ev, Budget(ev, time_limit=0.3), random.Random(0))
    assert 0.3 <= result.elapsed < 1.0
