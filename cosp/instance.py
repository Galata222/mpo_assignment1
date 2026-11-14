"""Problem instances: n orders, o jobs per order, m machines.

Jobs are numbered 0 .. n*o-1 with job = order * o + index_in_order, so the
order of a job is job // o.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Instance:
    name: str
    n: int  # number of orders
    o: int  # jobs per order
    m: int  # machines
    p: tuple[tuple[int, ...], ...]  # p[job][machine] processing time
    best_known: float | None = None  # lowest known objective value (from the authors' file)
    instance_id: int | None = None
    order_of: tuple[int, ...] = field(init=False, repr=False)  # order_of[job]
    total_time: tuple[int, ...] = field(init=False, repr=False)  # TP: sum of a job's processing times

    def __post_init__(self) -> None:
        if len(self.p) != self.n * self.o:
            raise ValueError(f"{self.name}: expected {self.n * self.o} jobs, got {len(self.p)}")
        if any(len(row) != self.m for row in self.p):
            raise ValueError(f"{self.name}: every job needs {self.m} processing times")
        object.__setattr__(self, "order_of", tuple(job // self.o for job in range(self.num_jobs)))
        object.__setattr__(self, "total_time", tuple(sum(row) for row in self.p))

    @property
    def num_jobs(self) -> int:
        return self.n * self.o

    def jobs_of_order(self, order: int) -> list[int]:
        return list(range(order * self.o, (order + 1) * self.o))


def load_instance(path: str | Path) -> Instance:
    """Read one CSV file of the authors' data set (github.com/Julius2627/COSP_Flow_Shop).

    Header: n, o, m, instance number, lowest known total completion time.
    Then, per order: one line with the order id followed by o lines holding the
    m processing times of one job each (machine sequence = column sequence).
    """
    path = Path(path)
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    header = lines[0].split(",")
    if len(header) != 5:
        raise ValueError(f"{path}: header must have 5 fields, got {lines[0]!r}")
    n, o, m, instance_id = (int(x) for x in header[:4])
    best_known = float(header[4])
    if len(lines) != 1 + n * (o + 1):
        raise ValueError(f"{path}: expected {1 + n * (o + 1)} non-empty lines, got {len(lines)}")

    p: list[tuple[int, ...]] = []
    row = 1
    for order in range(n):
        if int(lines[row]) != order:
            raise ValueError(f"{path}: line {row + 1} should be order id {order}, got {lines[row]!r}")
        row += 1
        for _ in range(o):
            p.append(tuple(int(x) for x in lines[row].split(",")))
            row += 1
    return Instance(path.stem, n, o, m, tuple(p), best_known, instance_id)


def generate_instance(n: int, o: int, m: int, seed: int) -> Instance:
    """Random instance with processing times uniform on 1..100, as in the paper (Sec. 5.1)."""
    rng = random.Random(seed)
    p = tuple(tuple(rng.randint(1, 100) for _ in range(m)) for _ in range(n * o))
    return Instance(f"generated-{n}-{o}-{m}-seed{seed}", n, o, m, p)


def instance_path(data_dir: str | Path, n: int, o: int, m: int, instance_id: int) -> Path:
    return Path(data_dir) / f"{n}_orders" / f"instance-{n}-{o}-{m}-{instance_id}.csv"
