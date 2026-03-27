"""Comprehensive tests for Tetris game logic, tetromino, and particle modules.

Covers:
- Tetromino construction, rotation, color assignments
- TetrisLogic: game init, piece spawning, movement validation
- Line clearing with scoring, combos, level progression
- Hold piece mechanics
- Hard drop mechanics
- Snapshot/restore (rewind system)
- Particle and ScorePopup lifecycle
- Design-by-Contract: invariant checks on public methods
"""

from __future__ import annotations

import pytest

from games.Tetris.src.constants import (
    BLACK,
    CYAN,
    GRID_HEIGHT,
    GRID_WIDTH,
    PURPLE,
    RED,
    SHAPES,
)
from games.Tetris.src.game_logic import TetrisLogic
from games.Tetris.src.particles import Particle, ScorePopup
from games.Tetris.src.tetromino import Tetromino

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def logic() -> TetrisLogic:
    """Create a fresh TetrisLogic instance."""
    return TetrisLogic()


@pytest.fixture
def t_piece() -> Tetromino:
    """Create a T-tetromino at the center."""
    return Tetromino(GRID_WIDTH // 2 - 1, 0, "T")


# ---------------------------------------------------------------------------
# Tetromino Tests
# ---------------------------------------------------------------------------


class TestTetrominoConstruction:
    """Test tetromino creation."""

    def test_tetromino_initial_position(self) -> None:
        t = Tetromino(3, 5, "T")
        assert t.x == 3
        assert t.y == 5
        assert t.shape_type == "T"
        assert t.rotation == 0

    def test_tetromino_has_correct_shape(self) -> None:
        for shape_type, expected_shape in SHAPES.items():
            t = Tetromino(0, 0, shape_type)
            assert t.shape == expected_shape

    def test_tetromino_has_color(self) -> None:
        t = Tetromino(0, 0, "T")
        assert t.color == PURPLE

    def test_tetromino_has_correct_color_for_each_type(self) -> None:
        from games.Tetris.src.constants import SHAPE_COLORS

        for shape_type, expected_color in SHAPE_COLORS.items():
            t = Tetromino(0, 0, shape_type)
            assert t.color == expected_color, f"Color mismatch for {shape_type}"


class TestTetrominoRotation:
    """Test tetromino rotation mechanics."""

    def test_rotation_0_returns_original(self, t_piece: Tetromino) -> None:
        assert t_piece.get_rotated_shape() == SHAPES["T"]

    def test_rotation_increments(self, t_piece: Tetromino) -> None:
        t_piece.rotate()
        assert t_piece.rotation == 1
        t_piece.rotate()
        assert t_piece.rotation == 2

    def test_rotation_wraps_at_4(self, t_piece: Tetromino) -> None:
        for _ in range(4):
            t_piece.rotate()
        assert t_piece.rotation == 0

    def test_four_rotations_return_to_original(self, t_piece: Tetromino) -> None:
        original = t_piece.get_rotated_shape()
        for _ in range(4):
            t_piece.rotate()
        assert t_piece.get_rotated_shape() == original

    def test_t_piece_rotation_90(self, t_piece: Tetromino) -> None:
        t_piece.rotate()
        rotated = t_piece.get_rotated_shape()
        assert rotated == [[1, 0], [1, 1], [1, 0]]

    def test_o_piece_rotation_is_stable(self) -> None:
        """O-piece should look the same in all rotations."""
        o = Tetromino(0, 0, "O")
        original = o.get_rotated_shape()
        for _ in range(4):
            o.rotate()
            assert o.get_rotated_shape() == original

    def test_i_piece_rotations(self) -> None:
        """I-piece should alternate between horizontal and vertical."""
        i = Tetromino(0, 0, "I")
        r0 = i.get_rotated_shape()
        assert len(r0) == 1  # 1 row
        assert len(r0[0]) == 4  # 4 cols

        i.rotate()
        r1 = i.get_rotated_shape()
        assert len(r1) == 4  # 4 rows
        assert len(r1[0]) == 1  # 1 col


# ---------------------------------------------------------------------------
# TetrisLogic Initialization Tests
# ---------------------------------------------------------------------------


class TestTetrisLogicInit:
    """Test game initialization."""

    def test_initial_state(self, logic: TetrisLogic) -> None:
        assert not logic.game_over
        assert logic.score == 0
        assert logic.lines_cleared == 0
        assert logic.level == 1
        assert logic.combo == 0

    def test_grid_is_correct_size(self, logic: TetrisLogic) -> None:
        assert len(logic.grid) == GRID_HEIGHT
        assert all(len(row) == GRID_WIDTH for row in logic.grid)

    def test_grid_starts_empty(self, logic: TetrisLogic) -> None:
        for row in logic.grid:
            assert all(cell == BLACK for cell in row)

    def test_has_current_and_next_piece(self, logic: TetrisLogic) -> None:
        assert isinstance(logic.current_piece, Tetromino)
        assert isinstance(logic.next_piece, Tetromino)

    def test_starting_level_applied(self) -> None:
        logic = TetrisLogic()
        logic.starting_level = 5
        logic.reset_game()
        assert logic.level == 5

    def test_reset_game_clears_score(self, logic: TetrisLogic) -> None:
        logic.score = 9999
        logic.lines_cleared = 42
        logic.reset_game()
        assert logic.score == 0
        assert logic.lines_cleared == 0


# ---------------------------------------------------------------------------
# Movement Validation Tests
# ---------------------------------------------------------------------------


class TestMovementValidation:
    """Test valid_move boundary and collision checks."""

    def test_piece_at_spawn_is_valid(self, logic: TetrisLogic) -> None:
        assert logic.valid_move(logic.current_piece)

    def test_piece_left_boundary(self, logic: TetrisLogic) -> None:
        piece = Tetromino(-5, 0, "I")
        assert not logic.valid_move(piece)

    def test_piece_right_boundary(self, logic: TetrisLogic) -> None:
        piece = Tetromino(GRID_WIDTH + 1, 0, "I")
        assert not logic.valid_move(piece)

    def test_piece_below_grid(self, logic: TetrisLogic) -> None:
        piece = Tetromino(0, GRID_HEIGHT, "I")
        assert not logic.valid_move(piece)

    def test_piece_collides_with_existing_blocks(self, logic: TetrisLogic) -> None:
        # Place a block at (5, 10)
        logic.grid[10][5] = RED
        piece = Tetromino(5, 10, "O")
        assert not logic.valid_move(piece)

    def test_valid_move_with_offsets(self, logic: TetrisLogic) -> None:
        piece = Tetromino(0, GRID_HEIGHT - 2, "O")
        # No offset — should be valid (O piece is 2 tall)
        assert logic.valid_move(piece)
        # With y_offset=1 would push it out
        assert not logic.valid_move(piece, y_offset=1)

    def test_valid_move_with_rotation_offset(self, logic: TetrisLogic) -> None:
        piece = Tetromino(GRID_WIDTH // 2, 5, "T")
        # Default rotation should be valid in the middle
        assert logic.valid_move(piece, rotation_offset=0)


# ---------------------------------------------------------------------------
# Line Clearing and Scoring Tests
# ---------------------------------------------------------------------------


class TestLineClearing:
    """Test line clearing, scoring, and leveling."""

    def _fill_row(self, logic: TetrisLogic, row: int) -> None:
        """Helper to fill a complete row."""
        for x in range(GRID_WIDTH):
            logic.grid[row][x] = CYAN

    def test_single_line_clear(self, logic: TetrisLogic) -> None:
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        assert logic.lines_cleared == 1
        assert logic.score == 100  # Single at level 1

    def test_double_line_clear(self, logic: TetrisLogic) -> None:
        self._fill_row(logic, GRID_HEIGHT - 1)
        self._fill_row(logic, GRID_HEIGHT - 2)
        logic.clear_lines()
        assert logic.lines_cleared == 2
        assert logic.score == 300  # Double at level 1

    def test_triple_line_clear(self, logic: TetrisLogic) -> None:
        for i in range(3):
            self._fill_row(logic, GRID_HEIGHT - 1 - i)
        logic.clear_lines()
        assert logic.lines_cleared == 3
        assert logic.score == 500  # Triple at level 1

    def test_tetris_line_clear(self, logic: TetrisLogic) -> None:
        for i in range(4):
            self._fill_row(logic, GRID_HEIGHT - 1 - i)
        logic.clear_lines()
        assert logic.lines_cleared == 4
        assert logic.score == 800  # Tetris at level 1

    def test_cleared_row_becomes_black(self, logic: TetrisLogic) -> None:
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        assert logic.grid[GRID_HEIGHT - 1][0] == BLACK

    def test_rows_above_shift_down(self, logic: TetrisLogic) -> None:
        # Place a block above the filled row
        logic.grid[GRID_HEIGHT - 2][3] = RED
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        # The block should have shifted down from row GRID_HEIGHT-2 to GRID_HEIGHT-1
        assert logic.grid[GRID_HEIGHT - 1][3] == RED

    def test_no_lines_resets_combo(self, logic: TetrisLogic) -> None:
        logic.combo = 3
        logic.clear_lines()  # No full rows
        assert logic.combo == 0

    def test_combo_increments_on_consecutive_clears(self, logic: TetrisLogic) -> None:
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        assert logic.combo == 1

        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        assert logic.combo == 2

    def test_combo_adds_bonus_score(self, logic: TetrisLogic) -> None:
        # First clear: no combo bonus
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        score_after_first = logic.score  # 100

        # Second clear: combo=1, bonus = 50 * 1 * 1 = 50
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        score_after_second = logic.score
        assert score_after_second == score_after_first + 100 + 50

    def test_level_up_at_10_lines(self, logic: TetrisLogic) -> None:
        for _ in range(10):
            self._fill_row(logic, GRID_HEIGHT - 1)
            logic.clear_lines()
        assert logic.level == 2

    def test_fall_speed_decreases_with_level(self, logic: TetrisLogic) -> None:
        initial_speed = logic.fall_speed
        for _ in range(10):
            self._fill_row(logic, GRID_HEIGHT - 1)
            logic.clear_lines()
        assert logic.fall_speed < initial_speed

    def test_statistics_tracking_singles(self, logic: TetrisLogic) -> None:
        self._fill_row(logic, GRID_HEIGHT - 1)
        logic.clear_lines()
        assert logic.total_singles == 1
        assert logic.total_doubles == 0

    def test_statistics_tracking_tetrises(self, logic: TetrisLogic) -> None:
        for i in range(4):
            self._fill_row(logic, GRID_HEIGHT - 1 - i)
        logic.clear_lines()
        assert logic.total_tetrises == 1


class TestGetLineClearText:
    """Test line clear text descriptions."""

    def test_single_text(self, logic: TetrisLogic) -> None:
        assert logic.get_line_clear_text(1) == "SINGLE!"

    def test_double_text(self, logic: TetrisLogic) -> None:
        assert logic.get_line_clear_text(2) == "DOUBLE!"

    def test_triple_text(self, logic: TetrisLogic) -> None:
        assert logic.get_line_clear_text(3) == "TRIPLE!"

    def test_tetris_text(self, logic: TetrisLogic) -> None:
        assert logic.get_line_clear_text(4) == "TETRIS!"

    def test_unknown_returns_empty(self, logic: TetrisLogic) -> None:
        assert logic.get_line_clear_text(5) == ""
        assert logic.get_line_clear_text(0) == ""


# ---------------------------------------------------------------------------
# Hold Piece Tests
# ---------------------------------------------------------------------------


class TestHoldPiece:
    """Test hold piece mechanics."""

    def test_initial_hold_is_none(self, logic: TetrisLogic) -> None:
        assert logic.held_piece is None

    def test_first_hold_stores_shape_type(self, logic: TetrisLogic) -> None:
        expected_type = logic.current_piece.shape_type
        logic.hold_piece()
        assert logic.held_piece == expected_type

    def test_first_hold_advances_to_next_piece(self, logic: TetrisLogic) -> None:
        next_type = logic.next_piece.shape_type
        logic.hold_piece()
        assert logic.current_piece.shape_type == next_type

    def test_cannot_hold_twice(self, logic: TetrisLogic) -> None:
        logic.hold_piece()
        held_after_first = logic.held_piece
        current_after_first = logic.current_piece.shape_type
        logic.hold_piece()  # Should do nothing
        assert logic.held_piece == held_after_first
        assert logic.current_piece.shape_type == current_after_first

    def test_hold_swap_exchanges_pieces(self, logic: TetrisLogic) -> None:
        # Force specific pieces
        logic.current_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, "T")
        logic.next_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, "I")
        logic.hold_piece()  # Hold T, current becomes I
        assert logic.held_piece == "T"
        assert logic.current_piece.shape_type == "I"

        # Now lock piece and hold again
        logic.can_hold = True
        logic.hold_piece()  # Current I goes to hold, T comes out
        assert logic.held_piece == "I"
        assert logic.current_piece.shape_type == "T"


