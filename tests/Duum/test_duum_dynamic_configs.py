from games.Duum.src import constants as C


def test_duum_weapons_loaded_from_json():
    assert C.WEAPONS is not None
    assert isinstance(C.WEAPONS, dict)
    assert "pistol" in C.WEAPONS
    assert "damage" in C.WEAPONS["pistol"]
    assert C.WEAPONS["pistol"]["damage"] == 25


def test_duum_enemies_loaded_from_json():
    assert C.ENEMY_TYPES is not None
    assert isinstance(C.ENEMY_TYPES, dict)
    assert "zombie" in C.ENEMY_TYPES


def test_duum_wall_colors_exist():
    assert C.WALL_COLORS is not None
    assert 1 in C.WALL_COLORS
