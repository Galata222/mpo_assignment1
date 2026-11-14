"""The objective function must reproduce the values printed in the paper."""
from conftest import brute_force_optimum, job

from cosp.objective import Evaluator


def test_example_schedule_has_total_completion_time_37(example_instance):
    inst = example_instance
    schedule = [job(inst, *x) for x in [(2, 2), (2, 1), (2, 3), (1, 1), (1, 2), (1, 3)]]
    assert Evaluator(inst).total(schedule) == 37  # Fig. 3: C_2 = 12, C_1 = 25


def test_makespan_of_single_order_matches_fig2(example_instance):
    inst = example_instance
    assert Evaluator(inst).makespan([job(inst, 1, 1), job(inst, 1, 2), job(inst, 1, 3)]) == 15


def test_table5_values(counter_example_instance):
    inst = counter_example_instance
    table5 = [
        ([(1, 1), (1, 2), (2, 1), (2, 2)], 85),
        ([(1, 1), (1, 2), (2, 2), (2, 1)], 80),
        ([(1, 2), (1, 1), (2, 1), (2, 2)], 90),
        ([(1, 2), (1, 1), (2, 2), (2, 1)], 90),
        ([(2, 1), (2, 2), (1, 1), (1, 2)], 103),
        ([(2, 1), (2, 2), (1, 2), (1, 1)], 103),
        ([(2, 2), (2, 1), (1, 1), (1, 2)], 83),
        ([(2, 2), (2, 1), (1, 2), (1, 1)], 83),
    ]
    ev = Evaluator(inst)
    for sequence, expected in table5:
        assert ev.total([job(inst, *x) for x in sequence]) == expected


def test_optimum_of_counter_example_is_79_with_interleaved_orders(counter_example_instance):
    inst = counter_example_instance
    interleaved = [job(inst, *x) for x in [(2, 2), (1, 2), (1, 1), (2, 1)]]
    assert Evaluator(inst).total(interleaved) == 79
    assert brute_force_optimum(inst) == 79


def test_partial_sequence_counts_only_present_orders(example_instance):
    inst = example_instance
    assert Evaluator(inst).total([job(inst, 2, 2), job(inst, 2, 1), job(inst, 2, 3)]) == 12


def test_evaluations_are_counted_in_full_schedule_equivalents(example_instance):
    ev = Evaluator(example_instance)
    ev.total(list(range(6)))
    ev.total([0, 1, 2])
    ev.makespan([3, 4, 5])
    assert ev.full_evals == 2.0
