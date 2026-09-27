"""Tests for reservoir_sample. Deterministic; never touches wall-clock time."""

import random
import unittest

from reservoir_sample import ReservoirSampler, AlgorithmR


class _FakeRandom:
    """Deterministic stand-in for random.Random returning a fixed value sequence."""

    def __init__(self, values):
        self._values = list(values)
        self._i = 0

    def randrange(self, low, high):
        # Caller (AlgorithmR) only ever calls randrange(0, n).
        v = self._values[self._i % len(self._values)]
        self._i += 1
        return v


class FillPhaseTests(unittest.TestCase):
    def test_under_capacity_keeps_all_in_order(self):
        s = AlgorithmR(3)
        for x in ("a", "b"):
            s.add(x)
        self.assertEqual(s.sample(), ["a", "b"])
        self.assertEqual(s.seen, 2)

    def test_at_capacity_keeps_all(self):
        s = AlgorithmR(3)
        for x in ("a", "b", "c"):
            s.add(x)
        self.assertEqual(s.sample(), ["a", "b", "c"])
        self.assertEqual(s.seen, 3)

    def test_capacity_zero_drops_everything(self):
        s = AlgorithmR(0)
        for x in (1, 2, 3):
            s.add(x)
        self.assertEqual(s.sample(), [])
        self.assertEqual(s.seen, 3)


class NextIndexTests(unittest.TestCase):
    def test_fill_phase_returns_T(self):
        s = AlgorithmR(3, rng=random.Random(0))
        # Slots for items 1..3 (0-indexed T = 0, 1, 2).
        self.assertEqual(s.next_index_for_stream_length(0), 0)
        self.assertEqual(s.next_index_for_stream_length(1), 1)
        self.assertEqual(s.next_index_for_stream_length(2), 2)

    def test_replacement_phase_returns_slot_or_none(self):
        # capacity 2; rng yields 1 (keep -> slot 1), then 2 (drop -> None).
        s = AlgorithmR(2, rng=_FakeRandom([1, 2]))
        self.assertEqual(s.next_index_for_stream_length(2), 1)   # T+1=3, j=1<2
        self.assertIsNone(s.next_index_for_stream_length(3))     # T+1=4, j=2>=2


class ReplacementTests(unittest.TestCase):
    def test_replaces_at_specified_slot(self):
        s = AlgorithmR(3, rng=_FakeRandom([1]))
        for x in ("a", "b", "c", "d"):
            s.add(x)
        # After fill, reservoir = [a,b,c]. Item 4 drawn j=1 -> replace slot 1.
        self.assertEqual(s.sample(), ["a", "d", "c"])
        self.assertEqual(s.seen, 4)

    def test_item_dropped_when_j_at_or_above_capacity(self):
        # capacity 2; fill [a,b]; item 3 j=2 (>= capacity) dropped; item 4 j=0 kept.
        s = AlgorithmR(2, rng=_FakeRandom([2, 0]))
        for x in ("a", "b", "c", "d"):
            s.add(x)
        self.assertEqual(s.sample(), ["d", "b"])


class WrapperTests(unittest.TestCase):
    def test_feed_consumes_and_returns_reservoir(self):
        s = ReservoirSampler(3, rng=random.Random(0))
        out = s.feed(iter(range(10)))
        self.assertEqual(len(out), 3)
        self.assertEqual(set(out).issubset(set(range(10))), True)
        self.assertEqual(s.seen, 10)
        self.assertEqual(s.capacity, 3)

    def test_add_then_sample_progressive(self):
        s = ReservoirSampler(2, rng=_FakeRandom([1, 0]))
        s.add("x")
        self.assertEqual(s.sample(), ["x"])
        s.add("y")
        self.assertEqual(s.sample(), ["x", "y"])
        s.add("z")  # T=2 -> j=1 -> replace slot 1
        self.assertEqual(s.sample(), ["x", "z"])
        s.add("w")  # T=3 -> j=0 -> replace slot 0
        self.assertEqual(s.sample(), ["w", "z"])

    def test_capacity_zero_wrapper(self):
        s = ReservoirSampler(0)
        self.assertEqual(s.feed([1, 2, 3]), [])
        self.assertEqual(s.seen, 3)


class ValidationTests(unittest.TestCase):
    def test_negative_capacity_raises(self):
        with self.assertRaises(ValueError):
            AlgorithmR(-1)

    def test_non_int_capacity_raises(self):
        with self.assertRaises(TypeError):
            AlgorithmR(2.5)

    def test_negative_T_raises(self):
        with self.assertRaises(ValueError):
            AlgorithmR(3).next_index_for_stream_length(-1)


class StatisticalSanityTests(unittest.TestCase):
    """End-to-end uniformity check using a fixed seed. Asserts types and length
    rather than exact contents, and bounds the count of any single item so the
    test stays deterministic yet still catches gross bias."""

    def test_uniform_over_many_trials(self):
        capacity = 3
        stream = list(range(20))
        counts = [0] * 20
        for seed in range(2000):
            s = AlgorithmR(capacity, rng=random.Random(seed))
            for x in stream:
                s.add(x)
            for x in s.sample():
                counts[x] += 1
        total = sum(counts)
        self.assertEqual(total, capacity * 2000)
        # With 6000 slots across 20 equal items, expect ~300 each; allow [150, 450].
        for c in counts:
            self.assertGreater(c, 150)
            self.assertLess(c, 450)


if __name__ == "__main__":
    unittest.main()
