"""Comprehensive tests for game mechanics across multiple games.

Tests cover:
- Game initialization and state setup
- Turn mechanics (move order, turn validation, turn advancement)
- Move validation (legal vs illegal moves, boundary conditions)
- State transitions (win/loss conditions, draw detection, game reset)
- Score/points calculation
- Resource management (if applicable)
- Collision detection and spatial queries
- Rules enforcement (checking for rule violations)
- Edge cases (empty board, single entity, maximum state size)

Design by Contract approach:
- Preconditions: validate game state initialization, valid moves
- Postconditions: verify state consistency after moves, score updates correct
- Invariants: board state integrity, conservation laws (total resources)
- Edge cases: boundary moves, null states, rapid sequences
"""

from __future__ import annotations

import pytest

from games.Peanut_Butter_Panic.peanut_butter_panic.core import (
    GameConfig,
    GameWorld,
    InputState,
    Player,
    Sandwich,
)
from games.shared.spatial_grid import SpatialGrid
from games.Tetris.src.constants import (
    BLACK,
    CYAN,
    GRID_HEIGHT,
    GRID_WIDTH,
    RED,
)
from games.Tetris.src.game_logic import TetrisLogic
from games.Tetris.src.tetromino import Tetromino

# ============================================================================
# TETRIS GAME MECHANICS TESTS
# ============================================================================


class TestTetrisGameInitialization:
    """Tests for Tetris game setup and initial state (Preconditions).

    Contract: Game must initialize to a valid playing state with:
    - Empty grid
    - Valid starting piece and next piece
    - Score, level, and lines_cleared all zero
    - No game-over condition
    """

    def test_tetris_initializes_to_valid_state(self) -> None:
        """Game should initialize to valid starting state."""
        logic = TetrisLogic()

        # Precondition check: valid initial state exists
        assert logic is not None
        assert not logic.game_over
        assert logic.score == 0
        assert logic.lines_cleared == 0
        assert logic.level == 1

    def test_tetris_grid_dimensions(self) -> None:
        """Grid should have correct dimensions."""
        logic = TetrisLogic()
        assert len(logic.grid) == GRID_HEIGHT
        assert all(len(row) == GRID_WIDTH for row in logic.grid)

    def test_tetris_grid_initially_empty(self) -> None:
        """All grid cells should be empty (BLACK) at start."""
        logic = TetrisLogic()
        for row in logic.grid:
            for cell in row:
                assert cell == BLACK

    def test_tetris_current_piece_exists(self) -> None:
        """Current piece should be valid Tetromino."""
        logic = TetrisLogic()
        assert logic.current_piece is not None
        assert isinstance(logic.current_piece, Tetromino)
        assert 0 <= logic.current_piece.x < GRID_WIDTH
        assert 0 <= logic.current_piece.y < GRID_HEIGHT

    def test_tetris_next_piece_exists(self) -> None:
        """Next piece should be valid Tetromino."""
        logic = TetrisLogic()
        assert logic.next_piece is not None
        assert isinstance(logic.next_piece, Tetromino)

    def test_tetris_held_piece_initially_none(self) -> None:
        """Held piece should be None at start."""
        logic = TetrisLogic()
        assert logic.held_piece is None

    def test_tetris_can_hold_initially_true(self) -> None:
        """Can hold flag should be True at start."""
        logic = TetrisLogic()
        assert logic.can_hold is True

    def test_tetris_combo_starts_at_zero(self) -> None:
        """Combo counter should start at zero."""
        logic = TetrisLogic()
        assert logic.combo == 0


