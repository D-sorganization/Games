from unittest.mock import patch

from games.Force_Field.src.map import Map


def test_map_init():
    """Test map initialization and validation."""
    game_map = Map(size=10)
    assert game_map.size == 10
    assert len(game_map.grid) == 10
    assert game_map._is_valid_map()


def test_map_validation_retry():
    """Test that map generation recycles until a valid map is found."""
    with patch("games.Force_Field.src.map.MapBase.create_map") as mock_create:
        with patch.object(Map, "_is_valid_map", side_effect=[False, False, True]):
            # Test that it retried 3 times
            Map(size=10)
            assert mock_create.call_count == 3
