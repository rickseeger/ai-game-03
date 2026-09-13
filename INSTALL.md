# Breakout — Install & Run

Reproducible install/run instructions for the committed Breakout game
(`breakout/game.py` + `breakout/storage.py` + the `curses` renderer in
`breakout/ui.py`), for both Linux/macOS and Windows.

One codebase, two platforms:

* **Linux / macOS** — the `curses` module ships with the standard library, so
  there are **no third-party dependencies** to install.
* **Windows** — the standard library does *not* include `curses`, so the
  `windows-curses` package provides it. It is installed automatically from
  `requirements.txt`.

The game itself is pure Python (no compiled extensions). It needs a terminal
of at least **66 columns x 27 rows**.

---

## Requirements

* Python **3.10 or newer** (3.11 / 3.12 recommended; they have the widest
  `windows-curses` wheel coverage on Windows). The code is compatible with
  3.7+, but use 3.10+ for a clean, supported baseline.
* A terminal (real TTY) of at least 66x27 cells. Works in GNOME Terminal,
  Konsole, iTerm2, Windows Terminal, and most others. It will **not** run
  correctly inside an IDE output pane that is not a real terminal.
* Git (to clone the repository), or a downloaded source archive.

---

## Linux / macOS

Run these commands in a terminal, in order:

```bash
# 1. Get the code
git clone https://github.com/rickseeger/ai-game-03.git
cd ai-game-03

# 2. (Recommended) create and activate an isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies.
#    On Linux/macOS this is a no-op: curses is already in the standard
#    library, and the windows-curses line in requirements.txt is gated to
#    Windows by a platform marker, so pip simply ignores it.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Run the game
python breakout.py
#   ...or, from anywhere inside the checkout:
python -m breakout
```

You should immediately see a coloured Breakout board with the status line
`SCORE 0  HIGH 0  LIVES 3`, a field of bricks, a paddle, and a ball.

### Controls

| Key | Action |
| --- | --- |
| Left / Right arrows (or `A` / `D`) | Move the paddle (hold to keep moving) |
| Space / Up arrow | Serve the ball |
| `P` | Pause / resume |
| `R` | Restart |
| `Q` | Quit |

### Run the tests (Linux/macOS)

The test suite is pure `unittest` (standard library) and runs headless — no
terminal, no extra dependencies:

```bash
# From the repository root, with or without a venv:
python -m unittest discover -s tests -t . -v
```

Expected result: `Ran 30 tests ... OK` (30 tests, 0 failures).

pytest works too, if you prefer it:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

Expected result: `30 passed`.

---

## Windows

Use **PowerShell** (or cmd — the commands are identical). Open a terminal and
run:

```powershell
# 1. Get the code
git clone https://github.com/rickseeger/ai-game-03.git
cd ai-game-03

# 2. (Recommended) create and activate an isolated virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies. This is the step that matters on Windows:
#    it pulls in `windows-curses`, which supplies the `curses` module the
#    Windows standard library does not provide.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Run the game
python breakout.py
#   ...or, from anywhere inside the checkout:
python -m breakout
```

`requirements.txt` pins the Windows fallback with a platform marker, so the
same file works unchanged on both platforms:

```
windows-curses>=2.3 ; platform_system == "Windows"
```

### Windows troubleshooting

If you skip step 3 and run `python breakout.py` first, the game does not crash
confusingly — it prints a clear message and exits:

```
ERROR: the 'curses' module is not available.
This is expected on Windows. Install the fallback with:
    pip install windows-curses
then run the game again.
```

Just run `python -m pip install -r requirements.txt` (or
`pip install windows-curses`) and start again.

If `pip install windows-curses` reports **no matching wheel for your Python
version**, install a Python version that has a `windows-curses` wheel
(3.10–3.12 are reliably published) or upgrade the package, then retry.

### Run the tests (Windows)

The suite is headless and dependency-free, so it runs identically on Windows:

```powershell
python -m unittest discover -s tests -t . -v
```

Expected result: `Ran 30 tests ... OK`.

---

## High score

The high score is persisted to a plain-text file:

```
~/.local/share/breakout/highscore.txt        (Linux / macOS)
C:\Users\<you>\.local\share\breakout\highscore.txt   (Windows)
```

* On Linux/macOS the base directory can be overridden with the
  `XDG_DATA_HOME` environment variable.
* On Windows, the code uses the same `~/.local/share/breakout/highscore.txt`
  path (via `os.path.expanduser("~")`), which resolves under the user's home
  directory. It survives restarts; the file is created automatically on the
  first save.

---

## Verifying a clean install (what was smoke-tested)

This document was verified from a clean `python3 -m venv` on Linux:

1. `python -m pip install -r requirements.txt` — completes; `windows-curses`
   is skipped (`markers 'platform_system == "Windows"' don't match`).
2. `python breakout.py` — launches the curses UI, draws the board, responds to
   `Q` and exits cleanly (exit code 0).
3. `python -m unittest discover -s tests -t . -v` — `Ran 30 tests ... OK`.
4. The Windows `ImportError` fallback prints exactly the message shown above
   and exits with code 1 when `curses` is unavailable.
