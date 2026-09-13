"""curses front-end for Breakout.

All game rules live in :mod:`breakout.game`; this module only renders the
state and translates key presses into the per-frame inputs the game expects.
The ``curses`` module is imported lazily so the game prints a helpful message
on Windows when ``windows-curses`` is not installed.
"""

from __future__ import annotations

import time

from . import game as G
from .storage import HighScoreStore

TARGET_FPS = 60.0
FRAME_TIME = 1.0 / TARGET_FPS

# Layout (in screen rows/cols, around the BOARD_W x BOARD_H play field).
MARGIN_X = 2
MARGIN_Y = 2


def _required_size() -> tuple:
    """Minimum terminal size needed to draw everything."""
    cols = MARGIN_X * 2 + G.BOARD_W + 2
    lines = MARGIN_Y + G.BOARD_H + 3
    return lines, cols


def main() -> None:
    """Entry point: bootstrap curses (or explain the Windows fallback)."""
    try:
        import curses
    except ImportError:
        print("ERROR: the 'curses' module is not available.")
        print("This is expected on Windows. Install the fallback with:")
        print("    pip install windows-curses")
        print("then run the game again.")
        raise SystemExit(1)
    try:
        curses.wrapper(lambda stdscr: _run(stdscr, curses))
    except KeyboardInterrupt:
        pass


# --------------------------------------------------------------------------- #
# Colour setup
# --------------------------------------------------------------------------- #
def _init_colors(curses) -> None:
    curses.start_color()
    curses.use_default_colors()
    # 1..5: solid brick colours (coloured background, black foreground).
    brick_colors = (
        curses.COLOR_RED,
        curses.COLOR_YELLOW,
        curses.COLOR_GREEN,
        curses.COLOR_CYAN,
        curses.COLOR_MAGENTA,
    )
    for idx, color in enumerate(brick_colors, start=1):
        curses.init_pair(idx, curses.COLOR_BLACK, color)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)   # paddle
    curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # ball
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)   # border/text
    curses.init_pair(9, curses.COLOR_CYAN, curses.COLOR_BLACK)    # status line
    curses.init_pair(10, curses.COLOR_RED, curses.COLOR_BLACK)    # game over
    curses.init_pair(11, curses.COLOR_GREEN, curses.COLOR_BLACK)  # win


