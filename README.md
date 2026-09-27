# reservoir_sample

Uniform sampling of N items from a stream of unknown length, in one pass, using Algorithm R.

## Usage

```python
from reservoir_sample import ReservoirSampler

sampler = ReservoirSampler(3)
sample = sampler.feed(iter(range(1_000_000)))
print(sample)          # a list of 3 ints, uniformly drawn
print(sampler.seen)    # 1000000 — number of items offered
```

For incremental feeding or explicit control over `random`:

```python
import random
from reservoir_sample import AlgorithmR

r = AlgorithmR(5, rng=random.Random(42))
for x in range(1_000_000):
    r.add(x)
result = r.sample()
```

## Why this exists

When you need a fixed-size uniform sample but cannot hold the full stream in
memory and do not know its length in advance. Algorithm R is the textbook
answer: one pass, O(stream) time, O(N) memory, and provably uniform — after T
items, each seen item has probability N/T of being in the reservoir.

The trade-off: it is *not* weighted sampling, it cannot remove items once
admitted before replacement, and `feed()` consumes the whole iterable before
returning. If you need streaming outputs as you go, call `add()` per item and
read `sample()` whenever you like.

## Edge cases

- `capacity == 0` is allowed and yields `[]`. It is the "sample nothing" case,
  not an error.
- While the stream length is below `capacity`, the reservoir holds every item
  seen, in arrival order.
- `ReservoirSampler` and `AlgorithmR` accept an optional `rng=random.Random(...)`
  for deterministic output. Without one, the global `random` module is used
  and results are non-deterministic across runs.

## Exported names

- `ReservoirSampler(capacity, rng=None)` — wrapper with `feed(stream) -> list`,
  `add(item)`, `sample() -> list`, `capacity -> int`, `seen -> int`.
- `AlgorithmR(capacity, rng=None)` — the sampler itself, with `add(item)`,
  `sample() -> list`, `next_index_for_stream_length(T) -> int | None`,
  `capacity -> int`, `seen -> int`.
