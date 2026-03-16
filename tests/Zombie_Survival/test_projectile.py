from games.Zombie_Survival.src.projectile import Projectile


def test_projectile_initialization():
    """Test initialization of Zombie Survival projectile."""
    x, y, angle, damage, speed = 10.0, 10.0, 0.0, 50, 5.0
    p = Projectile(x, y, angle, damage, speed)
    assert p.x == 10.0
    assert p.y == 10.0
    assert p.angle == 0.0
    assert p.damage == 50
    assert p.speed == 5.0
    assert p.alive
