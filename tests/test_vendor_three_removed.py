"""Regression test for removing vendored Three.js sources."""

from pathlib import Path


def test_vendored_three_tree_is_absent() -> None:
    assert not Path("src/games/vendor/three").exists()
