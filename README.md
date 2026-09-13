# Breakout

A tiny, deliberately simple Breakout game that renders clean colour ASCII in
the terminal. One codebase runs on Linux/macOS (stdlib `curses`) and on
Windows (via the `windows-curses` fallback).

See [INSTALL.md](INSTALL.md) for detailed, copy-paste install/run
instructions for both Linux/macOS and Windows.

## Run it

Linux / macOS:

    python3 breakout.py

Windows:

    pip install windows-curses
    python breakout.py

Alternatively, from anywhere inside the checkout:

    python3 -m breakout

## Controls

    Left / Right arrows  (or A / D)   move the paddle (hold to keep moving)
    Space / Up arrow                  serve the ball
    P                                 pause / resume
    R                                 restart
    Q                                 quit

## Rules

- Three lives. Clear every brick to win; miss the ball and you lose a life.
- The bounce angle off the paddle depends on where the ball hits it — hit near
  an edge for a steep angle, near the centre for a straight return.
- The ball speeds up a little on each paddle/brick hit, up to a cap.
- Top rows of bricks are worth more points.

## High score

The high score is written to a plain-text file at:

    ~/.local/share/breakout/highscore.txt

(override the base directory with the `XDG_DATA_HOME` environment variable).
It survives restarts.

## Layout

- `breakout/game.py` — pure game logic (no curses, no files). Unit-testable.
- `breakout/storage.py` — high-score persistence (injectable file path).
- `breakout/ui.py` — the `curses` renderer and input loop.
- `breakout.py` — entry point.
- `tests/` — the headless test suite (stdlib `unittest`, pytest-compatible).

## Tests

The test suite is pure `unittest` (standard library) and runs headless — no
terminal needed — so it passes straight from a clean checkout:

    python3 -m unittest discover -s tests -t . -v

pytest works too:

    pip install -r requirements-dev.txt
    python3 -m pytest -v

It covers the core logic: wall/ceiling/paddle/brick collisions, paddle-hit
angle response, scoring, life loss, win/lose detection, and high-score
load/save round-trip.
