# Breakout

A small, deliberately simple Breakout game that renders colourful ASCII in the
terminal. One codebase runs on Linux/macOS (stdlib `curses`) and on Windows
(via the `windows-curses` fallback). The game rules live in `breakout/game.py`
(pure logic — no terminal or file I/O), the renderer and input loop in
`breakout/ui.py`, and high-score persistence in `breakout/storage.py`.

See [INSTALL.md](INSTALL.md) for full, copy-paste install/run instructions for
both platforms. The short version:

Linux / macOS — no third-party dependencies (`curses` ships with Python):

    python3 breakout.py

Windows — install the fallback first:

    pip install -r requirements.txt
    python breakout.py

From anywhere inside the checkout you can also run:

    python -m breakout

The game needs a terminal of at least 66 columns x 27 rows.

## Controls

    Left / Right arrows  (or A / D)   move the paddle — hold to keep moving
    Space / Up / Enter                serve (launch) the ball
    P                                 pause / resume
    R                                 restart
    Q  (or Esc)                       quit

## Scoring

The brick field is 5 rows tall and 15 columns wide (75 bricks). Higher rows
are worth more points:

    Row 0 (top)     50 points
    Row 1           40 points
    Row 2           30 points
    Row 3           20 points
    Row 4 (bottom)  10 points

A cleared brick scores `(5 - row) x 10` points. The ball speeds up slightly on
every paddle or brick hit, up to a cap. The bounce angle off the paddle depends
on where the ball strikes it — dead centre returns it straight up, while an
edge hit sends it off at a steep angle (up to 60 degrees).

You start with three lives. If the ball falls past the paddle you lose a life;
clear all 75 bricks to win, or lose all three lives and it is game over.

## High score

The high score is saved to a plain-text file and survives restarts:

    ~/.local/share/breakout/highscore.txt

Set the `XDG_DATA_HOME` environment variable to relocate it (Linux/macOS).

The loop is simple: the stored high score is loaded when the game starts, and
it is written back whenever a game finishes — win or lose — with a score higher
than the previous best. The status line shows the higher of the stored high
score and your current score, so it updates live as you pass the old record.

## Tests

The test suite is headless — it drives the pure game logic directly, so it
needs no terminal and no third-party packages. Run it from the repository root:

    python3 -m unittest discover -s tests -t . -v

Expected: `Ran 30 tests ... OK` (30 tests, 0 failures).

pytest works too, if you prefer it:

    pip install -r requirements-dev.txt
    python3 -m pytest -v

The suite covers wall/ceiling/paddle/brick collisions, paddle-hit angle
response, scoring, life loss, win/lose detection, paddle movement and clamping,
and high-score load/save round-trips.

## Layout

    breakout/game.py      pure game logic — no curses, no files, unit-testable
    breakout/storage.py   high-score persistence (injectable file path)
    breakout/ui.py        the curses renderer and input loop
    breakout.py           entry point (python breakout.py)
    breakout/__main__.py  entry point for python -m breakout
    tests/                the headless test suite (stdlib unittest)
    INSTALL.md            detailed install/run instructions for both platforms
