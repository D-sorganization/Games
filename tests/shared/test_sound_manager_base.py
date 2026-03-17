"""Tests for games.shared.sound_manager_base module.

Tests both SoundManagerBase and NullSoundManager using mocked pygame.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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

    @patch("games.shared.sound_manager_base.pygame.mixer")
    @patch("games.shared.sound_manager_base.Path")
    def test_init_and_load_assets(self, mock_path, mock_mixer):
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_cwd = MagicMock()
        mock_path.cwd.return_value = mock_path_cwd
        resolved = mock_path.return_value.resolve.return_value
        resolved.parent.parent.__truediv__.return_value = mock_path_instance
        mock_path_instance.__truediv__.return_value = mock_path_instance

        # Mock file exists
        mock_path_instance.exists.return_value = True

        class MySoundManager(SoundManagerBase):
            SOUND_FILES = {
                "boom": "boom.wav",
                "music_level": "music.wav",
                "ambient": "amb.wav",
            }

            def get_game_name(self):
                return "MyGame"

        # Test success mapping
        _SOUND = "games.shared.sound_manager_base.pygame.mixer.Sound"
        with patch(_SOUND) as mock_sound_cls:
            mock_snd = MagicMock()
            mock_sound_cls.return_value = mock_snd
            mgr = MySoundManager()
            assert "boom" in mgr.sounds
            assert "music_level" in mgr.sounds
            assert "ambient" in mgr.sounds

            # volume lowered for music and ambient
            mock_snd.set_volume.assert_called_with(0.5)

        # Test failure loading sound (Exception caught)
        _SOUND = "games.shared.sound_manager_base.pygame.mixer.Sound"
        with patch(_SOUND, side_effect=Exception("Codec error")):
            mgr2 = MySoundManager()
            assert not mgr2.sounds  # nothing loaded

        # Test path doesn't exist
        mock_path_instance.exists.return_value = False
        mgr3 = MySoundManager()
        assert not mgr3.sounds

    def test_play_sound_exception(self) -> None:
        """play_sound should catch exceptions during playback."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_sound = MagicMock()
        mock_sound.play.side_effect = Exception("error")
        mgr.sounds = {"boom": mock_sound}
        mgr.sound_enabled = True
        mgr.play_sound("boom")  # Should catch the error cleanly

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

    def test_start_music_unknown_key(self) -> None:
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sounds = {}
        mgr.sound_enabled = True
        mgr.current_music = None
        mgr.start_music("nonexistent")
        assert mgr.current_music is None

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

    def test_stop_music_ambient_fallback(self) -> None:
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_ambient = MagicMock()
        mgr.sounds = {"ambient": mock_ambient}
        mgr.sound_enabled = True
        mgr.current_music = None
        mgr.stop_music()
        mock_ambient.stop.assert_called_once()

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

    def test_pause_unpause_disabled(self) -> None:
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sound_enabled = False
        mgr.pause_all()
        mgr.unpause_all()