# --------------------------------------------------------------------------- #
# Drawing
# --------------------------------------------------------------------------- #
def _center(width: int, text: str) -> int:
    return max(0, (width - len(text)) // 2)


def _draw(stdscr, curses, state: "G.GameState", paused: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    # Status line.
    status = "SCORE {:>5}   HIGH {:>5}   LIVES {}".format(
        state.score, max(state.high_score, state.score), state.lives
    )
    try:
        stdscr.addstr(0, MARGIN_X, status, curses.color_pair(8) | curses.A_BOLD)
    except curses.error:
        pass

    # Border around the play field.
    left = MARGIN_X - 1
    top = MARGIN_Y - 1
    try:
        stdscr.addstr(top, left, "┌" + "─" * G.BOARD_W + "┐", curses.color_pair(8))
        for y in range(1, G.BOARD_H + 1):
            stdscr.addstr(top + y, left, "│", curses.color_pair(8))
            stdscr.addstr(top + y, left + G.BOARD_W + 1, "│", curses.color_pair(8))
        stdscr.addstr(top + G.BOARD_H + 1, left, "└" + "─" * G.BOARD_W + "┘", curses.color_pair(8))
    except curses.error:
        pass

    # Bricks.
    for row in range(G.BRICK_ROWS):
        for col in range(G.BRICK_COLS):
            brick = state.bricks[row][col]
            if brick is not None and brick.alive:
                y = MARGIN_Y + G.BRICK_TOP + row * G.BRICK_H
                x = MARGIN_X + col * G.BRICK_W
                try:
                    stdscr.addstr(y, x, " " * G.BRICK_W, curses.color_pair(brick.color))
                except curses.error:
                    pass

    # Paddle.
    px = int(state.paddle_x)
    try:
        stdscr.addstr(
            MARGIN_Y + G.PADDLE_Y,
            MARGIN_X + px,
            " " * G.PADDLE_W,
            curses.color_pair(6) | curses.A_BOLD,
        )
    except curses.error:
        pass

    # Ball.
    try:
        stdscr.addstr(
            MARGIN_Y + int(state.ball_y),
            MARGIN_X + int(state.ball_x),
            "O",
            curses.color_pair(7) | curses.A_BOLD,
        )
    except curses.error:
        pass

    # Overlay messages in the middle of the field.
    message = None
    pair = curses.color_pair(9) | curses.A_BOLD
    if paused:
        message = "PAUSED — press P to resume"
    elif state.status == "serve":
        message = state.message or "Press SPACE to serve"
    elif state.status == "won":
        message = "YOU WIN!  Score {} — press R to play again".format(state.score)
        pair = curses.color_pair(11) | curses.A_BOLD
    elif state.status == "lost":
        message = "GAME OVER  Score {} — press R to play again".format(state.score)
        pair = curses.color_pair(10) | curses.A_BOLD

    if message:
        my = MARGIN_Y + G.BOARD_H // 2 - 1
        mx = MARGIN_X + _center(G.BOARD_W, message)
        try:
            stdscr.addstr(my, mx, message, pair)
        except curses.error:
            pass

    # Help line at the very bottom.
    help_text = "←/→ or A/D move   SPACE serve   P pause   R restart   Q quit"
    hy = height - 1
    try:
        stdscr.addstr(hy, MARGIN_X, help_text, curses.color_pair(8))
    except curses.error:
        pass


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def _run(stdscr, curses) -> None:
    req_lines, req_cols = _required_size()
    lines, cols = stdscr.getmaxyx()
    if lines < req_lines or cols < req_cols:
        msg = "Terminal too small (need {}x{}). Resize and re-run.".format(req_cols, req_lines)
        stdscr.addstr(0, 0, msg[:cols - 1])
        stdscr.refresh()
        time.sleep(2)
        return

    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(True)
    _init_colors(curses)

    key_left = {curses.KEY_LEFT, ord("a"), ord("A")}
    key_right = {curses.KEY_RIGHT, ord("d"), ord("D")}
    key_launch = {curses.KEY_UP, ord(" "), ord("\n"), 13}
    key_quit = {ord("q"), ord("Q"), 27}
    key_restart = {ord("r"), ord("R")}
    key_pause = {ord("p"), ord("P")}

    store = HighScoreStore()
    high = store.load()
    state = G.GameState(high_score=high)

    held_dir = 0        # -1 left, 0 stop, +1 right
    since_key = 0       # frames since the last movement key event
    paused = False
    prev_launch = False
    prev_restart = False
    prev_pause = False

    last = time.monotonic()

    while True:
        ch = stdscr.getch()

        if ch in key_quit:
            break

        # Restart (edge-triggered).
        if ch in key_restart and not prev_restart:
            state.new_game(high_score=store.load())
            held_dir = 0
            since_key = 0
            paused = False
        prev_restart = ch in key_restart

        # Pause toggle (edge-triggered).
        if ch in key_pause and not prev_pause:
            paused = not paused
        prev_pause = ch in key_pause

        # Smooth held-key movement. We keep the last direction for a couple of
        # frames after the most recent key event so the terminal's auto-repeat
        # gap doesn't cause a visible stutter, but we still stop promptly on
        # release.
        if ch in key_left:
            held_dir = -1
            since_key = 0
        elif ch in key_right:
            held_dir = 1
            since_key = 0
        elif ch == -1:
            since_key += 1
            if since_key > 2:
                held_dir = 0
        else:
            since_key = 0

        now = time.monotonic()
        dt = min(now - last, 0.05)
        last = now

        launch_pressed = ch in key_launch
        if not paused:
            state.left = held_dir < 0
            state.right = held_dir > 0
            state.launch = launch_pressed and not prev_launch
            state.update(dt)
        prev_launch = launch_pressed

        # Persist a new high score as soon as a game finishes.
        if state.status in ("won", "lost") and state.score > state.high_score:
            state.high_score = state.score
            store.save(state.high_score)

        _draw(stdscr, curses, state, paused)
        stdscr.refresh()

        elapsed = time.monotonic() - now
        if elapsed < FRAME_TIME:
            time.sleep(FRAME_TIME - elapsed)