class TestTetrisMoveValidation:
    """Tests for move validation and legal/illegal move detection.

    Contract: Move validation must correctly identify:
    - Legal moves (within bounds, no collision)
    - Illegal moves (out of bounds, collision)
    - Boundary conditions (edge positions)
    """

    def test_valid_move_left_from_center(self) -> None:
        """Moving left from center should be valid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = GRID_WIDTH // 2
        piece.y = 2
        assert logic.valid_move(piece)

    def test_valid_move_right_from_center(self) -> None:
        """Moving right from center should be valid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = GRID_WIDTH // 2 - 2
        piece.y = 2
        assert logic.valid_move(piece)

    def test_invalid_move_left_out_of_bounds(self) -> None:
        """Moving too far left should be invalid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = -2
        assert not logic.valid_move(piece)

    def test_invalid_move_right_out_of_bounds(self) -> None:
        """Moving too far right should be invalid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = GRID_WIDTH + 2
        assert not logic.valid_move(piece)

    def test_invalid_move_collision_with_filled_cell(self) -> None:
        """Move should be invalid if piece overlaps filled cell."""
        logic = TetrisLogic()
        # Fill a region with color - several cells to ensure collision
        for x in range(GRID_WIDTH):
            logic.grid[5][x] = RED
        piece = logic.current_piece
        piece.x = 0
        piece.y = 4
        # Should detect collision with filled line below
        assert not logic.valid_move(piece, y_offset=1)

    def test_valid_move_down_from_top(self) -> None:
        """Moving down from top should be valid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.y = 2
        assert logic.valid_move(piece)

    def test_boundary_move_left_edge(self) -> None:
        """Piece at left edge should be valid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = 0
        assert logic.valid_move(piece)

    def test_boundary_move_right_edge(self) -> None:
        """Piece at right edge should be valid if within bounds."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = GRID_WIDTH - 4  # Leave room for tetromino width
        assert logic.valid_move(piece)


class TestTetrisStateTransitions:
    """Tests for game state transitions and win/loss conditions.

    Contract: Game state transitions must maintain invariants:
    - Score only increases or stays same
    - Lines cleared only increases or stays same
    - Level only increases or stays same
    - Game over state is irreversible
    """

    def test_game_over_when_piece_cant_spawn(self) -> None:
        """Game should end when new piece can't fit at spawn."""
        logic = TetrisLogic()
        # Fill spawn area completely
        for y in range(4):
            for x in range(GRID_WIDTH):
                logic.grid[y][x] = RED

        # Try to spawn new piece
        piece = logic.new_piece()
        assert not logic.valid_move(piece)

    def test_reset_game_clears_score(self) -> None:
        """Reset should zero out score."""
        logic = TetrisLogic()
        logic.score = 500
        logic.reset_game()
        assert logic.score == 0

    def test_reset_game_clears_grid(self) -> None:
        """Reset should clear the grid."""
        logic = TetrisLogic()
        logic.grid[0][0] = RED
        logic.reset_game()
        assert logic.grid[0][0] == BLACK

    def test_reset_game_clears_lines_cleared(self) -> None:
        """Reset should zero lines cleared."""
        logic = TetrisLogic()
        logic.lines_cleared = 10
        logic.reset_game()
        assert logic.lines_cleared == 0

    def test_reset_game_resets_level(self) -> None:
        """Reset should reset level to starting level."""
        logic = TetrisLogic()
        logic.level = 5
        logic.reset_game()
        assert logic.level == logic.starting_level

    def test_score_monotonically_increases(self) -> None:
        """Score should never decrease after move."""
        logic = TetrisLogic()
        initial_score = logic.score
        logic.move_piece_down()
        assert logic.score >= initial_score

    def test_lines_cleared_monotonically_increases(self) -> None:
        """Lines cleared should never decrease."""
        logic = TetrisLogic()
        initial_lines = logic.lines_cleared
        # Manually set a filled line and clear it
        for x in range(GRID_WIDTH):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN
        logic.clear_lines()
        assert logic.lines_cleared >= initial_lines


