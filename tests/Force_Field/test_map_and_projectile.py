"""Tests for games.Force_Field.src.map."""

from __future__ import annotations

from games.Force_Field.src.map import Map


class TestFFMap:
    def test_init_creates_valid_grid(self) -> None:
        m = Map(size=20)
        assert m.grid is not None
        assert len(m.grid) == 20
        assert len(m.grid[0]) == 20

    def test_is_valid_map_passes_quality_check(self) -> None:
        """Validate that _is_valid_map correctly returns True when there
        are enough walkable tiles (>= 15% of total)."""
        from games.Force_Field.src.map import Map

        # Create a Map and manually manipulate the grid to guarantee validity
        m = Map(size=10)
        m.grid = [[0] * 10 for _ in range(10)]  # 100% walkable
        assert m._is_valid_map() is True

    def test_is_invalid_map_fails_quality_check(self) -> None:
        """Verify _is_valid_map returns False when fewer than 15% are walkable."""
        m = Map(size=10)
        m.grid = [[1] * 10 for _ in range(10)]  # 0% walkable
        assert m._is_valid_map() is False

    def test_grid_contains_walls_and_floors(self) -> None:
        """Map should have both wall (!=0) and floor (0) tiles."""
        m = Map(size=20)
        total = m.size * m.size
        walls = sum(
            1 for i in range(m.size) for j in range(m.size) if m.grid[i][j] != 0
        )
        floors = total - walls
        assert floors > 0  # At least some passable space
        assert walls > 0  # At least some walls

    def test_default_size(self) -> None:
        from games.Force_Field.src.constants import DEFAULT_MAP_SIZE

        m = Map()
        assert m.size == DEFAULT_MAP_SIZE


class TestFFProjectile:
    def test_init_creates_projectile(self) -> None:
        from games.Force_Field.src.projectile import Projectile

        p = Projectile(1.0, 2.0, 0.0, speed=0.5, damage=25)
        assert p.x == 1.0
        assert p.y == 2.0
        assert p.damage == 25

    def test_projectile_inherits_base(self) -> None:
        from games.Force_Field.src.projectile import Projectile
        from games.shared.projectile_base import ProjectileBase

        p = Projectile(1.0, 2.0, 0.0, speed=0.5, damage=10)
        assert isinstance(p, ProjectileBase)


class TestZSProjectile:
    def test_init_creates_projectile(self) -> None:
        from games.Zombie_Survival.src.projectile import Projectile

        p = Projectile(3.0, 4.0, 1.57, speed=0.3, damage=15)
        assert p.x == 3.0
        assert p.damage == 15

    def test_projectile_inherits_base(self) -> None:
        from games.shared.projectile_base import ProjectileBase
        from games.Zombie_Survival.src.projectile import Projectile

        p = Projectile(1.0, 2.0, 0.0, speed=0.5, damage=10)
        assert isinstance(p, ProjectileBase)
