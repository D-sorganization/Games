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
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sound_enabled = True
        mgr.sounds = {}
        mgr.current_music = None
        with patch("games.shared.sound_manager_base.pygame.mixer.pause") as mock_pause:
            mgr.pause_all()
            mock_pause.assert_called()

    def test_unpause_all_calls_mixer(self) -> None:
        """unpause_all should call pygame.mixer.unpause when enabled."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sound_enabled = True
        mgr.sounds = {}
        mgr.current_music = None
        with patch(
            "games.shared.sound_manager_base.pygame.mixer.unpause"
        ) as mock_unpause:
            mgr.unpause_all()
            mock_unpause.assert_called()

    def test_init_calls_mixer_and_load_assets(self) -> None:
        """__init__ configures pygame.mixer and calls load_assets."""
        with (
            patch("pygame.mixer.quit") as mock_quit,
            patch("pygame.mixer.pre_init") as mock_pre,
            patch("pygame.mixer.init") as mock_init,
            patch("pygame.mixer.set_num_channels") as mock_channels,
            patch.object(SoundManagerBase, "load_assets") as mock_load,
        ):
            mgr = SoundManagerBase()
            mock_quit.assert_called_once()
            mock_pre.assert_called_once_with(44100, -16, 2, 512)
            mock_init.assert_called_once()
            mock_channels.assert_called_once_with(32)
            mock_load.assert_called_once()
            assert mgr.sounds == {}
            assert mgr.sound_enabled is True

    def test_load_assets(self, tmp_path) -> None:
        """load_assets should find and load sounds from the mapped dict."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.SOUND_FILES = {"boom": "boom.wav", "ambient": "bg.wav"}
        mgr.sounds = {}

        # We need a fake directory structure
        game_name = "MockGame"
        base_dir = tmp_path / game_name
        sound_dir = base_dir / "assets" / "sounds"
        sound_dir.mkdir(parents=True)
        (sound_dir / "boom.wav").write_bytes(b"DATA")
        (sound_dir / "bg.wav").write_bytes(b"DATA")

        mock_sound = MagicMock()
        mock_ambient = MagicMock()

        def fake_sound(path):
            if "bg.wav" in str(path):
                return mock_ambient
            return mock_sound

        with (
            patch.object(mgr, "get_game_name", return_value=game_name),
            patch("pathlib.Path.resolve", return_value=tmp_path / "foo" / "mock.py"),
            patch("pygame.mixer.Sound", side_effect=fake_sound),
        ):
            mgr.load_assets()

        assert "boom" in mgr.sounds
        assert "ambient" in mgr.sounds
        # Ambient should have volume lowered
        mock_ambient.set_volume.assert_called_once_with(0.5)
        # Boom should not
        mock_sound.set_volume.assert_not_called()

    def test_load_assets_missing_file_and_exception(self, tmp_path) -> None:
        """load_assets should handle missing files and exceptions."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.SOUND_FILES = {"missing": "no.wav", "bad": "bad.wav"}
        mgr.sounds = {}

        # Only bad.wav exists, but fails to load
        sound_dir = tmp_path / "MockGame" / "assets" / "sounds"
        sound_dir.mkdir(parents=True)
        (sound_dir / "bad.wav").write_bytes(b"DATA")

        with (
            patch.object(mgr, "get_game_name", return_value="MockGame"),
            patch("pathlib.Path.resolve", return_value=tmp_path / "foo" / "mock.py"),
            patch("pygame.mixer.Sound", side_effect=OSError("codec fail")),
        ):
            mgr.load_assets()

        # Neigher should log successfully
        assert mgr.sounds == {}

    def test_play_sound_catches_exception(self) -> None:
        """play_sound should catch and log exceptions."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_sound = MagicMock()
        mock_sound.play.side_effect = RuntimeError("audio device fail")
        mgr.sounds = {"boom": mock_sound}
        mgr.sound_enabled = True

        # Should not raise exception
        mgr.play_sound("boom")

    def test_pause_unpause_disabled(self) -> None:
        """pause and unpause do nothing if sound_enabled is False."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sound_enabled = False
        with (
            patch("pygame.mixer.pause") as mock_pause,
            patch("pygame.mixer.unpause") as mock_unpause,
        ):
            mgr.pause_all()
            mgr.unpause_all()
            mock_pause.assert_not_called()
            mock_unpause.assert_not_called()

    def test_stop_music_ambient_fallback(self) -> None:
        """stop_music should also stop 'ambient' if present."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mock_ambient = MagicMock()
        mgr.sounds = {"ambient": mock_ambient}
        mgr.current_music = None

        mgr.stop_music()
        mock_ambient.stop.assert_called_once()

    def test_start_music_unknown_name(self) -> None:
        """start_music does not change current_music if track is missing."""
        mgr = SoundManagerBase.__new__(SoundManagerBase)
        mgr.sounds = {}
        mgr.sound_enabled = True
        mgr.current_music = None

        mgr.start_music("missing_loop")
        assert mgr.current_music is None
