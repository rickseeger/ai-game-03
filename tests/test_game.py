"""Automated tests for Breakout's pure game logic (:mod:`breakout.game`).

These run headless — no curses, no terminal — and drive :class:`GameState`
directly so every collision, scoring, life, and win/loss path is exercised
deterministically.

Run with either of (from the repository root):

    python3 -m unittest discover -s tests -t . -v
    python3 -m pytest -v
"""

import unittest

from breakout import game as G
from breakout.game import Brick, GameState


def _playing():
    """A fresh GameState moved into the 'playing' status for simulation tests."""
    state = GameState()
    state.status = "playing"
    return state


def _ball(state, x, y, dx=0.0, dy=1.0):
    """Place the ball at an explicit position and point it in a direction."""
    state.ball_x = float(x)
    state.ball_y = float(y)
    state.ball_dx = float(dx)
    state.ball_dy = float(dy)


class InitialStateTests(unittest.TestCase):
    def test_new_game_builds_full_brick_field(self):
        state = GameState()
        self.assertEqual(state.bricks_remaining, G.BRICK_ROWS * G.BRICK_COLS)
        self.assertEqual(state.bricks_remaining, 75)
        self.assertEqual(len(state.bricks), G.BRICK_ROWS)
        for row in state.bricks:
            self.assertEqual(len(row), G.BRICK_COLS)
            for brick in row:
                self.assertIsNotNone(brick)
                self.assertTrue(brick.alive)

    def test_new_game_starts_in_serve_with_three_lives(self):
        state = GameState()
        self.assertEqual(state.status, "serve")
        self.assertEqual(state.lives, 3)
        self.assertEqual(state.score, 0)

    def test_launch_ball_starts_play_and_points_up(self):
        state = GameState()
        state.launch_ball()
        self.assertEqual(state.status, "playing")
        self.assertLess(state.ball_dy, 0.0)
        self.assertNotEqual(state.ball_dx, 0.0)


class WallCollisionTests(unittest.TestCase):
    def test_left_wall_bounce(self):
        state = _playing()
        _ball(state, x=-0.3, y=10.0, dx=-1.0, dy=0.5)
        state._collide()
        self.assertEqual(state.ball_x, 0.0)
        self.assertGreater(state.ball_dx, 0.0)   # reflected to the right

    def test_right_wall_bounce(self):
        state = _playing()
        _ball(state, x=G.BOARD_W - 0.3, y=10.0, dx=1.0, dy=0.5)
        state._collide()
        self.assertEqual(state.ball_x, G.BOARD_W - 1.0)
        self.assertLess(state.ball_dx, 0.0)      # reflected to the left

    def test_ceiling_bounce(self):
        state = _playing()
        _ball(state, x=30.0, y=-0.2, dx=0.3, dy=-1.0)
        state._collide()
        self.assertEqual(state.ball_y, 0.0)
        self.assertGreater(state.ball_dy, 0.0)   # reflected downward


class PaddleCollisionTests(unittest.TestCase):
    def test_centre_hit_returns_vertical(self):
        state = _playing()
        centre = state.paddle_x + G.PADDLE_W / 2.0
        _ball(state, x=centre, y=G.PADDLE_Y + 0.5, dy=1.0)
        state._collide()
        self.assertAlmostEqual(state.ball_dx, 0.0, places=9)
        self.assertLess(state.ball_dy, 0.0)       # reflected upward
        self.assertAlmostEqual(state.ball_y, G.PADDLE_Y - 0.001, places=6)

    def test_paddle_hit_increases_speed(self):
        state = _playing()
        centre = state.paddle_x + G.PADDLE_W / 2.0
        _ball(state, x=centre, y=G.PADDLE_Y + 0.5, dy=1.0)
        before = state.ball_speed
        state._collide()
        self.assertEqual(state.ball_speed, before + G.BALL_SPEED_STEP)

    def test_paddle_hit_speed_caps_at_maximum(self):
        state = _playing()
        state.ball_speed = G.BALL_SPEED_MAX
        _ball(state, x=state.paddle_x + G.PADDLE_W / 2.0, y=G.PADDLE_Y + 0.5, dy=1.0)
        state._collide()
        self.assertEqual(state.ball_speed, G.BALL_SPEED_MAX)

    def test_right_edge_hit_launches_steeply_right(self):
        state = _playing()
        _ball(state, x=state.paddle_x + G.PADDLE_W - 0.01, y=G.PADDLE_Y + 0.5, dy=1.0)
        state._collide()
        self.assertGreater(state.ball_dx, 0.8)    # steep rightward angle
        self.assertLess(state.ball_dy, 0.0)       # and upward

    def test_left_edge_hit_launches_steeply_left(self):
        state = _playing()
        _ball(state, x=state.paddle_x + 0.01, y=G.PADDLE_Y + 0.5, dy=1.0)
        state._collide()
        self.assertLess(state.ball_dx, -0.8)      # steep leftward angle
        self.assertLess(state.ball_dy, 0.0)

    def test_angle_scales_with_hit_offset(self):
        centre = _playing()
        _ball(centre, x=centre.paddle_x + G.PADDLE_W / 2.0, y=G.PADDLE_Y + 0.5, dy=1.0)
        centre._collide()

        edge = _playing()
        _ball(edge, x=edge.paddle_x + G.PADDLE_W - 0.01, y=G.PADDLE_Y + 0.5, dy=1.0)
        edge._collide()

        # An off-centre hit deflects more sharply than a dead-centre hit.
        self.assertGreater(abs(edge.ball_dx), abs(centre.ball_dx))


