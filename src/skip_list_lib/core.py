"""A probabilistically balanced ordered map backed by a skip list.

The skip list stores keys in sorted order and maps each key to a value. It uses a
randomised level assignment so that search, insertion and deletion are O(log n) in
expectation without the complexity of a balanced tree.

Randomness is supplied by a caller-provided callable returning a float in [0, 1).
This keeps the structure deterministic under a fake generator in tests and lets the
caller choose the source of randomness (e.g. ``random.random``).
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, List, Optional, Tuple


class SkipListError(Exception):
    """Raised for operations that cannot be satisfied by the skip list."""


class _Node:
    """A single key/value slot at one level of the skip list.

    ``forward`` holds the next node at each level this node participates in.
    """

    __slots__ = ("key", "value", "forward")

    def __init__(self, key: Any, value: Any, height: int) -> None:
        self.key = key
        self.value = value
        self.forward: List[Optional[_Node]] = [None] * height


class SkipList:
    """An ordered map with expected O(log n) search, insert and delete.

    Keys must be mutually comparable and support ``<`` and ``==``. Values may be
    any object. ``max_level`` bounds the number of levels; ``p`` is the probability
    that a node is promoted to the next level. The default ``p=0.5`` gives a good
    balance between memory use and search speed.

    ``random`` must be a callable returning a float in [0, 1). It is used only to
    choose node heights; passing a deterministic generator makes the structure's
    shape reproducible, which is what the test suite relies on.
    """

    def __init__(
        self,
        max_level: int = 16,
        p: float = 0.5,
        random: Callable[[], float] = None,
    ) -> None:
        if max_level < 1:
            raise ValueError("max_level must be at least 1")
        if not 0.0 < p < 1.0:
            raise ValueError("p must be strictly between 0 and 1")
        if random is None:
            import random as _random

            random = _random.random
        self.max_level = max_level
        self.p = p
        self._random = random
        self._level = 1
        # Sentinel head node participates at every level.
        self._head = _Node(None, None, max_level)
        self._size = 0

    # -- introspection -----------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: Any) -> bool:
        return self._find_node(key) is not None

    def __iter__(self) -> Iterator[Any]:
        """Iterate keys in ascending order."""
        node = self._head.forward[0]
        while node is not None:
            yield node.key
            node = node.forward[0]

    def __repr__(self) -> str:
        return f"SkipList(size={self._size}, level={self._level})"

    def items(self) -> Iterator[Tuple[Any, Any]]:
        """Iterate ``(key, value)`` pairs in ascending key order."""
        node = self._head.forward[0]
        while node is not None:
            yield node.key, node.value
            node = node.forward[0]

    # -- public map operations --------------------------------------------

    def get(self, key: Any, default: Any = None) -> Any:
        """Return the value for *key*, or *default* if absent."""
        node = self._find_node(key)
        if node is None:
            return default
        return node.value

    def set(self, key: Any, value: Any) -> None:
        """Insert or update *key* with *value*."""
        update = [None] * self.max_level
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node

        candidate = node.forward[0]
        if candidate is not None and candidate.key == key:
            candidate.value = value
            return

        height = self._random_level()
        if height > self._level:
            for i in range(self._level, height):
                update[i] = self._head
            self._level = height

        new_node = _Node(key, value, height)
        for i in range(height):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self._size += 1

    def delete(self, key: Any) -> bool:
        """Remove *key*. Return True if it was present, False otherwise."""
        update = [None] * self.max_level
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node

        target = node.forward[0]
        if target is None or target.key != key:
            return False

        for i in range(self._level):
            if update[i].forward[i] is not target:
                break
            update[i].forward[i] = target.forward[i]

        while self._level > 1 and self._head.forward[self._level - 1] is None:
            self._level -= 1
        self._size -= 1
        return True

    # -- helpers -----------------------------------------------------------

    def _random_level(self) -> int:
        """Draw a node height in [1, max_level].

        Each promotion costs one call to the random source. The loop stops as soon
        as the draw fails the ``p`` threshold, so the expected number of calls is
        constant regardless of ``max_level``.
        """
        level = 1
        while level < self.max_level and self._random() < self.p:
            level += 1
        return level

    def _find_node(self, key: Any) -> Optional[_Node]:
        node = self._head
        for i in range(self._level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
        candidate = node.forward[0]
        if candidate is not None and candidate.key == key:
            return candidate
        return None
