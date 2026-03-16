from games.Zombie_Survival.src.map import Map


def test_map_init():
    """Test Zombie Survival map initialization."""
    game_map = Map(size=10)
    assert game_map.size == 10
    assert len(game_map.grid) == 10