class BrickCollisionTests(unittest.TestCase):
    def test_brick_hit_scores_and_removes_brick(self):
        state = _playing()
        _ball(state, x=2.0, y=1.5, dy=1.0)   # top-left brick (row 0 -> 50 pts)
        before = state.bricks_remaining
        state._collide()
        self.assertEqual(state.score, 50)
        self.assertEqual(state.bricks_remaining, before - 1)
        self.assertIsNone(state.bricks[0][0])

    def test_brick_hit_increases_speed(self):
        state = _playing()
        _ball(state, x=2.0, y=1.5, dy=1.0)
        before = state.ball_speed
        state._collide()
        self.assertEqual(state.ball_speed, before + G.BALL_SPEED_STEP)

    def test_points_for_row_decreases_down_the_field(self):
        self.assertEqual(
            [G.points_for_row(r) for r in range(G.BRICK_ROWS)],
            [50, 40, 30, 20, 10],
        )

    def test_bottom_row_brick_scores_ten(self):
        state = _playing()
        row = G.BRICK_ROWS - 1
        _ball(state, x=2.0, y=G.BRICK_TOP + row + 0.5, dy=1.0)
        state._collide()
        self.assertEqual(state.score, 10)


class LifeAndWinLossTests(unittest.TestCase):
    @staticmethod
    def _drop_ball(state):
        state.status = "playing"
        _ball(state, x=30.0, y=G.PADDLE_Y + 1.0, dy=1.0)

    def test_missing_ball_costs_a_life(self):
        state = _playing()
        self._drop_ball(state)
        state._collide()
        self.assertEqual(state.lives, 2)
        self.assertEqual(state.status, "serve")

    def test_three_misses_lose_the_game(self):
        state = _playing()
        for _ in range(3):
            self._drop_ball(state)
            state._collide()
        self.assertEqual(state.lives, 0)
        self.assertEqual(state.status, "lost")
        self.assertEqual(state.message, "GAME OVER")

    def test_clearing_last_brick_wins(self):
        state = _playing()
        # Clear every brick except the bottom-right one.
        for row in range(G.BRICK_ROWS):
            for col in range(G.BRICK_COLS):
                state.bricks[row][col] = None
        state.bricks_remaining = 1
        last_col = G.BRICK_COLS - 1
        last_row = G.BRICK_ROWS - 1
        state.bricks[last_row][last_col] = Brick(
            last_col, last_row, 5, G.points_for_row(last_row)
        )
        _ball(
            state,
            x=last_col * G.BRICK_W + 2.0,
            y=G.BRICK_TOP + last_row + 0.5,
            dy=1.0,
        )
        state._collide()
        self.assertEqual(state.bricks_remaining, 0)
        self.assertEqual(state.status, "won")
        self.assertEqual(state.message, "YOU WIN!")


class PaddleMovementTests(unittest.TestCase):
    def test_paddle_moves_right(self):
        state = _playing()
        state.right = True
        start = state.paddle_x
        state.update(0.05)
        self.assertGreater(state.paddle_x, start)

    def test_paddle_clamps_to_right_edge(self):
        state = _playing()
        state.right = True
        for _ in range(200):
            state.update(0.05)
        self.assertEqual(state.paddle_x, G.BOARD_W - G.PADDLE_W)

    def test_paddle_clamps_to_left_edge(self):
        state = _playing()
        state.left = True
        for _ in range(200):
            state.update(0.05)
        self.assertEqual(state.paddle_x, 0.0)


class UpdateIntegrationTests(unittest.TestCase):
    def test_launch_via_update_moves_ball_up(self):
        state = GameState()
        self.assertEqual(state.status, "serve")
        state.launch = True
        state.update(0.016)
        self.assertEqual(state.status, "playing")
        self.assertLess(state.ball_y, G.PADDLE_Y - 1.0)  # left the paddle

    def test_update_drives_ball_into_brick(self):
        state = _playing()
        _ball(state, x=2.0, y=1.6, dy=-1.0)   # moving up into brick row 0
        state.update(0.02)
        self.assertEqual(state.score, 50)
        self.assertEqual(state.bricks_remaining, G.BRICK_ROWS * G.BRICK_COLS - 1)


if __name__ == "__main__":
    unittest.main()