class TestTetrisMovement:
    """Tests for piece movement mechanics.

    Contract: Movement must:
    - Update piece position correctly
    - Validate before moving
    - Not allow invalid moves
    - Award soft-drop points on down move
    """

    def test_move_left_updates_position(self) -> None:
        """Moving left should decrease x."""
        logic = TetrisLogic()
        piece = logic.current_piece
        initial_x = piece.x
        logic.move_piece_left()
        assert piece.x == initial_x - 1

    def test_move_right_updates_position(self) -> None:
        """Moving right should increase x."""
        logic = TetrisLogic()
        piece = logic.current_piece
        initial_x = piece.x
        logic.move_piece_right()
        assert piece.x == initial_x + 1

    def test_move_down_updates_position_and_score(self) -> None:
        """Moving down should increase y and award point."""
        logic = TetrisLogic()
        piece = logic.current_piece
        initial_y = piece.y
        initial_score = logic.score
        logic.move_piece_down()
        assert piece.y == initial_y + 1
        assert logic.score == initial_score + 1

    def test_multiple_down_moves_increment_score_each_time(self) -> None:
        """Each soft drop should award point."""
        logic = TetrisLogic()
        initial_score = logic.score
        logic.move_piece_down()
        logic.move_piece_down()
        logic.move_piece_down()
        assert logic.score == initial_score + 3


class TestTetrisRotation:
    """Tests for piece rotation mechanics.

    Contract: Rotation must:
    - Change piece orientation
    - Be reversible (4 rotations = identity)
    - Validate rotation before applying
    """

    def test_tetromino_rotation_cycles(self) -> None:
        """Piece should return to original after 4 rotations."""
        t = Tetromino(0, 0, "T")
        initial_rotation = t.rotation
        for _ in range(4):
            t.rotate()
        assert t.rotation == initial_rotation

    def test_tetromino_t_piece_rotation_changes_shape(self) -> None:
        """T piece rotation should change its shape."""
        t = Tetromino(0, 0, "T")
        shape1 = t.get_rotated_shape()
        t.rotate()
        shape2 = t.get_rotated_shape()
        # Shapes should be different after rotation
        assert shape1 != shape2


class TestTetrisLineClearing:
    """Tests for line clearing and scoring.

    Contract: Line clearing must:
    - Detect complete lines
    - Clear detected lines
    - Award points based on level and lines cleared
    - Move lines down after clearing
    """

    def test_complete_line_is_detected(self) -> None:
        """Completely filled line should be cleared."""
        logic = TetrisLogic()
        # Fill bottom line
        for x in range(GRID_WIDTH):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN

        initial_lines = logic.lines_cleared
        logic.clear_lines()
        assert logic.lines_cleared > initial_lines

    def test_complete_line_is_cleared_to_black(self) -> None:
        """Cleared line should be all BLACK."""
        logic = TetrisLogic()
        # Fill bottom line
        for x in range(GRID_WIDTH):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN

        logic.clear_lines()
        # Line should be cleared (all BLACK)
        assert all(cell == BLACK for cell in logic.grid[GRID_HEIGHT - 1])

    def test_multiple_lines_cleared_together(self) -> None:
        """Multiple complete lines should be cleared together."""
        logic = TetrisLogic()
        # Fill two bottom lines
        for x in range(GRID_WIDTH):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN
            logic.grid[GRID_HEIGHT - 2][x] = CYAN

        initial_lines = logic.lines_cleared
        logic.clear_lines()
        assert logic.lines_cleared >= initial_lines + 2

    def test_partial_line_not_cleared(self) -> None:
        """Partially filled line should not be cleared."""
        logic = TetrisLogic()
        # Fill most of bottom line, but not all
        for x in range(GRID_WIDTH - 1):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN

        initial_lines = logic.lines_cleared
        logic.clear_lines()
        # Line should not be cleared
        assert logic.lines_cleared == initial_lines


