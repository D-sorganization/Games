from .constants import GOLD, SILVER

class Particle:
    """Visual particle effect"""

    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        velocity_x: float,
        velocity_y: float,
    ) -> None:
        """Initialize particle with position, color, and velocity"""
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.lifetime = 60
        self.alpha = 255

    def update(self) -> None:
        """Update particle position and lifetime"""
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.2  # Gravity
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 60) * 255)

    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.lifetime > 0


class ScorePopup:
    """Score notification popup"""

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = GOLD,
    ) -> None:
        """Initialize score popup with text, position, and color"""
        self.text = text
        self.x = x
        self.y = y
        self.start_y = y
        self.color = color
        self.lifetime = 90
        self.alpha = 255

    def update(self) -> None:
        """Update popup position and lifetime"""
        self.y -= 1
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 90) * 255)

    def is_alive(self) -> bool:
        """Check if popup is still alive"""
        return self.lifetime > 0
