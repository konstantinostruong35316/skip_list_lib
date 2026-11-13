import unittest

from skip_list_lib import SkipList, SkipListError


class _Counter:
    """Deterministic random source that cycles through a fixed sequence.

    Returning values from a list keeps every test reproducible: the skip list's
    shape depends only on the sequence, never on the platform's RNG.
    """

    def __init__(self, values):
        if not values:
            raise ValueError("need at least one value")
        self._values = list(values)
        self._index = 0

    def __call__(self):
        value = self._values[self._index % len(self._values)]
        self._index += 1
        return value


def _always(threshold):
    """Return a callable that always yields *threshold*."""
    return lambda: threshold


class TestConstruction(unittest.TestCase):
    def test_rejects_bad_max_level(self):
        with self.assertRaises(ValueError):
            SkipList(max_level=0)

    def test_rejects_bad_probability(self):
        with self.assertRaises(ValueError):
            SkipList(p=0.0)
        with self.assertRaises(ValueError):
            SkipList(p=1.0)

    def test_default_random_is_usable(self):
        sl = SkipList()
        sl.set("a", 1)
        self.assertEqual(sl.get("a"), 1)


class TestGetSet(unittest.TestCase):
    def test_get_missing_returns_default(self):
        sl = SkipList(random=_always(0.9))
        self.assertIsNone(sl.get("nope"))
        self.assertEqual(sl.get("nope", 42), 42)

    def test_set_then_get(self):
        sl = SkipList(random=_always(0.9))
        sl.set("x", 10)
        self.assertEqual(sl.get("x"), 10)
        self.assertEqual(len(sl), 1)

    def test_update_existing_key(self):
        sl = SkipList(random=_always(0.9))
        sl.set("x", 10)
        sl.set("x", 20)
        self.assertEqual(sl.get("x"), 20)
        self.assertEqual(len(sl), 1)

    def test_contains(self):
        sl = SkipList(random=_always(0.9))
        sl.set(3, "three")
        self.assertIn(3, sl)
        self.assertNotIn(4, sl)

    def test_negative_and_zero_keys(self):
        sl = SkipList(random=_always(0.9))
        sl.set(-5, "neg")
        sl.set(0, "zero")
        self.assertEqual(sl.get(-5), "neg")
        self.assertEqual(sl.get(0), "zero")


class TestDelete(unittest.TestCase):
    def test_delete_existing(self):
        sl = SkipList(random=_always(0.9))
        sl.set("a", 1)
        self.assertTrue(sl.delete("a"))
        self.assertFalse("a" in sl)
        self.assertEqual(len(sl), 0)

    def test_delete_missing(self):
        sl = SkipList(random=_always(0.9))
        self.assertFalse(sl.delete("ghost"))

    def test_delete_keeps_others(self):
        sl = SkipList(random=_always(0.9))
        for i in range(5):
            sl.set(i, i * i)
        self.assertTrue(sl.delete(2))
        self.assertEqual(list(sl), [0, 1, 3, 4])
        self.assertEqual(sl.get(3), 9)

    def test_delete_from_empty(self):
        sl = SkipList(random=_always(0.9))
        self.assertFalse(sl.delete(1))


class TestOrdering(unittest.TestCase):
    def test_iteration_is_sorted(self):
        sl = SkipList(random=_always(0.9))
        for key in [5, 1, 4, 2, 3]:
            sl.set(key, key)
        self.assertEqual(list(sl), [1, 2, 3, 4, 5])

    def test_items_are_sorted_pairs(self):
        sl = SkipList(random=_always(0.9))
        sl.set("b", 2)
        sl.set("a", 1)
        sl.set("c", 3)
        self.assertEqual(list(sl.items()), [("a", 1), ("b", 2), ("c", 3)])

    def test_duplicate_set_does_not_change_order(self):
        sl = SkipList(random=_always(0.9))
        sl.set(2, "two")
        sl.set(1, "one")
        sl.set(2, "TWO")
        self.assertEqual(list(sl), [1, 2])
        self.assertEqual(sl.get(2), "TWO")


class TestRandomisedHeights(unittest.TestCase):
    def test_always_promote_reaches_max_level(self):
        # p=0.5 and a source that always returns 0.0 promotes every node to the
        # maximum height, exercising the multi-level insert path.
        sl = SkipList(max_level=4, p=0.5, random=_always(0.0))
        for i in range(10):
            sl.set(i, i)
        self.assertEqual(sl._level, 4)
        self.assertEqual(list(sl), list(range(10)))

    def test_never_promote_stays_single_level(self):
        sl = SkipList(max_level=4, p=0.5, random=_always(0.9))
        for i in range(10):
            sl.set(i, i)
        self.assertEqual(sl._level, 1)
        self.assertEqual(list(sl), list(range(10)))

    def test_level_shrinks_after_deleting_high_nodes(self):
        sl = SkipList(max_level=4, p=0.5, random=_always(0.0))
        for i in range(3):
            sl.set(i, i)
        self.assertEqual(sl._level, 4)
        for i in range(3):
            sl.delete(i)
        self.assertEqual(sl._level, 1)
        self.assertEqual(len(sl), 0)

    def test_mixed_heights_with_cycle(self):
        # A repeating pattern of draws gives a mixture of heights while staying
        # deterministic.
        sl = SkipList(max_level=4, p=0.5, random=_Counter([0.1, 0.9, 0.2, 0.8]))
        for i in range(20):
            sl.set(i, i)
        self.assertEqual(list(sl), list(range(20)))
        self.assertEqual(len(sl), 20)


class TestRepr(unittest.TestCase):
    def test_repr_reports_size_and_level(self):
        sl = SkipList(max_level=4, p=0.5, random=_always(0.9))
        sl.set("k", "v")
        self.assertEqual(repr(sl), "SkipList(size=1, level=1)")


class TestErrorType(unittest.TestCase):
    def test_error_is_exported(self):
        self.assertTrue(issubclass(SkipListError, Exception))


if __name__ == "__main__":
    unittest.main()
