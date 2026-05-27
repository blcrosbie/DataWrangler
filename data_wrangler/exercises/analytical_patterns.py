"""Python data manipulation patterns for Codility-style performance checks.

Each function is designed to avoid O(N^2) loops on large arrays. The examples
favor explicit control flow over clever one-liners because these are reference
patterns for live interview use.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Optional


Number = int | float


def _safe_number(value: object, default: Number = 0) -> Number:
    """Convert None to a numeric default while preserving ints/floats."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value
    raise TypeError(f"Expected int, float, or None; got {type(value).__name__}")


def find_duplicate_boundaries(values: Iterable[object]) -> list[tuple[int, int, object]]:
    """Return first-index/current-index pairs for repeated values.

    Hash map pattern:
      - Track the first index where each value appeared.
      - Every lookup and insert is average O(1), so the full scan is O(N).
      - This replaces the classic nested-loop duplicate search that times out
        on arrays with 100,000+ elements.

    None is treated as a valid value because Codility inputs often contain
    sentinel or missing states that still need deterministic handling.
    """
    first_seen: dict[object, int] = {}
    duplicates: list[tuple[int, int, object]] = []

    for index, value in enumerate(values):
        if value in first_seen:
            duplicates.append((first_seen[value], index, value))
        else:
            first_seen[value] = index

    return duplicates


def first_pair_with_sum(values: Iterable[Number | None], target: Number) -> Optional[tuple[int, int]]:
    """Find the first pair of indexes whose values add to target.

    Hash map matching pattern:
      - Store value -> earliest index.
      - For each value, check whether target - value has already appeared.
      - Runs in O(N) time and O(N) memory.

    None entries are ignored, which lets sparse arrays pass without special
    casing at the call site.
    """
    seen: dict[Number, int] = {}

    for index, raw_value in enumerate(values):
        if raw_value is None:
            continue

        value = _safe_number(raw_value)
        complement = target - value
        if complement in seen:
            return seen[complement], index

        if value not in seen:
            seen[value] = index

    return None


def max_window_sum(values: Sequence[Number | None], window_size: int) -> Number:
    """Return the maximum sum for any fixed-size sliding window.

    Sliding window pattern:
      - Build the first window once.
      - Move one step at a time by subtracting the outgoing value and adding the
        incoming value.
      - Runs in O(N) time and O(1) extra memory.

    None is treated as 0. Empty inputs and non-positive windows return 0.
    """
    if window_size <= 0 or not values:
        return 0

    size = min(window_size, len(values))
    current = sum(_safe_number(values[i]) for i in range(size))
    best = current

    for right in range(size, len(values)):
        left = right - size
        current += _safe_number(values[right])
        current -= _safe_number(values[left])
        if current > best:
            best = current

    return best


def longest_streak_at_or_above(values: Iterable[Number | None], threshold: Number) -> int:
    """Return the longest consecutive run of values meeting a threshold.

    Sliding stream pattern:
      - Keep only the current streak length and best streak length.
      - Reset the current streak when the predicate fails.
      - Runs in O(N) time and O(1) extra memory.

    None breaks the streak because missing data should not satisfy a numeric
    threshold unless the problem explicitly says otherwise.
    """
    current = 0
    best = 0

    for value in values:
        if value is not None and _safe_number(value) >= threshold:
            current += 1
            if current > best:
                best = current
        else:
            current = 0

    return best


def two_sum_sorted(values: Sequence[Number | None], target: Number) -> Optional[tuple[int, int]]:
    """Find indexes of two values in a sorted sequence that add to target.

    Two-pointer pattern:
      - Start at both ends and move the pointer that can improve the sum.
      - Each pointer moves at most N times, so runtime is O(N).
      - Assumes non-None values are sorted in ascending order. None values at
        either edge are skipped defensively.
    """
    left = 0
    right = len(values) - 1

    while left < right:
        left_value = values[left]
        right_value = values[right]

        if left_value is None:
            left += 1
            continue
        if right_value is None:
            right -= 1
            continue

        total = _safe_number(left_value) + _safe_number(right_value)
        if total == target:
            return left, right
        if total < target:
            left += 1
        else:
            right -= 1

    return None


def filter_with_two_pointers(
    sorted_values: Sequence[Number | None],
    minimum: Number,
    maximum: Number,
) -> list[Number]:
    """Return values inside [minimum, maximum] from a sorted sequence.

    Two-pointer filtering pattern:
      - Advance the left pointer past values below the lower bound.
      - Retreat the right pointer past values above the upper bound.
      - Copy only the surviving interval.
      - Runs in O(N) time with O(K) output memory, where K is the number of
        retained values.

    None values are skipped at the edges. Internal None values are ignored while
    building the result.
    """
    left = 0
    right = len(sorted_values) - 1

    while left <= right:
        value = sorted_values[left]
        if value is None or _safe_number(value) < minimum:
            left += 1
        else:
            break

    while left <= right:
        value = sorted_values[right]
        if value is None or _safe_number(value) > maximum:
            right -= 1
        else:
            break

    return [
        _safe_number(value)
        for value in sorted_values[left : right + 1]
        if value is not None and minimum <= _safe_number(value) <= maximum
    ]


if __name__ == "__main__":
    sample = [None, -3, -1, 2, 4, 7, 11]
    print("duplicate boundaries:", find_duplicate_boundaries([1, 2, 1, None, None]))
    print("first pair with sum:", first_pair_with_sum(sample, 6))
    print("max window sum:", max_window_sum(sample, 3))
    print("longest streak:", longest_streak_at_or_above(sample, 2))
    print("two sum sorted:", two_sum_sorted(sample, 6))
    print("filtered:", filter_with_two_pointers(sample, -1, 7))
