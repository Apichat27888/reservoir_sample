"""Reservoir sampling (Algorithm R) over a stream of unknown length.

WHY `random=None` default: exposing `add` as the public surface means callers
should not need to thread a `random.Random` instance around just to get started.
The cost of `random.randint` is negligible relative to any real stream work.
Pass an explicit `random=random.Random(seed)` when reproducibility matters.
"""

from __future__ import annotations

import random


class AlgorithmR:
    """Streaming reservoir sampler: uniform N-of-everything-so-far.

    Guarantees that after processing T items, each of those T items has equal
    probability N/T of being in the final reservoir (truncated to min(N, T)).
    One pass, O(T) time, O(N) memory.

    `next_index_for_stream_length(T)` returns the slot to replace for the (T+1)-th
    item, or None to skip. Exposed mainly for testing at exact boundaries; normal
    callers should use `add`.
    """

    __slots__ = ("_reservoir", "_capacity", "_seen", "_rand")

    def __init__(self, capacity: int, rng: random.Random | None = None) -> None:
        if not isinstance(capacity, int):
            raise TypeError(f"capacity must be int, got {type(capacity).__name__}")
        if capacity < 0:
            raise ValueError(f"capacity must be non-negative, got {capacity}")
        self._capacity = capacity
        self._reservoir: list = []
        self._seen = 0
        self._rand = rng if rng is not None else random

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def seen(self) -> int:
        """Number of items offered so far."""
        return self._seen

    def add(self, item) -> None:
        """Offer one item to the reservoir."""
        if self._capacity == 0:
            self._seen += 1
            return
        idx = self.next_index_for_stream_length(self._seen)
        if idx is not None:
            if idx < len(self._reservoir):
                self._reservoir[idx] = item
            else:
                self._reservoir.append(item)
        self._seen += 1

    def next_index_for_stream_length(self, T: int) -> int | None:
        """Replacement slot index for the (T+1)-th item, or None if no replace.

        For T < capacity the slot is T (fill phase). For T >= capacity draw a
        uniform slot in [0, T]; keep the item iff it lands in [0, capacity).
        Returns the slot to overwrite, or None meaning "drop this item".
        """
        if T < 0:
            raise ValueError(f"T must be non-negative, got {T}")
        n_after = T + 1
        if n_after <= self._capacity:
            return T
        j = self._rand.randrange(0, n_after)
        if j < self._capacity:
            return j
        return None

    def sample(self) -> list:
        """Current reservoir contents (a copy)."""
        return list(self._reservoir)


class ReservoirSampler:
    """Convenience wrapper that fills from any iterable on demand.

    WHY a wrapper: the inner `AlgorithmR` is the decision boundary; the wrapper
    owns the iteration loop and the `seen`/`capacity` fields, so callers don't
    hand-roll `for x in stream: sampler.add(x)` every time. Construction with
    `capacity=0` is the legitimate "sample nothing" case and is honoured.
    """

    __slots__ = ("_algo",)

    def __init__(self, capacity: int, rng: random.Random | None = None) -> None:
        self._algo = AlgorithmR(capacity, rng)

    def feed(self, stream) -> list:
        """Consume the entire stream and return the final reservoir."""
        for item in stream:
            self._algo.add(item)
        return self._algo.sample()

    def add(self, item) -> None:
        self._algo.add(item)

    def sample(self) -> list:
        return self._algo.sample()

    @property
    def capacity(self) -> int:
        return self._algo.capacity

    @property
    def seen(self) -> int:
        return self._algo.seen