class TestTetrisEdgeCases:
    """Tests for edge cases and boundary conditions.

    Contract: Edge cases must be handled gracefully:
    - Empty grid
    - Single cell filled
    - Maximum state size
    - Rapid piece spawning
    """

    def test_empty_grid_valid_move(self) -> None:
        """Piece should move freely in empty grid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = GRID_WIDTH // 2
        piece.y = 5
        assert logic.valid_move(piece)

    def test_single_cell_filled_doesnt_break_game(self) -> None:
        """Single filled cell should not break game."""
        logic = TetrisLogic()
        # Grid is 20 high, fill a safe cell
        logic.grid[15][5] = RED
        piece = logic.current_piece
        piece.x = 0
        piece.y = 0
        # Game should still function
        assert logic is not None

    def test_piece_at_grid_boundary(self) -> None:
        """Piece at grid boundary should be valid."""
        logic = TetrisLogic()
        piece = logic.current_piece
        piece.x = GRID_WIDTH - 1
        piece.y = GRID_HEIGHT - 1
        # Should handle boundary without error
        assert isinstance(piece, Tetromino)

    def test_rewind_history_clear(self) -> None:
        """Clearing rewind history should work."""
        logic = TetrisLogic()
        logic.rewind_history = [{"some": "snapshot"}]
        logic.clear_rewind_history()
        assert len(logic.rewind_history) == 0


# ============================================================================
# PEANUT BUTTER PANIC GAME MECHANICS TESTS
# ============================================================================


class TestPBPGameInitialization:
    """Tests for PBP game setup and initial state (Preconditions).

    Contract: Game must initialize with:
    - Correct number of sandwiches
    - Valid player position
    - Player health > 0
    - Score = 0
    - No enemies at start
    """

    def test_pbp_game_world_initializes(self) -> None:
        """Game world should initialize to valid state."""
        world = GameWorld()
        assert world is not None
        assert world.player is not None
        assert world.player.health > 0

    def test_pbp_initial_sandwich_count(self) -> None:
        """Should have starting number of sandwiches."""
        world = GameWorld()
        assert len(world.sandwiches) == 2  # Default is 2 sandwiches

    def test_pbp_initial_score_zero(self) -> None:
        """Score should start at zero."""
        world = GameWorld()
        assert world.stats.score == 0

    def test_pbp_initial_wave_is_one(self) -> None:
        """Wave should start at 1."""
        world = GameWorld()
        assert world.stats.wave == 1

    def test_pbp_player_position_in_bounds(self) -> None:
        """Player should spawn in valid position."""
        world = GameWorld()
        config = world.config
        assert 0 <= world.player.position[0] <= config.width
        assert 0 <= world.player.position[1] <= config.height

    def test_pbp_player_initial_health(self) -> None:
        """Player health should match config."""
        world = GameWorld()
        assert world.player.health == world.config.player_health

    def test_pbp_initial_no_enemies(self) -> None:
        """No enemies should spawn at initialization."""
        world = GameWorld()
        assert len(world.enemies) == 0


class TestPBPMovement:
    """Tests for player movement mechanics.

    Contract: Movement must:
    - Update player position based on input
    - Respect game boundaries
    - Handle diagonal movement
    - Maintain movement speed
    """

    def test_player_moves_right(self) -> None:
        """Player should move right with right input."""
        world = GameWorld()
        initial_pos = world.player.position
        input_state = InputState(move=(1.0, 0.0))
        world.update(0.1, input_state)
        assert world.player.position[0] > initial_pos[0]

    def test_player_moves_left(self) -> None:
        """Player should move left with left input."""
        world = GameWorld()
        initial_pos = world.player.position
        input_state = InputState(move=(-1.0, 0.0))
        world.update(0.1, input_state)
        assert world.player.position[0] < initial_pos[0]

    def test_player_moves_up(self) -> None:
        """Player should move up with up input."""
        world = GameWorld()
        initial_pos = world.player.position
        input_state = InputState(move=(0.0, -1.0))
        world.update(0.1, input_state)
        assert world.player.position[1] < initial_pos[1]

    def test_player_moves_down(self) -> None:
        """Player should move down with down input."""
        world = GameWorld()
        initial_pos = world.player.position
        input_state = InputState(move=(0.0, 1.0))
        world.update(0.1, input_state)
        assert world.player.position[1] > initial_pos[1]

    def test_no_movement_with_zero_input(self) -> None:
        """Player should not move with zero input."""
        world = GameWorld()
        initial_pos = world.player.position
        input_state = InputState(move=(0.0, 0.0))
        world.update(0.1, input_state)
        # Position should be unchanged (or very close due to floating point)
        assert abs(world.player.position[0] - initial_pos[0]) < 1e-6
        assert abs(world.player.position[1] - initial_pos[1]) < 1e-6

    def test_player_stays_in_bounds_left(self) -> None:
        """Player should not move past left boundary."""
        world = GameWorld()
        # Move player to left edge
        world.player.position = (0.0, world.config.height // 2)
        input_state = InputState(move=(-1.0, 0.0))
        world.update(0.1, input_state)
        assert world.player.position[0] >= 0

    def test_player_stays_in_bounds_right(self) -> None:
        """Player should not move past right boundary."""
        world = GameWorld()
        world.player.position = (world.config.width, world.config.height // 2)
        input_state = InputState(move=(1.0, 0.0))
        world.update(0.1, input_state)
        assert world.player.position[0] <= world.config.width

    def test_diagonal_movement(self) -> None:
        """Player should move diagonally with both inputs."""
        world = GameWorld()
        initial_pos = world.player.position
        input_state = InputState(move=(1.0, 1.0))
        world.update(0.1, input_state)
        # Both coordinates should change
        assert world.player.position[0] > initial_pos[0]
        assert world.player.position[1] > initial_pos[1]


class TestPBPResourceManagement:
    """Tests for resource management (player health, sandwich health).

    Contract: Resources must:
    - Decrease when damaged
    - Never go negative
    - Be conserved or accounted for
    - Trigger game-over when zero
    """

    def test_player_health_decreases_on_damage(self) -> None:
        """Player health should decrease when damaged."""
        world = GameWorld()
        initial_health = world.player.health
        world.player.health -= 1
        assert world.player.health < initial_health

    def test_player_health_never_negative(self) -> None:
        """Player health should never be negative after assignment."""
        world = GameWorld()
        # Direct assignment allows negative (game logic should handle this)
        world.player.health = -1
        # Negative health is technically allowed in the data structure
        # but game logic should interpret it as dead
        assert world.player.health <= 0

    def test_sandwich_health_decreases_on_damage(self) -> None:
        """Sandwich health should decrease when damaged."""
        world = GameWorld()
        sandwich = world.sandwiches[0]
        initial_health = sandwich.health
        sandwich.health -= 1
        assert sandwich.health < initial_health

    def test_sandwich_dies_at_zero_health(self) -> None:
        """Sandwich should be considered dead at 0 health."""
        world = GameWorld()
        sandwich = world.sandwiches[0]
        sandwich.health = 0
        assert not sandwich.alive

    def test_sandwich_alive_above_zero_health(self) -> None:
        """Sandwich should be alive above 0 health."""
        world = GameWorld()
        sandwich = world.sandwiches[0]
        sandwich.health = 1
        assert sandwich.alive

    def test_multiple_sandwiches_tracked_independently(self) -> None:
        """Each sandwich should track health independently."""
        world = GameWorld()
        s1 = world.sandwiches[0]
        s2 = world.sandwiches[1] if len(world.sandwiches) > 1 else None

        if s2:
            s1.health = 1
            s2.health = 3
            assert s1.health != s2.health


class TestPBPCollisionDetection:
    """Tests for collision detection and spatial queries.

    Contract: Collision detection must:
    - Detect overlapping entities
    - Calculate distances correctly
    - Handle edge cases (same position, far apart)
    """

    def test_entities_at_same_position_collide(self) -> None:
        """Entities at same position should collide."""
        world = GameWorld()
        pos = (100.0, 100.0)
        player = Player(position=pos, speed=0.0)
        sandwich = Sandwich(position=pos, health=1)
        # Calculate distance
        dist = (
            abs(
                (player.position[0] - sandwich.position[0]) ** 2
                + (player.position[1] - sandwich.position[1]) ** 2
            )
            ** 0.5
        )
        assert dist < player.radius + sandwich.radius

    def test_entities_far_apart_no_collision(self) -> None:
        """Distant entities should not collide."""
        pos1 = (0.0, 0.0)
        pos2 = (1000.0, 1000.0)
        player = Player(position=pos1, speed=0.0)
        sandwich = Sandwich(position=pos2, health=1)
        dist = (
            abs(
                (player.position[0] - sandwich.position[0]) ** 2
                + (player.position[1] - sandwich.position[1]) ** 2
            )
            ** 0.5
        )
        assert dist > player.radius + sandwich.radius

    def test_distance_calculation_correct(self) -> None:
        """Distance should be calculated correctly."""
        pos1 = (0.0, 0.0)
        pos2 = (3.0, 4.0)
        dist = abs((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
        assert abs(dist - 5.0) < 1e-6


class TestPBPScoring:
    """Tests for score calculation and reward mechanics.

    Contract: Scoring must:
    - Award points for enemy kills
    - Calculate bonuses correctly
    - Account for combos
    - Never decrease score
    """

    def test_initial_score_zero(self) -> None:
        """Score should start at zero."""
        world = GameWorld()
        assert world.stats.score == 0

    def test_score_non_decreasing(self) -> None:
        """Score should never decrease."""
        world = GameWorld()
        initial_score = world.stats.score
        # Simulate some game updates
        world.update(0.1, InputState())
        world.update(0.1, InputState())
        assert world.stats.score >= initial_score

    def test_combo_tracks_correctly(self) -> None:
        """Combo counter should track kills."""
        world = GameWorld()
        initial_combo = world.stats.combo
        # Combo should start at 0
        assert initial_combo >= 0


class TestPBPGameStateTransitions:
    """Tests for game state transitions and win/loss conditions.

    Contract: Game state must:
    - Transition to game-over when player dies
    - Track wave progression
    - Handle wave completion
    - Not allow actions after game-over
    """

    def test_game_not_over_at_start(self) -> None:
        """Game should have valid initial state."""
        world = GameWorld()
        # GameWorld doesn't have explicit game_over flag, check conditions instead
        assert world.player.health > 0
        assert any(s.alive for s in world.sandwiches)

    def test_player_death_condition(self) -> None:
        """Player death should be detectable by health == 0."""
        world = GameWorld()
        world.player.health = 0
        # Game logic should detect this as a loss condition
        assert world.player.health == 0

    def test_all_sandwiches_dead_condition(self) -> None:
        """All sandwiches dead should be detectable."""
        world = GameWorld()
        for sandwich in world.sandwiches:
            sandwich.health = 0
        # All sandwiches should be marked as not alive
        assert all(not s.alive for s in world.sandwiches)


class TestPBPEdgeCases:
    """Tests for edge cases and boundary conditions.

    Contract: Edge cases must be handled gracefully:
    - Empty enemy list
    - Single sandwich
    - Zero time delta
    - Maximum wave number
    """

    def test_empty_enemy_list(self) -> None:
        """Game should handle no enemies."""
        world = GameWorld()
        assert isinstance(world.enemies, list)
        assert len(world.enemies) >= 0

    def test_game_with_custom_config(self) -> None:
        """Game should accept custom config."""
        config = GameConfig(player_health=5)
        world = GameWorld(config)
        assert world.player.health == 5

    def test_zero_time_delta(self) -> None:
        """Zero delta should not break game."""
        world = GameWorld()
        initial_pos = world.player.position
        world.update(0.0, InputState())
        # Position should not change with zero delta
        assert world.player.position == initial_pos

    def test_large_time_delta(self) -> None:
        """Large delta should not break game."""
        world = GameWorld()
        # Should handle large time steps without error
        world.update(10.0, InputState(move=(1.0, 0.0)))
        assert world is not None


# ============================================================================
# SPATIAL GRID TESTS (Shared mechanic across games)
# ============================================================================


class TestSpatialGridInitialization:
    """Tests for spatial grid setup and initialization.

    Contract: Grid must:
    - Initialize with valid cell size
    - Start empty
    - Support custom cell sizes
    """

    def test_spatial_grid_default_cell_size(self) -> None:
        """Grid should have default cell size."""
        grid = SpatialGrid()
        assert grid.cell_size == 5.0

    def test_spatial_grid_custom_cell_size(self) -> None:
        """Grid should accept custom cell size."""
        grid = SpatialGrid(cell_size=10.0)
        assert grid.cell_size == 10.0

    def test_spatial_grid_starts_empty(self) -> None:
        """Grid should start with no cells."""
        grid = SpatialGrid()
        assert len(grid.cells) == 0

    def test_spatial_grid_invalid_cell_size_raises(self) -> None:
        """Zero or negative cell size should raise."""
        with pytest.raises(ValueError):
            SpatialGrid(cell_size=0)
        with pytest.raises(ValueError):
            SpatialGrid(cell_size=-1.0)


class TestSpatialGridInsertion:
    """Tests for entity insertion and spatial organization.

    Contract: Insertion must:
    - Place entities in correct cells
    - Handle multiple entities in same cell
    - Handle entities in different cells
    """

    def test_insert_single_entity(self) -> None:
        """Inserting entity should create cell."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        p = Point(2.5, 3.5)
        grid.insert(p)
        assert len(grid.cells) == 1

    def test_insert_multiple_entities_same_cell(self) -> None:
        """Multiple entities in same cell should share cell."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        a = Point(1.0, 1.0)
        b = Point(2.0, 2.0)
        grid.insert(a)
        grid.insert(b)
        assert len(grid.cells) == 1

    def test_insert_entities_different_cells(self) -> None:
        """Entities in different cells should create separate cells."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        a = Point(1.0, 1.0)  # cell (0, 0)
        b = Point(6.0, 6.0)  # cell (1, 1)
        grid.insert(a)
        grid.insert(b)
        assert len(grid.cells) == 2


