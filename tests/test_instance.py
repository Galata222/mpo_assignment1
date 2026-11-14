import pytest

from cosp.instance import generate_instance, instance_path, load_instance

# First file of the authors' data set (3_orders/instance-3-2-2-0.csv).
SAMPLE = """3,2,2,0,629.0
0
82,15
4,95
1
36,32
29,18
2
95,14
87,95
"""


def test_load_instance(tmp_path):
    path = tmp_path / "instance-3-2-2-0.csv"
    path.write_text(SAMPLE, encoding="utf-8")
    inst = load_instance(path)
    assert (inst.n, inst.o, inst.m, inst.instance_id) == (3, 2, 2, 0)
    assert inst.best_known == 629.0
    assert inst.name == "instance-3-2-2-0"
    assert inst.p == ((82, 15), (4, 95), (36, 32), (29, 18), (95, 14), (87, 95))
    assert inst.order_of == (0, 0, 1, 1, 2, 2)
    assert inst.total_time == (97, 99, 68, 47, 109, 182)


def test_load_instance_rejects_truncated_file(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text(SAMPLE.rsplit("\n", 2)[0], encoding="utf-8")
    with pytest.raises(ValueError):
        load_instance(path)


def test_generate_instance_is_reproducible_and_in_range():
    a = generate_instance(4, 3, 2, seed=5)
    b = generate_instance(4, 3, 2, seed=5)
    assert a.p == b.p
    assert a.num_jobs == 12
    assert all(1 <= t <= 100 for row in a.p for t in row)


def test_instance_path_follows_repository_layout():
    path = instance_path("data", 10, 5, 3, 12)
    assert path.parts[-2:] == ("10_orders", "instance-10-5-3-12.csv")
