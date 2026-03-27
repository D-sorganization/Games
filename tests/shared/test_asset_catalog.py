"""Tests for AssetCatalog — path resolution, JSON loading, caching."""

import json

import pytest

from games.shared.asset_catalog import AssetCatalog
from games.shared.contracts import ContractViolation

# --- Construction ---


class TestConstruction:
    def test_base_dir(self, tmp_path):
        catalog = AssetCatalog(tmp_path)
        assert catalog.base_dir == tmp_path

    def test_assets_dir(self, tmp_path):
        catalog = AssetCatalog(tmp_path)
        assert catalog.assets_dir == tmp_path / "assets"

    def test_none_base_raises(self):
        with pytest.raises(ContractViolation):
            AssetCatalog(None)


# --- Path Resolution ---


class TestPathResolution:
    def test_resolve_path(self, tmp_path):
        catalog = AssetCatalog(tmp_path)
        p = catalog.resolve_path("images", "bg.png")
        assert p == tmp_path / "assets" / "images" / "bg.png"

    def test_exists_nonexistent(self, tmp_path):
        catalog = AssetCatalog(tmp_path)
        assert not catalog.exists("nope.txt")

    def test_exists_real_file(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "test.txt").write_text("hello")
        catalog = AssetCatalog(tmp_path)
        assert catalog.exists("test.txt")


# --- JSON Loading ---


class TestJsonLoading:
    def test_load_json_from_data_subdir(self, tmp_path):
        data_dir = tmp_path / "assets" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "config.json").write_text(
            json.dumps({"key": "value"}), encoding="utf-8"
        )
        catalog = AssetCatalog(tmp_path)
        result = catalog.load_json("config.json")
        assert result == {"key": "value"}

    def test_load_json_fallback_to_assets_root(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "levels.json").write_text(json.dumps({"level": 1}), encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        result = catalog.load_json("levels.json")
        assert result == {"level": 1}

    def test_load_json_nonexistent(self, tmp_path):
        catalog = AssetCatalog(tmp_path)
        assert catalog.load_json("missing.json") is None

    def test_load_json_invalid(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "bad.json").write_text("not json!", encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        assert catalog.load_json("bad.json") is None


# --- Text Loading ---


class TestTextLoading:
    def test_load_text(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "readme.txt").write_text("hello world", encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        assert catalog.load_text("readme.txt") == "hello world"

    def test_load_text_nonexistent(self, tmp_path):
        catalog = AssetCatalog(tmp_path)
        assert catalog.load_text("nope.txt") is None


# --- Caching ---


class TestCaching:
    def test_cache_size_grows(self, tmp_path):
        data_dir = tmp_path / "assets" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "a.json").write_text("{}", encoding="utf-8")
        (data_dir / "b.json").write_text("{}", encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        assert catalog.cache_size == 0
        catalog.load_json("a.json")
        assert catalog.cache_size == 1
        catalog.load_json("b.json")
        assert catalog.cache_size == 2

    def test_cache_returns_same_object(self, tmp_path):
        data_dir = tmp_path / "assets" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "c.json").write_text('{"x": 1}', encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        first = catalog.load_json("c.json")
        second = catalog.load_json("c.json")
        assert first is second

    def test_clear_cache(self, tmp_path):
        data_dir = tmp_path / "assets" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "d.json").write_text("{}", encoding="utf-8")
        catalog = AssetCatalog(tmp_path)
        catalog.load_json("d.json")
        assert catalog.cache_size == 1
        catalog.clear_cache()
        assert catalog.cache_size == 0