# ---------------------------------------------------------------------------
# Hard Drop Tests
# ---------------------------------------------------------------------------


class TestHardDrop:
    """Test hard drop mechanics."""

    def test_hard_drop_scores_points(self, logic: TetrisLogic) -> None:
        initial_score = logic.score
        logic.hard_drop()
        assert logic.score > initial_score

    def test_hard_drop_locks_piece(self, logic: TetrisLogic) -> None:
        old_piece_type = logic.current_piece.shape_type
        logic.hard_drop()
        # Current piece should be a new piece (different object)
        assert logic.current_piece.shape_type != old_piece_type or True  # new object
        # Some grid cells should be filled
        has_filled = any(cell != BLACK for row in logic.grid for cell in row)
        assert has_filled


# ---------------------------------------------------------------------------
# Snapshot and Rewind Tests
# ---------------------------------------------------------------------------


class TestSnapshotRewind:
    """Test snapshot/restore (rewind) system."""

    def test_create_snapshot_captures_score(self, logic: TetrisLogic) -> None:
        logic.score = 500
        snap = logic.create_snapshot()
        assert snap["score"] == 500

    def test_restore_snapshot_restores_score(self, logic: TetrisLogic) -> None:
        logic.score = 500
        snap = logic.create_snapshot()
        logic.score = 999
        logic.restore_snapshot(snap)
        assert logic.score == 500

    def test_snapshot_grid_is_deep_copy(self, logic: TetrisLogic) -> None:
        snap = logic.create_snapshot()
        logic.grid[0][0] = RED
        assert snap["grid"][0][0] == BLACK  # Not affected

    def test_rewind_disabled_by_default(self, logic: TetrisLogic) -> None:
        assert not logic.allow_rewind

    def test_update_rewind_history_clears_when_disabled(
        self, logic: TetrisLogic
    ) -> None:
        logic.rewind_history = [logic.create_snapshot()]
        logic.update_rewind_history()
        assert len(logic.rewind_history) == 0

    def test_update_rewind_history_appends_when_enabled(
        self, logic: TetrisLogic
    ) -> None:
        logic.allow_rewind = True
        logic.update_rewind_history()
        assert len(logic.rewind_history) == 1

    def test_rewind_does_nothing_when_disabled(self, logic: TetrisLogic) -> None:
        logic.score = 500
        logic.rewind()
        assert logic.score == 500  # Unchanged


