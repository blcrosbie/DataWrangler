"""Codility-style correctness and performance harness.

This script exercises the SQL reference queries in exercises/sql_challenges.sql
and the Python optimization patterns in exercises/analytical_patterns.py.

It intentionally uses only Python's standard library. SQL execution runs through
sqlite3 because it gives an in-memory database without external services. The
SQL challenge file is written with PostgreSQL-first, SQLite-compatible query
blocks so the same core CTE/window-function logic can be smoke-tested locally.
"""

from __future__ import annotations

import argparse
import importlib.util
import random
import sqlite3
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
EXERCISES_DIR = ROOT / "exercises"
SQL_FILE = EXERCISES_DIR / "sql_challenges.sql"
PATTERNS_FILE = EXERCISES_DIR / "analytical_patterns.py"

STRICT_SECONDS = 1.5
STRICT_PEAK_MB = 64.0
DEFAULT_ROWS = 50_000


def load_sql_block(name: str) -> str:
    """Extract a named SQL block marked by -- name: X and -- end: X."""
    source = SQL_FILE.read_text(encoding="utf-8")
    start_marker = f"-- name: {name}"
    end_marker = f"-- end: {name}"

    start = source.find(start_marker)
    if start == -1:
        raise ValueError(f"Missing SQL start marker: {start_marker}")

    query_start = source.find("\n", start)
    if query_start == -1:
        raise ValueError(f"Malformed SQL block: {name}")

    end = source.find(end_marker, query_start)
    if end == -1:
        raise ValueError(f"Missing SQL end marker: {end_marker}")

    return source[query_start:end].strip()


def load_patterns_module() -> Any:
    spec = importlib.util.spec_from_file_location("analytical_patterns", PATTERNS_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {PATTERNS_FILE}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def timed_call(label: str, fn: Callable[[], Any]) -> tuple[Any, float, float]:
    """Run a callable and return result, elapsed seconds, and peak MiB."""
    tracemalloc.start()
    started = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"{label:<36} {elapsed:>8.4f}s  peak={peak_mb:>8.2f} MiB")
    return result, elapsed, peak_mb


def assert_resource_bounds(label: str, elapsed: float, peak_mb: float) -> None:
    if elapsed > STRICT_SECONDS:
        raise AssertionError(f"{label} exceeded {STRICT_SECONDS}s: {elapsed:.4f}s")
    if peak_mb > STRICT_PEAK_MB:
        raise AssertionError(f"{label} exceeded {STRICT_PEAK_MB} MiB: {peak_mb:.2f} MiB")


def new_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -20000")
    return conn


def run_query(conn: sqlite3.Connection, name: str) -> list[tuple[Any, ...]]:
    query = load_sql_block(name)
    return list(conn.execute(query))


def test_sql_sum_correctness() -> None:
    query_name = "SqlSum"

    conn = new_connection()
    conn.execute("CREATE TABLE numbers(value INTEGER)")
    assert run_query(conn, query_name) == [(0,)]
    conn.close()

    conn = new_connection()
    conn.execute("CREATE TABLE numbers(value INTEGER)")
    conn.executemany("INSERT INTO numbers(value) VALUES (?)", [(None,), (None,)])
    assert run_query(conn, query_name) == [(0,)]
    conn.close()

    conn = new_connection()
    conn.execute("CREATE TABLE numbers(value INTEGER)")
    conn.executemany("INSERT INTO numbers(value) VALUES (?)", [(-5,), (10,), (None,), (-2,)])
    assert run_query(conn, query_name) == [(3,)]
    conn.close()


def test_sql_events_delta_correctness() -> None:
    query_name = "SqlEventsDelta"

    conn = new_connection()
    conn.execute(
        "CREATE TABLE events(event_type TEXT, event_time INTEGER, value INTEGER)"
    )
    assert run_query(conn, query_name) == []
    conn.close()

    conn = new_connection()
    conn.execute(
        "CREATE TABLE events(event_type TEXT, event_time INTEGER, value INTEGER)"
    )
    conn.executemany(
        "INSERT INTO events(event_type, event_time, value) VALUES (?, ?, ?)",
        [
            ("deploy", 1, 10),
            ("deploy", 2, None),
            ("deploy", 3, 22),
            ("incident", 1, -4),
            ("incident", 2, -10),
            (None, 1, 99),
        ],
    )
    assert run_query(conn, query_name) == [("deploy", 22, 0, 22), ("incident", -10, -4, -6)]
    conn.close()


def test_sql_world_cup_correctness() -> None:
    query_name = "SqlWorldCup"

    conn = new_connection()
    conn.execute("CREATE TABLE teams(team_name TEXT)")
    conn.execute(
        """
        CREATE TABLE matches(
            host_team TEXT,
            guest_team TEXT,
            host_goals INTEGER,
            guest_goals INTEGER
        )
        """
    )
    conn.executemany(
        "INSERT INTO teams(team_name) VALUES (?)",
        [("Brazil",), ("Canada",), ("Japan",), ("Norway",)],
    )
    conn.executemany(
        "INSERT INTO matches(host_team, guest_team, host_goals, guest_goals) VALUES (?, ?, ?, ?)",
        [
            ("Brazil", "Canada", 2, 0),
            ("Japan", "Brazil", 1, 1),
            ("Canada", "Japan", None, 3),
        ],
    )
    assert run_query(conn, query_name) == [
        ("Brazil", 4, 2),
        ("Japan", 4, 2),
        ("Canada", 0, 2),
        ("Norway", 0, 0),
    ]
    conn.close()


