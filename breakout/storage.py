"""Local high-score persistence for Breakout.

Kept free of curses so the pure-logic tests can inject a temp path and never
touch the user's real high-score file.
"""

from __future__ import annotations

import os


def default_highscore_path() -> str:
    """Return the default location for the persisted high score."""
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(base, "breakout", "highscore.txt")


class HighScoreStore:
    """Read/write a single integer high score to a plain-text file."""

    def __init__(self, path=None):
        self.path = path if path is not None else default_highscore_path()

    def load(self) -> int:
        """Return the stored high score, or 0 if missing/unreadable."""
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return int(fh.read().strip())
        except (OSError, ValueError):
            return 0

    def save(self, score: int) -> bool:
        """Persist *score*. Returns True on success, False on failure."""
        try:
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                fh.write(str(int(score)))
            return True
        except OSError:
            return False