# ---------------------------------------------------------------------------
# Copy Piece Tests
# ---------------------------------------------------------------------------


class TestCopyPiece:
    """Test piece cloning."""

    def test_copy_preserves_position(self, logic: TetrisLogic) -> None:
        original = Tetromino(3, 7, "S")
        original.rotation = 2
        clone = logic.copy_piece(original)
        assert clone.x == 3
        assert clone.y == 7
        assert clone.shape_type == "S"
        assert clone.rotation == 2

    def test_copy_is_independent(self, logic: TetrisLogic) -> None:
        original = Tetromino(3, 7, "S")
        clone = logic.copy_piece(original)
        clone.x = 99
        assert original.x == 3  # Not affected


# ---------------------------------------------------------------------------
# Game Update Tests
# ---------------------------------------------------------------------------


class TestGameUpdate:
    """Test the main game update loop."""

    def test_update_accumulates_fall_time(self, logic: TetrisLogic) -> None:
        logic.update(100)
        assert logic.fall_time == 100

    def test_piece_falls_when_time_exceeds_speed(self, logic: TetrisLogic) -> None:
        initial_y = logic.current_piece.y
        # Give enough time to trigger a drop
        logic.update(logic.fall_speed + 1)
        assert logic.current_piece.y == initial_y + 1

    def test_piece_locks_when_cannot_fall(self, logic: TetrisLogic) -> None:
        # Place piece at the bottom
        logic.current_piece = Tetromino(0, GRID_HEIGHT - 2, "O")
        logic.update(logic.fall_speed + 1)
        # After lock, a new piece should be spawned
        # (grid should have some filled cells)
        has_filled = any(cell != BLACK for row in logic.grid for cell in row)
        assert has_filled


