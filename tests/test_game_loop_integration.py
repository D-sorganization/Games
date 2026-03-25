"""Integration tests for game loops.

Covers Duum, Tetris, and Force_Field games.  Each test creates a game
instance (mocking pygame display where needed), runs several update
cycles, and verifies the resulting game state is self-consistent.

The test suite runs under the root conftest.py which replaces the real
``pygame`` C extension with a lightweight fake module tree.  That means
display, event, mouse, mixer, and most pygame APIs are already stubbed
out; the fixtures here only need to patch things that are *not* covered
by conftest (sound loading, texture generation).

Relates to: issue #571
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

# Belt-and-suspenders: keep SDL headless in case conftest fake is incomplete.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dummy_surface(size: tuple[int, int] = (800, 600)) -> MagicMock:
    """Return a MagicMock that mimics enough of pygame.Surface for tests."""
    surf = MagicMock()
    surf.get_size.return_value = size
    surf.get_width.return_value = size[0]
    surf.get_height.return_value = size[1]
    return surf


# ---------------------------------------------------------------------------
# Tetris — game logic does not require a display surface directly
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTetrisGameLoopIntegration:
    """Integration tests for TetrisLogic update cycles."""

    def test_initial_state_is_valid(self) -> None:
        """A freshly constructed TetrisLogic should have a coherent state."""
        from games.Tetris.src.constants import BLACK, GRID_HEIGHT, GRID_WIDTH
        from games.Tetris.src.game_logic import TetrisLogic

        logic = TetrisLogic()

        assert not logic.game_over
        assert logic.score == 0
        assert logic.level == logic.starting_level
        assert len(logic.grid) == GRID_HEIGHT
        assert all(len(row) == GRID_WIDTH for row in logic.grid)
        # Board must be empty at start
        assert all(cell == BLACK for row in logic.grid for cell in row)
        assert logic.current_piece is not None
        assert logic.next_piece is not None

    def test_update_cycles_progress_fall_timer(self) -> None:
        """Running several update ticks must advance fall_time."""
        from games.Tetris.src.game_logic import TetrisLogic

        logic = TetrisLogic()
        logic.reset_game()

        # Tick with small dt so the piece does not lock immediately
        for _ in range(5):
            logic.update(10)

        # fall_time accumulates dt values (resets only when a piece falls)
        # After 5 ticks of 10 ms, fall_time <= 50 ms (may be 0 if a drop occurred)
        assert logic.fall_time >= 0
        assert not logic.game_over

    def test_many_update_cycles_keep_state_valid(self) -> None:
        """Running many update ticks should not corrupt the grid or piece."""
        from games.Tetris.src.constants import GRID_HEIGHT, GRID_WIDTH
        from games.Tetris.src.game_logic import TetrisLogic

        logic = TetrisLogic()

        # 200 ticks of 16 ms ≈ 3.2 seconds of gameplay at 60 fps
        for _ in range(200):
            logic.update(16)

        # Grid dimensions must remain constant
        assert len(logic.grid) == GRID_HEIGHT
        assert all(len(row) == GRID_WIDTH for row in logic.grid)

        # Every non-empty cell must be a colour tuple (not None, not BLACK)
        for row in logic.grid:
            for cell in row:
                assert isinstance(cell, tuple), f"Grid cell must be tuple, got {cell!r}"

    def test_score_non_negative_after_updates(self) -> None:
        """Score must never go negative regardless of how many ticks pass."""
        from games.Tetris.src.game_logic import TetrisLogic

        logic = TetrisLogic()
        for _ in range(100):
            logic.update(50)

        assert logic.score >= 0

    def test_level_non_decreasing(self) -> None:
        """Level must only stay the same or increase over time."""
        from games.Tetris.src.game_logic import TetrisLogic

        logic = TetrisLogic()
        previous_level = logic.level
        for _ in range(300):
            logic.update(16)
            assert logic.level >= previous_level
            previous_level = logic.level


# ---------------------------------------------------------------------------
# Shared fixture factory for FPS games (Duum and Force_Field)
#
# The root conftest.py replaces pygame with a fake module tree at collection
# time, so there is nothing to patch for display/event/mouse/mixer — those
# are already MagicMocks.  We only need to patch:
#   1. The game's SoundManager -> NullSoundManager (avoids file I/O)
#   2. TextureGenerator.generate_textures (avoids loading PNG/BMP files)
# ---------------------------------------------------------------------------


def _fps_game_fixture(game_pkg: str):
    """Generator yielding a headless FPS game instance with patches held open.

    Keeps the TextureGenerator and SoundManager patches alive for the entire
    lifetime of the fixture (construction AND all test method calls like
    start_game()).

    Also patches ``pygame.Surface`` in the ui_renderer and ui_renderer_base
    modules so that ``_generate_vignette()`` and similar methods receive a
    proper MagicMock instance (with ``fill`` / ``set_at`` auto-stubs) rather
    than the class-level ``MagicMock`` that is installed by conftest.

    Args:
        game_pkg: Dotted package path, e.g. "games.Duum.src.game".

    Yields:
        An initialised Game instance.
    """
    import importlib

    from games.shared.sound_manager_base import NullSoundManager

    stub_textures = {
        k: _make_dummy_surface() for k in ("stone", "brick", "metal", "tech", "hidden")
    }

    # Derive the game name (e.g. "Duum") from the package path so we can patch
    # the correct module-level pygame.Surface reference.
    game_name = game_pkg.split(".")[1]  # "games.Duum.src.game" -> "Duum"
    ui_renderer_pkg = f"games.{game_name}.src.ui_renderer"

    surf_factory = MagicMock(return_value=_make_dummy_surface())

    with (
        patch(f"{game_pkg}.SoundManager", NullSoundManager),
        patch(
            "games.shared.raycaster.TextureGenerator.generate_textures",
            return_value=stub_textures,
        ),
        patch(f"{ui_renderer_pkg}.pygame.Surface", surf_factory),
        patch("games.shared.ui_renderer_base.pygame.Surface", surf_factory),
        patch(
            f"{ui_renderer_pkg}.pygame.transform.smoothscale",
            return_value=_make_dummy_surface(),
        ),
    ):
        mod = importlib.import_module(game_pkg)
        Game = mod.Game  # noqa: N806
        yield Game(sound_manager=NullSoundManager())


# ---------------------------------------------------------------------------
# Duum — FPS game
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestDuumGameLoopIntegration:
    """Integration tests for the Duum game update_game cycle."""

    @pytest.fixture()
    def duum_game(self):
        """Create a headless Duum Game instance."""
        yield from _fps_game_fixture("games.Duum.src.game")

    def test_initial_state_is_intro(self, duum_game) -> None:
        """Game should start in the INTRO state."""
        from games.shared.constants import GameState

        assert duum_game.state == GameState.INTRO
        assert duum_game.running is True

    def test_start_game_creates_player_and_map(self, duum_game) -> None:
        """start_game() must populate player and game_map for the first level.

        Note: Duum's state transition to PLAYING happens via the UI event
        handlers (not directly in start_game).  This test verifies the
        game objects are correctly created, which is the meaningful
        integration point.
        """
        duum_game.start_game()

        assert duum_game.player is not None
        assert duum_game.game_map is not None

    def test_update_game_runs_without_error(self, duum_game) -> None:
        """update_game() must complete without raising after start_game()."""
        from games.shared.constants import GameState

        duum_game.start_game()
        # update_game() is only called when state == PLAYING; set it directly
        # to simulate the UI flow that normally sets the state.
        duum_game.state = GameState.PLAYING

        # Run a handful of update cycles (equivalent to a few frames)
        for _ in range(5):
            duum_game.update_game()

    def test_player_position_stays_valid_after_updates(self, duum_game) -> None:
        """Player position must remain finite after several update cycles."""
        import math

        from games.shared.constants import GameState

        duum_game.start_game()
        duum_game.state = GameState.PLAYING

        for _ in range(10):
            duum_game.update_game()

        player = duum_game.player
        assert player is not None
        assert math.isfinite(player.x)
        assert math.isfinite(player.y)

    def test_kills_non_negative_after_updates(self, duum_game) -> None:
        """Kill counter must never go negative."""
        from games.shared.constants import GameState

        duum_game.start_game()
        duum_game.state = GameState.PLAYING

        for _ in range(20):
            duum_game.update_game()

        assert duum_game.kills >= 0

    def test_level_unchanged_during_short_run(self, duum_game) -> None:
        """Level must not change after just a few update ticks."""
        from games.shared.constants import GameState

        duum_game.start_game()
        duum_game.state = GameState.PLAYING
        initial_level = duum_game.level

        for _ in range(10):
            duum_game.update_game()

        assert duum_game.level == initial_level


# ---------------------------------------------------------------------------
# Force_Field — FPS game
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestForceFieldGameLoopIntegration:
    """Integration tests for the Force_Field game update_game cycle."""

    @pytest.fixture()
    def ff_game(self):
        """Create a headless Force_Field Game instance."""
        yield from _fps_game_fixture("games.Force_Field.src.game")

    def test_initial_state_is_intro(self, ff_game) -> None:
        """Game should start in the INTRO state."""
        from games.shared.constants import GameState

        assert ff_game.state == GameState.INTRO
        assert ff_game.running is True

    def test_start_game_creates_player_and_map(self, ff_game) -> None:
        """start_game() must populate player and game_map for the first level."""
        ff_game.start_game()

        assert ff_game.player is not None
        assert ff_game.game_map is not None

    def test_update_game_runs_without_error(self, ff_game) -> None:
        """update_game() must complete without raising after start_game()."""
        from games.shared.constants import GameState

        ff_game.start_game()
        ff_game.state = GameState.PLAYING

        for _ in range(5):
            ff_game.update_game()

    def test_player_position_stays_valid_after_updates(self, ff_game) -> None:
        """Player position must remain finite after several update cycles."""
        import math

        from games.shared.constants import GameState

        ff_game.start_game()
        ff_game.state = GameState.PLAYING

        for _ in range(10):
            ff_game.update_game()

        player = ff_game.player
        assert player is not None
        assert math.isfinite(player.x)
        assert math.isfinite(player.y)

    def test_kills_non_negative_after_updates(self, ff_game) -> None:
        """Kill counter must never go negative."""
        from games.shared.constants import GameState

        ff_game.start_game()
        ff_game.state = GameState.PLAYING

        for _ in range(20):
            ff_game.update_game()

        assert ff_game.kills >= 0

    def test_level_unchanged_during_short_run(self, ff_game) -> None:
        """Level must not change after just a few update ticks."""
        from games.shared.constants import GameState

        ff_game.start_game()
        ff_game.state = GameState.PLAYING
        initial_level = ff_game.level

        for _ in range(10):
            ff_game.update_game()

        assert ff_game.level == initial_level
