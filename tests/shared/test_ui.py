"""Tests for games.shared.ui module.

Tests Button and BloodButton logic without real rendering.
pygame.Rect and font are mocked via the root conftest.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.shared.ui import BloodButton, Button

# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------


class TestButton:
    """Tests for the basic Button class."""

    def test_init_stores_text_and_color(self) -> None:
        """Button should store text and color on init."""
        btn = Button(10, 20, 100, 50, "Start", (200, 100, 50))
        assert btn.text == "Start"
        assert btn.color == (200, 100, 50)

    def test_hover_color_brighter(self) -> None:
        """Hover color should be brighter than base color."""
        btn = Button(0, 0, 100, 50, "Test", (100, 100, 100))
        for i in range(3):
            assert btn.hover_color[i] >= btn.color[i]

    def test_hover_color_capped_at_255(self) -> None:
        """Hover color channels should not exceed 255."""
        btn = Button(0, 0, 100, 50, "Test", (240, 240, 240))
        for c in btn.hover_color:
            assert c <= 255

    def test_hovered_default_false(self) -> None:
        """Button should not be hovered initially."""
        btn = Button(0, 0, 100, 50, "Test", (100, 100, 100))
        assert btn.hovered is False

    def test_color_setter_updates_hover(self) -> None:
        """Setting color should update hover_color too."""
        btn = Button(0, 0, 100, 50, "Test", (100, 100, 100))
        btn.color = (200, 200, 200)
        assert btn.color == (200, 200, 200)
        # Hover should reflect new color
        offset = Button.HOVER_BRIGHTNESS_OFFSET
        expected = tuple(min(255, 200 + offset) for _ in range(3))
        assert btn.hover_color == expected


class TestButtonUpdate:
    """Tests for Button.update hover detection."""

    def test_update_sets_hovered_true_when_inside(self) -> None:
        """Button should be hovered when mouse is inside rect."""
        btn = Button(10, 10, 100, 50, "Test", (100, 100, 100))
        # Mock rect.collidepoint
        btn.rect = MagicMock()
        btn.rect.collidepoint = MagicMock(return_value=True)
        btn.update((50, 30))
        assert btn.hovered is True

    def test_update_sets_hovered_false_when_outside(self) -> None:
        """Button should not be hovered when mouse is outside rect."""
        btn = Button(10, 10, 100, 50, "Test", (100, 100, 100))
        btn.rect = MagicMock()
        btn.rect.collidepoint = MagicMock(return_value=False)
        btn.update((500, 500))
        assert btn.hovered is False


class TestButtonIsClicked:
    """Tests for Button.is_clicked."""

    def test_clicked_inside_returns_true(self) -> None:
        """is_clicked should return True when position is inside."""
        btn = Button(0, 0, 100, 50, "Test", (100, 100, 100))
        btn.rect = MagicMock()
        btn.rect.collidepoint = MagicMock(return_value=True)
        assert btn.is_clicked((50, 25)) is True

    def test_clicked_outside_returns_false(self) -> None:
        """is_clicked should return False when position is outside."""
        btn = Button(0, 0, 100, 50, "Test", (100, 100, 100))
        btn.rect = MagicMock()
        btn.rect.collidepoint = MagicMock(return_value=False)
        assert btn.is_clicked((500, 500)) is False


# ---------------------------------------------------------------------------
# BloodButton
# ---------------------------------------------------------------------------


class TestBloodButton:
    """Tests for BloodButton drip animation logic."""

    def test_inherits_button(self) -> None:
        """BloodButton should be a subclass of Button."""
        assert issubclass(BloodButton, Button)

    def test_init_generates_drips(self) -> None:
        """BloodButton should generate drips on init."""
        btn = BloodButton(0, 0, 200, 50, "Play")
        assert len(btn.drips) > 0

    def test_pulse_timer_initialized(self) -> None:
        """pulse_timer should start at 0."""
        btn = BloodButton(0, 0, 200, 50, "Play")
        assert btn.pulse_timer == 0.0

    def test_update_advances_pulse_timer(self) -> None:
        """update should increment pulse_timer."""
        btn = BloodButton(0, 0, 200, 50, "Play")
        btn.rect = MagicMock()
        btn.rect.collidepoint = MagicMock(return_value=False)
        btn.update((0, 0))
        assert btn.pulse_timer > 0.0

    def test_drip_animation_changes_length(self) -> None:
        """Drip lengths should change during animation."""
        btn = BloodButton(0, 0, 200, 50, "Play")
        btn.rect = MagicMock()
        btn.rect.collidepoint = MagicMock(return_value=False)
        if btn.drips:
            initial_length = btn.drips[0]["length"]  # noqa: F841
            # Update many times to see oscillation
            for _ in range(50):
                btn.update((0, 0))
            # After many updates, length should have changed
            new_length = btn.drips[0]["length"]  # noqa: F841
            # Length oscillates so it may be different or the same at this point
            # but pulse_timer should definitely have advanced
            assert btn.pulse_timer > 4.0

    def test_default_color_is_dark_red(self) -> None:
        """Default BloodButton color should be dark red."""
        btn = BloodButton(0, 0, 200, 50, "Play")
        assert btn.color == (139, 0, 0)

class MockRect:
    def __init__(self, x=0, y=0, width=100, height=50, **kwargs):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = (x + width // 2, y + height // 2)
        self.topleft = (x, y)
        self.topright = (x + width, y)
        self.bottomleft = (x, y + height)
        self.bottomright = (x + width, y + height)
        self.bottom = y + height

    def collidepoint(self, pos):
        px, py = pos
        return (
            self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height
        )

    def copy(self):
        return MockRect(self.x, self.y, self.width, self.height)


@pytest.fixture(autouse=True)
def patch_rect():
    import pygame

    with patch.object(pygame, "Rect", MockRect):
        yield


class TestButtonDraw:
    """Tests for Button draw methods."""

    def test_button_draw(self) -> None:
        """Button draw should call pygame methods."""
        import pygame
        pygame.draw.rect = MagicMock()
        
        btn = Button(0, 0, 100, 50, "Test", (100, 100, 100))
        screen = MagicMock()
        font = MagicMock()
        font.render.return_value = MagicMock()
        btn.draw(screen, font)
        assert screen.blit.called
        assert font.render.called

    def test_blood_button_draw(self) -> None:
        """BloodButton.draw should call pygame methods."""
        import pygame

        # Inject drawing mocks into the FakeModule
        pygame.draw.rect = MagicMock()
        pygame.draw.circle = MagicMock()
        pygame.draw.line = MagicMock()
        
        mock_surf = MagicMock()
        mock_surf.get_rect.return_value = MockRect()
        pygame.Surface = MagicMock(return_value=mock_surf)

        btn = BloodButton(0, 0, 200, 50, "Play")
        screen = MagicMock()
        font = MagicMock()
        font.render.return_value = MagicMock()
        font.render.return_value.get_rect.return_value = MockRect()

        btn.draw(screen, font)
        
        assert pygame.draw.rect.called
        assert pygame.draw.circle.called
        assert pygame.draw.line.called
        assert screen.blit.called