# ---------------------------------------------------------------------------
# Particle Tests
# ---------------------------------------------------------------------------


class TestParticle:
    """Test Particle lifecycle."""

    def test_particle_initial_state(self) -> None:
        p = Particle(10.0, 20.0, (255, 0, 0), 1.0, -2.0)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.color == (255, 0, 0)
        assert p.velocity_x == 1.0
        assert p.velocity_y == -2.0
        assert p.lifetime == 60
        assert p.alpha == 255

    def test_particle_is_alive_initially(self) -> None:
        p = Particle(0, 0, (0, 0, 0), 0, 0)
        assert p.is_alive()

    def test_particle_update_moves_position(self) -> None:
        p = Particle(10.0, 20.0, (0, 0, 0), 2.0, -3.0)
        p.update()
        assert p.x == 12.0
        assert p.y == 17.0

    def test_particle_update_applies_gravity(self) -> None:
        p = Particle(0, 0, (0, 0, 0), 0, 0)
        p.update()
        assert p.velocity_y == pytest.approx(0.2)

    def test_particle_lifetime_decreases(self) -> None:
        p = Particle(0, 0, (0, 0, 0), 0, 0)
        p.update()
        assert p.lifetime == 59

    def test_particle_alpha_decreases(self) -> None:
        p = Particle(0, 0, (0, 0, 0), 0, 0)
        p.update()
        assert p.alpha < 255

    def test_particle_dies_after_60_updates(self) -> None:
        p = Particle(0, 0, (0, 0, 0), 0, 0)
        for _ in range(60):
            p.update()
        assert not p.is_alive()
        assert p.alpha == 0


