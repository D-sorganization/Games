"""Tests for the games.shared.projectile_base module."""

from __future__ import annotations

import math

import pytest

from games.shared.contracts import ContractViolation
from games.shared.projectile_base import ProjectileBase
from tests.conftest import MockMap

# Reuse small maps from conftest via fixtures
# Also create a map with a secret wall for testing


def _secret_wall_map() -> MockMap:
    """Map with a secret wall (type 5) at position (4, 5)."""
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 5, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    return MockMap(grid)


class TestProjectileInit:
    """Tests for ProjectileBase initialization."""

    def test_init_sets_position(self) -> None:
        """Projectile should store initial position."""
        p = ProjectileBase(3.0, 7.0, 0.0, damage=25, speed=1.0)
        assert p.x == pytest.approx(3.0)
        assert p.y == pytest.approx(7.0)

    def test_init_sets_angle(self) -> None:
        """Projectile should store direction angle."""
        p = ProjectileBase(0.0, 0.0, math.pi / 4, damage=10, speed=1.0)
        assert p.angle == pytest.approx(math.pi / 4)

    def test_init_sets_damage_and_speed(self) -> None:
        """Projectile should store damage and speed."""
        p = ProjectileBase(0.0, 0.0, 0.0, damage=50, speed=2.5)
        assert p.damage == 50
        assert p.speed == pytest.approx(2.5)

    def test_init_alive_by_default(self) -> None:
        """Projectile should be alive on creation."""
        p = ProjectileBase(0.0, 0.0, 0.0, damage=10, speed=1.0)
        assert p.alive is True

    def test_init_default_values(self) -> None:
        """Default optional values should be sensible."""
        p = ProjectileBase(0.0, 0.0, 0.0, damage=10, speed=1.0)
        assert p.is_player is False
        assert p.color == (255, 0, 0)
        assert p.size == pytest.approx(0.2)
        assert p.weapon_type == "normal"
        assert p.z == pytest.approx(0.5)
        assert p.vz == pytest.approx(0.0)
        assert p.gravity == pytest.approx(0.0)

    def test_init_custom_values(self) -> None:
        """Custom optional values should be stored."""
        p = ProjectileBase(
            0.0,
            0.0,
            0.0,
            damage=30,
            speed=3.0,
            is_player=True,
            color=(0, 255, 0),
            size=0.5,
            weapon_type="plasma",
            z=1.0,
            vz=0.1,
            gravity=0.01,
        )
        assert p.is_player is True
        assert p.color == (0, 255, 0)
        assert p.weapon_type == "plasma"
        assert p.gravity == pytest.approx(0.01)


class TestProjectileContracts:
    """Tests for ProjectileBase contract validation."""

    def test_rejects_negative_damage(self) -> None:
        """Should reject negative damage."""
        with pytest.raises(ContractViolation, match="damage"):
            ProjectileBase(0.0, 0.0, 0.0, damage=-5, speed=1.0)

    def test_accepts_zero_damage(self) -> None:
        """Zero damage should be accepted (e.g., for visual effects)."""
        p = ProjectileBase(0.0, 0.0, 0.0, damage=0, speed=1.0)
        assert p.damage == 0

    def test_rejects_zero_speed(self) -> None:
        """Should reject zero speed."""
        with pytest.raises(ContractViolation, match="speed"):
            ProjectileBase(0.0, 0.0, 0.0, damage=10, speed=0.0)

    def test_rejects_negative_speed(self) -> None:
        """Should reject negative speed."""
        with pytest.raises(ContractViolation, match="speed"):
            ProjectileBase(0.0, 0.0, 0.0, damage=10, speed=-1.0)


