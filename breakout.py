#!/usr/bin/env python3
"""Breakout — a tiny, colourful Breakout game for the terminal.

Run it with:

    python3 breakout.py          # Linux / macOS (stdlib curses)

On Windows the stdlib lacks ``curses``; install the fallback first:

    pip install windows-curses
    python breakout.py

All game rules live in ``breakout/game.py`` (pure logic, no curses); this file
is only the entry point.
"""

from breakout.ui import main

if __name__ == "__main__":
    main()
