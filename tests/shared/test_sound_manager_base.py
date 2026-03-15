"""Tests for games.shared.sound_manager_base module.

Tests both SoundManagerBase and NullSoundManager using mocked pygame.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from games.shared.sound_manager_base import NullSoundManager, SoundManagerBase

# ---------------------------------------------------------------------------
# NullSoundManager (the easy one -- no real pygame needed)
# ---------------------------------------------------------------------------


class TestNullSoundManager:
    """Tests for the silent NullSoundManager."""

    def test_init_does_not_touch_mixer(self) -> None:
        """NullSoundManager should not call pygame.mixer."""
        mgr = NullSoundManager()
        assert mgr.sound_enabled is False
        assert mgr.sounds == {}
        assert mgr.current_music is None

    def test_play_sound_is_noop(self) -> None:
        """play_sound should be a silent no-op."""
        mgr = NullSoundManager()
        mgr.play_sound("nonexistent")  # Should not raise

    def test_start_music_is_noop(self) -> None:
        """start_music should be a silent no-op."""
        mgr = NullSoundManager()
        mgr.start_music("music_loop")

    def test_stop_music_is_noop(self) -> None:
        """stop_music should be a silent no-op."""
        mgr = NullSoundManager()
        mgr.stop_music()

    def test_pause_all_is_noop(self) -> None:
        """pause_all should be a silent no-op."""
        mgr = NullSoundManager()
        mgr.pause_all()

    def test_unpause_all_is_noop(self) -> None:
        """unpause_all should be a silent no-op."""
        mgr = NullSoundManager()
        mgr.unpause_all()

    def test_load_assets_is_noop(self) -> None:
        """load_assets should be a silent no-op."""
        mgr = NullSoundManager()
        mgr.load_assets()


# ---------------------------------------------------------------------------
# SoundManagerBase
# ---------------------------------------------------------------------------


class TestSoundManagerBase:
    """Tests for SoundManagerBase core logic."""

    def test_play_sound_disabled(self) -> None:
        """play_sound should do nothing when sound is disabled."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sounds = {}
        mgr.sound_enabled = False
        mgr.current_music = None
        mgr.play_sound("boom")  # Should not raise

    def test_play_sound_existing_key(self) -> None:
        """play_sound should call .play() on a known sound."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_sound = MagicMock()
        mgr.sounds = {"boom": mock_sound}
        mgr.sound_enabled = True
        mgr.current_music = None
        mgr.play_sound("boom")
        mock_sound.play.assert_called_once()

    def test_play_sound_unknown_key(self) -> None:
        """play_sound with unknown key should be a no-op."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sounds = {}
        mgr.sound_enabled = True
        mgr.current_music = None
        mgr.play_sound("nonexistent")

    def test_start_music_plays_loop(self) -> None:
        """start_music should call .play(loops=-1) on known sound."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_sound = MagicMock()
        mgr.sounds = {"music_loop": mock_sound}
        mgr.sound_enabled = True
        mgr.current_music = None
        mgr.start_music("music_loop")
        mock_sound.play.assert_called_once_with(loops=-1)
        assert mgr.current_music == "music_loop"

    def test_start_music_disabled(self) -> None:
        """start_music should do nothing when sound is disabled."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sounds = {"music_loop": MagicMock()}
        mgr.sound_enabled = False
        mgr.current_music = None
        mgr.start_music("music_loop")
        assert mgr.current_music is None

    def test_stop_music_stops_current(self) -> None:
        """stop_music should call .stop() on current music sound."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_sound = MagicMock()
        mgr.sounds = {"track1": mock_sound}
        mgr.sound_enabled = True
        mgr.current_music = "track1"
        mgr.stop_music()
        mock_sound.stop.assert_called_once()

    def test_stop_music_no_current(self) -> None:
        """stop_music with no current music should not raise."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sounds = {}
        mgr.sound_enabled = True
        mgr.current_music = None
        mgr.stop_music()

    def test_get_game_name_from_module(self) -> None:
        """get_game_name should extract game name from module path."""

        class FakeManager(SoundManagerBase):
            __module__ = "src.games.Duum.src.sound"

            def __init__(self) -> None:
                self.sounds: dict = {}
                self.music_channel = None
                self.sound_enabled = False
                self.current_music = None

        mgr = FakeManager()
        assert mgr.get_game_name() == "Duum"

    def test_get_game_name_unknown_module(self) -> None:
        """get_game_name should return 'unknown' for unrecognized paths."""

        class FakeManager(SoundManagerBase):
            __module__ = "something.else"

            def __init__(self) -> None:
                self.sounds: dict = {}
                self.music_channel = None
                self.sound_enabled = False
                self.current_music = None

        mgr = FakeManager()
        assert mgr.get_game_name() == "unknown"

    def test_pause_all_calls_mixer(self) -> None:
        """pause_all should call pygame.mixer.pause when enabled."""
        import pygame

        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sound_enabled = True
        mgr.sounds = {}
        mgr.current_music = None
        mgr.pause_all()
        pygame.mixer.pause.assert_called()

    def test_unpause_all_calls_mixer(self) -> None:
        """unpause_all should call pygame.mixer.unpause when enabled."""
        import pygame

        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sound_enabled = True
        mgr.sounds = {}
        mgr.current_music = None
        mgr.unpause_all()
        pygame.mixer.unpause.assert_called()
