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
        m = Map(size=20)
        assert m._is_valid_map() is True

    def test_walkable_area_sufficient(self) -> None:
        m = Map(size=20)
        walkable = sum(
            1 for i in range(m.size) for j in range(m.size) if m.grid[i][j] == 0
        )
        min_walkable = int(m.size * m.size * 0.15)
        assert walkable >= min_walkable

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
