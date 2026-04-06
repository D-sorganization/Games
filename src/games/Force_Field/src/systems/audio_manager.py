"""Audio wiring for Force Field game.

This module wraps the SoundManager and provides audio event wiring
helpers used by Game to connect sound playback to game events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from games.shared.event_bus import EventBus
from games.shared.sound_manager_base import SoundManagerBase

from ..sound import SoundManager

if TYPE_CHECKING:
    pass


class AudioManager:
    """Manages audio wiring between the event bus and the sound manager.

    Preconditions:
        sound_manager is a SoundManagerBase instance.
        event_bus is an EventBus instance.
    """

    def __init__(
        self,
        sound_manager: SoundManagerBase | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.sound_manager: SoundManagerBase = (
            sound_manager if sound_manager is not None else SoundManager()
        )
        self.event_bus = event_bus or EventBus()
        self._wire_events()

    def _wire_events(self) -> None:
        """Subscribe audio reactions to game events via the event bus."""
        self.event_bus.subscribe(
            "bot_killed",
            lambda **kw: self.sound_manager.play_sound("scream"),
        )

    def start_music(self, track: str | None = None) -> None:
        """Start background music, optionally selecting a specific track."""
        if track is not None:
            self.sound_manager.start_music(track)
        else:
            self.sound_manager.start_music()

    def play_sound(self, name: str) -> None:
        """Play a named sound effect."""
        self.sound_manager.play_sound(name)