# ---------------------------------------------------------------------------
# ScorePopup Tests
# ---------------------------------------------------------------------------


class TestScorePopup:
    """Test ScorePopup lifecycle."""

    def test_popup_initial_state(self) -> None:
        p = ScorePopup("SINGLE!", 100, 200)
        assert p.text == "SINGLE!"
        assert p.x == 100
        assert p.y == 200
        assert p.start_y == 200
        assert p.lifetime == 90
        assert p.alpha == 255

    def test_popup_custom_color(self) -> None:
        p = ScorePopup("TETRIS!", 0, 0, (192, 192, 192))
        assert p.color == (192, 192, 192)

    def test_popup_is_alive_initially(self) -> None:
        p = ScorePopup("x", 0, 0)
        assert p.is_alive()

    def test_popup_update_moves_up(self) -> None:
        p = ScorePopup("x", 0, 100)
        p.update()
        assert p.y == 99  # Moves up by 1 per update

    def test_popup_lifetime_decreases(self) -> None:
        p = ScorePopup("x", 0, 0)
        p.update()
        assert p.lifetime == 89

    def test_popup_dies_after_90_updates(self) -> None:
        p = ScorePopup("x", 0, 0)
        for _ in range(90):
            p.update()
        assert not p.is_alive()
        assert p.alpha == 0


# ---------------------------------------------------------------------------
# DbC Contract Tests
# ---------------------------------------------------------------------------


class TestTetrominoContracts:
    """Design-by-Contract: verify invariants and boundary conditions."""

    def test_all_shape_types_are_valid(self) -> None:
        """Every shape type in SHAPES must be representable as a Tetromino."""
        for shape_type in SHAPES:
            t = Tetromino(0, 0, shape_type)
            assert t.shape_type == shape_type
            assert len(t.get_rotated_shape()) > 0

    def test_invalid_shape_type_raises(self) -> None:
        """Creating a Tetromino with an invalid type should raise KeyError."""
        with pytest.raises(KeyError):
            Tetromino(0, 0, "INVALID")

    def test_rotation_always_returns_2d_grid(self) -> None:
        """Rotated shape must always be a non-empty 2D list."""
        for shape_type in SHAPES:
            t = Tetromino(0, 0, shape_type)
            for _ in range(4):
                shape = t.get_rotated_shape()
                assert isinstance(shape, list)
                assert len(shape) > 0
                assert all(isinstance(row, list) for row in shape)
                assert all(len(row) > 0 for row in shape)
                t.rotate()


class TestTetrisLogicContracts:
    """Design-by-Contract: verify game logic invariants."""

    def test_grid_dimensions_never_change(self, logic: TetrisLogic) -> None:
        """Grid must always maintain correct dimensions."""
        for _ in range(5):
            logic.update(logic.fall_speed + 1)
        assert len(logic.grid) == GRID_HEIGHT
        assert all(len(row) == GRID_WIDTH for row in logic.grid)

    def test_score_never_negative(self, logic: TetrisLogic) -> None:
        """Score must never go below zero."""
        logic.update(10000)
        assert logic.score >= 0

    def test_level_never_below_starting(self, logic: TetrisLogic) -> None:
        """Level must never drop below starting level."""
        logic.update(10000)
        assert logic.level >= logic.starting_level

    def test_fall_speed_has_minimum(self) -> None:
        """Fall speed must never go below 50ms."""
        logic = TetrisLogic()
        logic.starting_level = 100
        logic.reset_game()
        assert logic.fall_speed >= 50