def benchmark_sql(rows: int) -> None:
    conn = new_connection()
    conn.execute("CREATE TABLE numbers(value INTEGER)")
    conn.executemany(
        "INSERT INTO numbers(value) VALUES (?)",
        ((i if i % 17 else None,) for i in range(-rows // 2, rows // 2)),
    )
    _, elapsed, peak_mb = timed_call("SQL SqlSum performance", lambda: run_query(conn, "SqlSum"))
    assert_resource_bounds("SQL SqlSum", elapsed, peak_mb)
    conn.close()

    conn = new_connection()
    conn.execute("CREATE TABLE events(event_type TEXT, event_time INTEGER, value INTEGER)")
    event_rows = (
        (f"type_{i % 100}", i, None if i % 41 == 0 else i % 1000)
        for i in range(rows)
    )
    conn.executemany(
        "INSERT INTO events(event_type, event_time, value) VALUES (?, ?, ?)",
        event_rows,
    )
    _, elapsed, peak_mb = timed_call(
        "SQL SqlEventsDelta performance", lambda: run_query(conn, "SqlEventsDelta")
    )
    assert_resource_bounds("SQL SqlEventsDelta", elapsed, peak_mb)
    conn.close()

    conn = new_connection()
    conn.execute("CREATE TABLE teams(team_name TEXT)")
    conn.execute(
        """
        CREATE TABLE matches(
            host_team TEXT,
            guest_team TEXT,
            host_goals INTEGER,
            guest_goals INTEGER
        )
        """
    )
    team_count = 1_000
    conn.executemany(
        "INSERT INTO teams(team_name) VALUES (?)",
        ((f"team_{i}",) for i in range(team_count)),
    )
    match_rows = (
        (
            f"team_{i % team_count}",
            f"team_{(i * 7 + 3) % team_count}",
            None if i % 97 == 0 else i % 5,
            None if i % 89 == 0 else (i * 3) % 5,
        )
        for i in range(rows)
    )
    conn.executemany(
        "INSERT INTO matches(host_team, guest_team, host_goals, guest_goals) VALUES (?, ?, ?, ?)",
        match_rows,
    )
    _, elapsed, peak_mb = timed_call(
        "SQL SqlWorldCup performance", lambda: run_query(conn, "SqlWorldCup")
    )
    assert_resource_bounds("SQL SqlWorldCup", elapsed, peak_mb)
    conn.close()


def test_python_correctness(patterns: Any) -> None:
    assert patterns.find_duplicate_boundaries([]) == []
    assert patterns.find_duplicate_boundaries([None, None, 1, 1, 2]) == [(0, 1, None), (2, 3, 1)]
    assert patterns.find_duplicate_boundaries([-1, -2, -1, -2]) == [(0, 2, -1), (1, 3, -2)]

    assert patterns.max_window_sum([], 3) == 0
    assert patterns.max_window_sum([None, None], 2) == 0
    assert patterns.max_window_sum([-5, -1, -7], 2) == -6
    assert patterns.max_window_sum([4, None, 2, 9, -3], 3) == 11

    assert patterns.longest_streak_at_or_above([], 10) == 0
    assert patterns.longest_streak_at_or_above([None, 10, 11, 4, 12], 10) == 2

    assert patterns.two_sum_sorted([], 10) is None
    assert patterns.two_sum_sorted([-5, -2, 1, 4, 8], 2) == (1, 3)
    assert patterns.two_sum_sorted([None, -2, 1, 4, 8], 2) == (1, 3)

    assert patterns.filter_with_two_pointers([], 0, 10) == []
    assert patterns.filter_with_two_pointers([None, -4, 0, 3, 9, 12], 0, 9) == [0, 3, 9]


def benchmark_python(patterns: Any, rows: int) -> None:
    rng = random.Random(42)
    data = [rng.randint(-10_000, 10_000) for _ in range(rows)]
    data.extend(data[: rows // 20])
    sorted_data = sorted(data)

    _, elapsed, peak_mb = timed_call(
        "Python hash map performance",
        lambda: patterns.find_duplicate_boundaries(data),
    )
    assert_resource_bounds("Python hash map", elapsed, peak_mb)

    _, elapsed, peak_mb = timed_call(
        "Python sliding window performance",
        lambda: patterns.max_window_sum(data, 250),
    )
    assert_resource_bounds("Python sliding window", elapsed, peak_mb)

    _, elapsed, peak_mb = timed_call(
        "Python streak performance",
        lambda: patterns.longest_streak_at_or_above(data, 0),
    )
    assert_resource_bounds("Python streak", elapsed, peak_mb)

    target = sorted_data[rows // 3] + sorted_data[(rows * 2) // 3]
    _, elapsed, peak_mb = timed_call(
        "Python two-pointer performance",
        lambda: patterns.two_sum_sorted(sorted_data, target),
    )
    assert_resource_bounds("Python two-pointer", elapsed, peak_mb)


def run_all(rows: int) -> None:
    print("Correctness matrix")
    test_sql_sum_correctness()
    test_sql_events_delta_correctness()
    test_sql_world_cup_correctness()
    patterns = load_patterns_module()
    test_python_correctness(patterns)
    print("  all correctness checks passed")

    print("\nPerformance matrix")
    benchmark_sql(rows)
    benchmark_python(patterns, rows)

    sample = [random.randint(-100, 100) for _ in range(5_000)]
    p95 = statistics.quantiles(sample, n=20)[18]
    print(f"\nHarness sanity metric: sample p95={p95}")
    print("All Codility-style checks passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="Synthetic row count for performance tests. Default: 50000.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.rows < 10_000:
        raise SystemExit("--rows must be at least 10000 to exercise large-data behavior")
    run_all(args.rows)
