"""Additional tests for AssetCatalog — sound and image loading paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from games.shared.asset_catalog import AssetCatalog


class TestSoundLoading:
    def test_load_sound_nonexistent_returns_none(self, tmp_path: Path) -> None:
        catalog = AssetCatalog(tmp_path)
        result = catalog.load_sound("doesnt_exist.wav")
        assert result is None

    def test_load_sound_existing_file(self, tmp_path: Path) -> None:
        sounds_dir = tmp_path / "assets" / "sounds"
        sounds_dir.mkdir(parents=True)
        sound_file = sounds_dir / "test.wav"
        sound_file.write_bytes(b"WAVE_DATA")

        mock_sound = MagicMock()
        with patch("pygame.mixer.Sound", return_value=mock_sound):
            catalog = AssetCatalog(tmp_path)
            result = catalog.load_sound("test.wav", volume=0.5)
        assert result is mock_sound
        mock_sound.set_volume.assert_called_once_with(0.5)

    def test_load_sound_cached_on_second_call(self, tmp_path: Path) -> None:
        sounds_dir = tmp_path / "assets" / "sounds"
        sounds_dir.mkdir(parents=True)
        (sounds_dir / "fx.wav").write_bytes(b"WAVE")

        mock_sound = MagicMock()
        with patch("pygame.mixer.Sound", return_value=mock_sound):
            catalog = AssetCatalog(tmp_path)
            first = catalog.load_sound("fx.wav")
            second = catalog.load_sound("fx.wav")
        assert first is second

    def test_load_sound_exception_returns_none(self, tmp_path: Path) -> None:
        sounds_dir = tmp_path / "assets" / "sounds"
        sounds_dir.mkdir(parents=True)
        (sounds_dir / "bad.wav").write_bytes(b"NOT_VALID_WAVE")

        with patch("pygame.mixer.Sound", side_effect=OSError("corrupt")):
            catalog = AssetCatalog(tmp_path)
            result = catalog.load_sound("bad.wav")
        assert result is None


class TestImageLoading:
    def test_load_image_nonexistent_returns_none(self, tmp_path: Path) -> None:
        catalog = AssetCatalog(tmp_path)
        result = catalog.load_image("missing.png")
        assert result is None

    def test_load_image_existing_with_alpha(self, tmp_path: Path) -> None:
        images_dir = tmp_path / "assets" / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "sprite.png").write_bytes(b"PNG_DATA")

        mock_surface = MagicMock()
        mock_surface.convert_alpha.return_value = mock_surface
        with (patch("pygame.image.load", return_value=mock_surface),):
            catalog = AssetCatalog(tmp_path)
            result = catalog.load_image("sprite.png", alpha=True)
        assert result is mock_surface
        mock_surface.convert_alpha.assert_called_once()

    def test_load_image_without_alpha(self, tmp_path: Path) -> None:
        images_dir = tmp_path / "assets" / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "bg.png").write_bytes(b"PNG_DATA")

        mock_surface = MagicMock()
        mock_surface.convert.return_value = mock_surface
        with patch("pygame.image.load", return_value=mock_surface):
            catalog = AssetCatalog(tmp_path)
            result = catalog.load_image("bg.png", alpha=False)
        assert result is mock_surface
        mock_surface.convert.assert_called_once()

    def test_load_image_cached(self, tmp_path: Path) -> None:
        images_dir = tmp_path / "assets" / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "cached.png").write_bytes(b"PNG_DATA")

        mock_surface = MagicMock()
        mock_surface.convert_alpha.return_value = mock_surface
        with patch("pygame.image.load", return_value=mock_surface):
            catalog = AssetCatalog(tmp_path)
            first = catalog.load_image("cached.png")
            second = catalog.load_image("cached.png")
        assert first is second

    def test_load_image_exception_returns_none(self, tmp_path: Path) -> None:
        images_dir = tmp_path / "assets" / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "bad.png").write_bytes(b"BAD_DATA")

        catalog = AssetCatalog(tmp_path)
        with patch("pygame.image.load", side_effect=ValueError("image decode fail")):
            result = catalog.load_image("bad_img.png")
            assert result is None

    def test_load_text_oserror(self, tmp_path) -> None:
        """load_text should catch OSError (e.g. reading a directory) and return None."""
        catalog = AssetCatalog(tmp_path)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir(exist_ok=True)
        test_dir = assets_dir / "protected.txt"
        test_dir.mkdir()
        result = catalog.load_text("protected.txt")
        assert result is None

    def test_load_image_exception(self, tmp_path) -> None:
        """load_image should catch Exception and return None."""
        catalog = AssetCatalog(tmp_path)
        img_dir = tmp_path / "assets" / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        bad_img = img_dir / "bad_img.png"
        bad_img.write_bytes(b"NOT A REAL IMAGE")

        with patch("pygame.image.load", side_effect=OSError("decode error")):
            result = catalog.load_image("bad_img.png")
            assert result is None


class TestTextCache:
    def test_load_text_cached(self, tmp_path: Path) -> None:
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "notes.txt").write_text("hello", encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        first = catalog.load_text("notes.txt")
        second = catalog.load_text("notes.txt")
        assert first is second
        assert catalog.cache_size == 1
