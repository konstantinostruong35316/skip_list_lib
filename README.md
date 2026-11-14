# skip_list_lib

A probabilistically balanced ordered map: keys stay sorted, and search, insert and
delete are O(log n) in expectation without the rebalancing machinery of a tree.

```python
from skip_list_lib import SkipList

sl = SkipList()
sl.set("banana", 2)
sl.set("apple", 1)
sl.set("cherry", 3)

assert sl.get("apple") == 1
assert sl.get("missing", 0) == 0
assert list(sl) == ["apple", "banana", "cherry"]
assert list(sl.items()) == [("apple", 1), ("banana", 2), ("cherry", 3)]
assert "banana" in sl
assert sl.delete("banana") is True
assert sl.delete("banana") is False
assert len(sl) == 2
```

The exported names are `SkipList` and `SkipListError`. `SkipList` exposes
`get(key, default=None)`, `set(key, value)`, `delete(key)`, `items()`, `__len__`,
`__contains__`, `__iter__` and `__repr__`. `SkipListError` is a subclass of
`Exception` reserved for future operations that cannot be satisfied; the current
methods raise `ValueError` for invalid constructor arguments and return a sentinel
or boolean for missing keys.

## Why this exists

An ordered map needs a search structure that keeps keys sorted but does not pay the
worst-case cost of a sorted list. A skip list gets the same expected bounds as a
balanced tree while being far simpler to implement: no rotations, no colour flips,
just a tower of forward pointers and a coin flip. The trade-off is that the bounds
are probabilistic rather than worst-case, and the shape depends on the random source.
That is a deliberate choice: for the common case of an in-memory ordered map, the
simplicity is worth more than a hard worst-case guarantee.

## The awkward edge

The height of each node is chosen by a caller-supplied callable that must return a
float in `[0, 1)`. The default is `random.random`, but tests and any code that needs
reproducible structure should pass their own generator. The number of levels is
capped at `max_level`, so a pathological generator that always returns `0.0` will
push every node to the cap; the structure still behaves correctly, it just uses more
memory. Conversely, a generator that always returns values at or above `p` keeps the
list at a single level, which is correct but degrades search to O(n). Both cases are
covered by the test suite.
