"""Automated tests for Breakout's high-score persistence (breakout.storage)."""

import os
import tempfile
import unittest

from breakout.storage import HighScoreStore


class HighScoreStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "highscore.txt")

    def test_missing_file_loads_zero(self):
        store = HighScoreStore(path=self.path)
        self.assertEqual(store.load(), 0)

    def test_save_then_load_round_trip(self):
        store = HighScoreStore(path=self.path)
        self.assertTrue(store.save(1234))
        self.assertEqual(store.load(), 1234)

    def test_overwrite_updates_score(self):
        store = HighScoreStore(path=self.path)
        store.save(100)
        store.save(2500)
        self.assertEqual(store.load(), 2500)

    def test_corrupt_file_loads_zero(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("not-a-number")
        store = HighScoreStore(path=self.path)
        self.assertEqual(store.load(), 0)

    def test_save_creates_missing_directories(self):
        deep = os.path.join(self._tmp.name, "a", "b", "c", "highscore.txt")
        store = HighScoreStore(path=deep)
        self.assertTrue(store.save(7))
        self.assertEqual(store.load(), 7)

    def test_save_zero_is_preserved(self):
        store = HighScoreStore(path=self.path)
        store.save(42)
        store.save(0)
        self.assertEqual(store.load(), 0)


if __name__ == "__main__":
    unittest.main()