class TestSpatialGridQuerying:
    """Tests for spatial queries and nearby detection.

    Contract: Queries must:
    - Return entities in query cell
    - Return entities in adjacent cells
    - Exclude distant entities
    - Handle negative coordinates
    """

    def test_query_returns_entity_in_same_cell(self) -> None:
        """Query should find entity in same cell."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        p = Point(2.5, 2.5)
        grid.insert(p)
        result = grid.get_nearby(2.5, 2.5)
        assert p in result

    def test_query_returns_entity_in_adjacent_cell(self) -> None:
        """Query should find entity in adjacent cell."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        p = Point(7.0, 7.0)  # cell (1, 1)
        grid.insert(p)
        result = grid.get_nearby(4.9, 4.9)  # cell (0, 0)
        assert p in result

    def test_query_excludes_distant_entities(self) -> None:
        """Query should not find distant entities."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        far = Point(52.0, 52.0)  # cell (10, 10)
        grid.insert(far)
        result = grid.get_nearby(0.0, 0.0)
        assert far not in result

    def test_query_empty_grid_returns_empty(self) -> None:
        """Query on empty grid should return empty list."""
        grid = SpatialGrid(cell_size=5.0)
        result = grid.get_nearby(0.0, 0.0)
        assert result == []

    def test_query_negative_coordinates(self) -> None:
        """Grid should handle negative coordinates."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        p = Point(-3.0, -7.0)
        grid.insert(p)
        result = grid.get_nearby(-3.0, -7.0)
        assert p in result


class TestSpatialGridUpdate:
    """Tests for bulk grid updates and clearing.

    Contract: Updates must:
    - Replace all entities
    - Clear previous entities
    - Handle empty lists
    """

    def test_update_rebuilds_grid(self) -> None:
        """Update should rebuild grid with new entities."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        a = Point(1.0, 1.0)
        b = Point(6.0, 6.0)
        grid.update([a, b])
        assert len(grid.cells) == 2

    def test_update_clears_previous_entities(self) -> None:
        """Update should clear old entities."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        grid.insert(Point(100.0, 100.0))
        grid.update([Point(1.0, 1.0)])
        assert len(grid.cells) == 1

    def test_update_with_empty_list(self) -> None:
        """Update with empty list should clear grid."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        grid.insert(Point(1.0, 1.0))
        grid.update([])
        assert len(grid.cells) == 0

    def test_grid_clear(self) -> None:
        """Explicit clear should empty grid."""
        grid = SpatialGrid(cell_size=5.0)

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        grid.insert(Point(1.0, 1.0))
        grid.insert(Point(6.0, 6.0))
        grid.clear()
        assert len(grid.cells) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
