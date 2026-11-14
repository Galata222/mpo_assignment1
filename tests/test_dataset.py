"""Checks against the authors' data set; skipped until it has been downloaded."""
import itertools
from pathlib import Path

import pytest

from cosp.instance import load_instance
from cosp.objective import Evaluator

DATA = Path(__file__).resolve().parent.parent / "data" / "COSP_Flow_Shop"

pytestmark = pytest.mark.skipif(not DATA.is_dir(), reason="run scripts/fetch_instances.py first")


def test_all_instance_files_load():
    files = sorted(DATA.rglob("instance-*.csv"))
    assert len(files) == 1620  # 54 problem sizes x 30 instances
    for path in files:
        inst = load_instance(path)
        assert inst.name == f"instance-{inst.n}-{inst.o}-{inst.m}-{inst.instance_id}"


def test_brute_force_optimum_equals_the_published_best_known_value():
    """For 3 orders x 2 jobs every schedule can be enumerated (720 permutations).

    Agreement with the authors' values shows that our objective function is
    the same as theirs.
    """
    files = sorted((DATA / "3_orders").glob("instance-3-2-*.csv"))
    assert len(files) == 90
    for path in files:
        inst = load_instance(path)
        ev = Evaluator(inst)
        optimum = min(ev.total(perm) for perm in itertools.permutations(range(inst.num_jobs)))
        assert optimum == inst.best_known, path.name