class TestProjectileUpdate:
    """Tests for projectile movement and collision."""

    @pytest.mark.parametrize(
        "angle,expected_dx_sign,expected_dy_sign",
        [
            (0.0, 1, 0),
            (math.pi / 2, 0, 1),
            (math.pi, -1, 0),
            (3 * math.pi / 2, 0, -1),
        ],
        ids=["east", "south", "west", "north"],
    )
    def test_update_moves_in_direction(
        self,
        open_map: MockMap,
        angle: float,
        expected_dx_sign: int,
        expected_dy_sign: int,
    ) -> None:
        """Projectile should move in the direction of its angle."""
        p = ProjectileBase(5.0, 5.0, angle, damage=10, speed=0.5)
        initial_x, initial_y = p.x, p.y
        p.update(open_map)

        if expected_dx_sign != 0:
            assert (p.x - initial_x) * expected_dx_sign > 0
        if expected_dy_sign != 0:
            assert (p.y - initial_y) * expected_dy_sign > 0

    def test_update_dies_on_wall_collision(self, open_map: MockMap) -> None:
        """Projectile should die when hitting a wall."""
        # Position near east wall, heading east
        p = ProjectileBase(8.5, 5.0, 0.0, damage=10, speed=1.0)
        p.update(open_map)
        assert p.alive is False

    def test_update_stays_alive_in_open_space(self, open_map: MockMap) -> None:
        """Projectile should stay alive in open space."""
        p = ProjectileBase(5.0, 5.0, 0.0, damage=10, speed=0.3)
        p.update(open_map)
        assert p.alive is True

    def test_update_skips_when_dead(self, open_map: MockMap) -> None:
        """Dead projectile should not move."""
        p = ProjectileBase(5.0, 5.0, 0.0, damage=10, speed=1.0)
        p.alive = False
        old_x = p.x
        p.update(open_map)
        assert p.x == pytest.approx(old_x)

    def test_secret_wall_tracking(self) -> None:
        """Hit on secret wall (type 5) should record position."""
        m = _secret_wall_map()
        # Near (4, 5) heading east
        p = ProjectileBase(3.5, 5.5, 0.0, damage=10, speed=1.0)
        p.update(m)
        assert p.alive is False
        assert p.hit_secret_pos is not None
        assert p.hit_secret_pos == (4, 5)

    def test_no_secret_pos_on_normal_wall(self, open_map: MockMap) -> None:
        """Normal wall hit should not set hit_secret_pos."""
        p = ProjectileBase(8.5, 5.0, 0.0, damage=10, speed=1.0)
        p.update(open_map)
        assert p.hit_secret_pos is None


class TestProjectilePhysics:
    """Tests for 3D arc physics (gravity, vz)."""

    def test_gravity_reduces_z(self, open_map: MockMap) -> None:
        """Gravity should reduce vertical velocity and height."""
        p = ProjectileBase(
            5.0, 5.0, 0.0, damage=10, speed=0.3, z=1.0, vz=-0.05, gravity=0.1
        )
        p.update(open_map)
        assert p.z < 1.0
        assert p.vz < -0.05

    def test_vz_adds_height(self, open_map: MockMap) -> None:
        """Positive vz should increase height."""
        p = ProjectileBase(
            5.0, 5.0, 0.0, damage=10, speed=0.3, z=0.5, vz=0.2, gravity=0.0
        )
        p.update(open_map)
        assert p.z == pytest.approx(0.7)

    def test_bomb_dies_on_ground(self, open_map: MockMap) -> None:
        """Bomb should die when hitting the ground."""
        p = ProjectileBase(
            5.0,
            5.0,
            0.0,
            damage=10,
            speed=0.3,
            weapon_type="bomb",
            z=0.05,
            vz=-0.1,
            gravity=0.0,
        )
        p.update(open_map)
        assert p.alive is False

    def test_freezer_dies_on_ground(self, open_map: MockMap) -> None:
        """Freezer should die when hitting the ground."""
        p = ProjectileBase(
            5.0,
            5.0,
            0.0,
            damage=0,
            speed=0.3,
            weapon_type="freezer",
            z=0.05,
            vz=-0.1,
            gravity=0.0,
        )
        p.update(open_map)
        assert p.alive is False

    def test_normal_survives_ground(self, open_map: MockMap) -> None:
        """Normal projectile should survive touching ground."""
        p = ProjectileBase(
            5.0,
            5.0,
            0.0,
            damage=10,
            speed=0.3,
            weapon_type="normal",
            z=0.05,
            vz=-0.1,
            gravity=0.0,
        )
        p.update(open_map)
        # Ground clips to 0 but normal types survive
        assert p.alive is True
        assert p.z == pytest.approx(0.0)
