import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

from games.shared.utils import try_move_entity


class MockMap:
    def __init__(self, size: int = 100) -> None:
        self.size = size

    def is_wall(self, x: float, y: float) -> bool:
        return not (0 <= x < self.size) or not (0 <= y < self.size)

class MockEntity:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.alive = True

class TestPhysicsProperties(unittest.TestCase):
    @given(
        start_x=st.floats(min_value=1.0, max_value=99.0,
                          allow_nan=False, allow_infinity=False),
        start_y=st.floats(min_value=1.0, max_value=99.0,
                          allow_nan=False, allow_infinity=False),
        dx=st.floats(min_value=-50.0, max_value=50.0,
                     allow_nan=False, allow_infinity=False),
        dy=st.floats(min_value=-50.0, max_value=50.0,
                     allow_nan=False, allow_infinity=False),
        radius=st.floats(min_value=0.1, max_value=5.0,
                         allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_try_move_entity_within_bounds(
        self, start_x: float, start_y: float, dx: float, dy: float, radius: float
    ) -> None:
        """Property: The entity should never move out of bounds (0 to 100)."""
        game_map = MockMap(100)
        entity = MockEntity(start_x, start_y)
        try_move_entity(entity, dx, dy, game_map, [], radius=radius)

        self.assertTrue(0 <= entity.x <= 100)
        self.assertTrue(0 <= entity.y <= 100)

    @given(
        start_x=st.floats(min_value=10.0, max_value=90.0),
        start_y=st.floats(min_value=10.0, max_value=90.0),
        dx=st.floats(min_value=-2.0, max_value=2.0),
        dy=st.floats(min_value=-2.0, max_value=2.0),
        ob_x=st.floats(min_value=10.0, max_value=90.0),
        ob_y=st.floats(min_value=10.0, max_value=90.0),
        radius=st.floats(min_value=0.5, max_value=1.5)
    )
    @settings(max_examples=100)
    def test_move_with_obstacles_no_clipping(
        self, start_x: float, start_y: float, dx: float, dy: float,
        ob_x: float, ob_y: float, radius: float
    ) -> None:
        """Property: Movement should not clip into an obstacle."""
        initial_d_sq = (start_x - ob_x)**2 + (start_y - ob_y)**2
        col_sq = radius * radius

        if initial_d_sq < col_sq + 1e-5:
            return

        game_map = MockMap(100)
        entity = MockEntity(start_x, start_y)
        obstacle = MockEntity(ob_x, ob_y)

        try_move_entity(entity, dx, dy, game_map, [obstacle], radius=radius)

        final_d_sq = (entity.x - ob_x)**2 + (entity.y - ob_y)**2

        self.assertTrue(
            final_d_sq >= col_sq - 1e-5,
            rf"Entity clipped through obstacle! {initial_d_sq} -\> {final_d_sq}"
        )

if __name__ == '__main__':
    unittest.main()
