"""Pure game logic for Breakout — no curses, no terminal I/O, no files.

This module is intentionally free of every external dependency so a later test
node can drive it deterministically. All state lives in :class:`GameState`;
:meth:`GameState.update` advances the simulation one frame given a time delta
and the current inputs. The curses front-end (:mod:`breakout.ui`) is only
responsible for drawing and for translating key presses into these inputs.

Coordinate system: terminal *cells*. ``x`` ranges over ``[0, BOARD_W)`` and
``y`` over ``[0, BOARD_H)``, with ``(0, 0)`` at the top-left. The brick field
occupies the top rows, the paddle sits near the bottom, and the ball is a
single point rendered as one cell.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

# --------------------------------------------------------------------------- #
# Board geometry (terminal cells)
# --------------------------------------------------------------------------- #
BOARD_W = 60             # play-field width
BOARD_H = 22             # play-field height

# Paddle
PADDLE_W = 9             # paddle width in cells
PADDLE_Y = BOARD_H - 2   # row the paddle occupies (its only row)

# Ball
BALL_SPEED_INIT = 18.0   # cells / second at serve
BALL_SPEED_MAX = 34.0    # hard speed cap
BALL_SPEED_STEP = 0.55   # speed gained per paddle/brick hit
MAX_BOUNCE_ANGLE = math.radians(60)  # max deflection off the paddle centre
LAUNCH_ANGLE = math.radians(25)       # serve angle measured off vertical

# Paddle movement
PADDLE_SPEED = 46.0      # cells / second

# Brick field
BRICK_W = 4              # width of one brick in cells
BRICK_H = 1              # height of one brick in cells
BRICK_TOP = 1            # first row of the brick field
BRICK_ROWS = 5
BRICK_COLS = BOARD_W // BRICK_W   # 15 columns -> 75 bricks

# Brick colour index per row (row 0 = top). Indexes into the UI colour table.
BRICK_COLORS = (1, 2, 3, 4, 5)

# Collision substep size — keeps the fast ball from tunnelling through cells.
_SUBSTEP = 0.45


def points_for_row(row: int) -> int:
    """Score awarded for clearing a brick in *row* (top rows worth more)."""
    return (BRICK_ROWS - row) * 10


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# --------------------------------------------------------------------------- #
# Brick
# --------------------------------------------------------------------------- #
@dataclass
class Brick:
    col: int
    row: int
    color: int
    points: int
    alive: bool = True


# --------------------------------------------------------------------------- #
# Game state
# --------------------------------------------------------------------------- #
@dataclass
class GameState:
    """Complete mutable state of one game of Breakout."""

    # Per-frame inputs (set by the UI before calling update()).
    left: bool = False
    right: bool = False
    launch: bool = False

    # Paddle (x = left edge).
    paddle_x: float = (BOARD_W - PADDLE_W) / 2.0

    # Ball (position + unit direction + scalar speed).
    ball_x: float = 0.0
    ball_y: float = 0.0
    ball_dx: float = 0.0
    ball_dy: float = 0.0
    ball_speed: float = BALL_SPEED_INIT

    # Brick field: bricks[row][col] is a Brick or None once cleared.
    bricks: List[List[Optional[Brick]]] = field(default_factory=list)
    bricks_remaining: int = 0

    # Score / lives.
    score: int = 0
    lives: int = 3
    high_score: int = 0

    # Status: 'serve' | 'playing' | 'won' | 'lost'
    status: str = "serve"
    message: str = ""            # transient line for the UI to display

    serve_index: int = 0         # alternates the launch direction

    def __post_init__(self):
        if not self.bricks:
            self.new_game(self.high_score)

    # -- reset helpers ----------------------------------------------------- #
    def _build_bricks(self) -> None:
        self.bricks = []
        self.bricks_remaining = 0
        for row in range(BRICK_ROWS):
            line: List[Optional[Brick]] = []
            for col in range(BRICK_COLS):
                line.append(Brick(col, row, BRICK_COLORS[row], points_for_row(row)))
            self.bricks.append(line)
            self.bricks_remaining += BRICK_COLS

    def _place_ball_on_paddle(self) -> None:
        self.ball_x = self.paddle_x + (PADDLE_W / 2.0) - 0.5
        self.ball_y = float(PADDLE_Y - 1)
        self.ball_dx = 0.0
        self.ball_dy = 0.0

    def new_game(self, high_score: Optional[int] = None) -> None:
        """Reset to a brand-new game: fresh bricks, three lives, zero score."""
        if high_score is not None:
            self.high_score = high_score
        self.score = 0
        self.lives = 3
        self.status = "serve"
        self.message = "Press SPACE to serve"
        self.serve_index = 0
        self.paddle_x = (BOARD_W - PADDLE_W) / 2.0
        self.ball_speed = BALL_SPEED_INIT
        self._build_bricks()
        self._place_ball_on_paddle()

    def _lose_life(self) -> None:
        self.lives -= 1
        self.ball_speed = BALL_SPEED_INIT
        if self.lives <= 0:
            self.status = "lost"
            self.message = "GAME OVER"
        else:
            self.status = "serve"
            self.message = "Life lost — press SPACE to serve"
        self._place_ball_on_paddle()

    # -- input ------------------------------------------------------------- #
    def launch_ball(self) -> None:
        """Launch the ball off the paddle while serving."""
        if self.status != "serve":
            return
        self.status = "playing"
        self.message = ""
        sign = 1.0 if self.serve_index % 2 == 0 else -1.0
        self.serve_index += 1
        self.ball_dx = sign * math.sin(LAUNCH_ANGLE)
        self.ball_dy = -math.cos(LAUNCH_ANGLE)

    # -- simulation -------------------------------------------------------- #
    def update(self, dt: float) -> None:
        """Advance the simulation by *dt* seconds using the stored inputs."""
        dt = clamp(dt, 0.0, 0.05)

        # Paddle movement (left wins if both are somehow held).
        if self.left and not self.right:
            self.paddle_x -= PADDLE_SPEED * dt
        elif self.right and not self.left:
            self.paddle_x += PADDLE_SPEED * dt
        self.paddle_x = clamp(self.paddle_x, 0.0, BOARD_W - PADDLE_W)

        # Launch request (edge-triggered by the UI).
        if self.launch:
            self.launch_ball()

        # While serving the ball rides the paddle.
        if self.status == "serve":
            self._place_ball_on_paddle()
            return

        if self.status != "playing":
            return

        # Move the ball in small substeps so it can't tunnel through a cell.
        remaining = self.ball_speed * dt
        while remaining > 0.0 and self.status == "playing":
            step = min(remaining, _SUBSTEP)
            remaining -= step
            self.ball_x += self.ball_dx * step
            self.ball_y += self.ball_dy * step
            self._collide()

    # -- collisions -------------------------------------------------------- #
    def _collide(self) -> None:
        # Side walls.
        if self.ball_x < 0.0:
            self.ball_x = 0.0
            self.ball_dx = abs(self.ball_dx)
        elif self.ball_x > BOARD_W - 1.0:
            self.ball_x = BOARD_W - 1.0
            self.ball_dx = -abs(self.ball_dx)

        # Ceiling.
        if self.ball_y <= 0.0:
            self.ball_y = 0.0
            self.ball_dy = abs(self.ball_dy)

        # Paddle bounce (only while travelling down, inside the paddle row).
        if (
            self.ball_dy > 0.0
            and PADDLE_Y <= self.ball_y < PADDLE_Y + 1.0
            and self.paddle_x <= self.ball_x < self.paddle_x + PADDLE_W
        ):
            self._bounce_off_paddle()
            return

        # Missed the paddle entirely — fell past it.
        if self.ball_y >= PADDLE_Y + 1.0:
            self._lose_life()
            return

        # Bricks.
        self._collide_bricks()

    def _bounce_off_paddle(self) -> None:
        self.ball_y = float(PADDLE_Y) - 0.001
        centre = self.paddle_x + PADDLE_W / 2.0
        offset = (self.ball_x - centre) / (PADDLE_W / 2.0)
        offset = clamp(offset, -1.0, 1.0)
        angle = offset * MAX_BOUNCE_ANGLE
        self.ball_speed = min(BALL_SPEED_MAX, self.ball_speed + BALL_SPEED_STEP)
        self.ball_dx = math.sin(angle)
        self.ball_dy = -math.cos(angle)

    def _collide_bricks(self) -> None:
        col = int(self.ball_x // BRICK_W)
        row = int((self.ball_y - BRICK_TOP) // BRICK_H)
        if not (0 <= row < BRICK_ROWS and 0 <= col < BRICK_COLS):
            return
        brick = self.bricks[row][col]
        if brick is None or not brick.alive:
            return

        brick.alive = False
        self.bricks[row][col] = None
        self.bricks_remaining -= 1
        self.score += brick.points
        self.ball_speed = min(BALL_SPEED_MAX, self.ball_speed + BALL_SPEED_STEP)

        left = col * BRICK_W
        right = left + BRICK_W
        top = BRICK_TOP + row * BRICK_H
        bottom = top + BRICK_H

        # Reflect off the nearest face. Bricks are short and wide, so a hit
        # from above/below flips vy and a hit from the side flips vx.
        d_top = abs(self.ball_y - top)
        d_bottom = abs(self.ball_y - bottom)
        d_left = abs(self.ball_x - left)
        d_right = abs(self.ball_x - right)
        nearest = min(d_top, d_bottom, d_left, d_right)
        if nearest == d_top or nearest == d_bottom:
            self.ball_dy = -self.ball_dy
        else:
            self.ball_dx = -self.ball_dx

        if self.bricks_remaining <= 0:
            self.status = "won"
            self.message = "YOU WIN!"
