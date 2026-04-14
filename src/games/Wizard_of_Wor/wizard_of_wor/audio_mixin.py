"""Audio mixin for Wizard of Wor – wraps SoundBoard integration.

Single-Responsibility: this module owns all audio event wiring between the
game state and the SoundBoard tone generator.  SoundBoard itself lives in
this module because its sole consumer is the audio layer.
"""

from __future__ import annotations

from array import array

import numpy as np
import pygame

# ---------------------------------------------------------------------------
# SoundBoard – lightweight tone generator
# ---------------------------------------------------------------------------


class SoundBoard:
    """Lightweight tone generator for classic arcade-style beeps."""

    def __init__(self) -> None:
        """Initialize the tone generator for arcade-style sound effects."""
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound | None] = {}
        try:
            get_init = getattr(pygame.mixer, "get_init", None)
            if get_init is None or not get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.enabled = True
        except (pygame.error, Exception):  # noqa: BLE001
            self.enabled = False

        get_init = getattr(pygame.mixer, "get_init", None)
        if get_init is not None and not get_init():
            self.enabled = False

        if self.enabled:
            self.sounds = {
                "shot": self._build_tone(920, 80),
                "enemy_hit": self._build_tone(480, 120),
                "player_hit": self._build_tone(220, 200),
                "spawn": self._build_tone(640, 150),
                "wizard": self._build_tone(300, 200),
            }
            self.intro_melody = self._build_intro_melody()
        else:
            self.sounds = {}

    def _build_tone(
        self, frequency: int, duration_ms: int
    ) -> pygame.mixer.Sound | None:
        """Build a tone sound effect with the given frequency and duration."""
        if not self.enabled:
            try:
                return pygame.mixer.Sound(buffer=b"")
            except pygame.error:
                return None
        sample_rate = 22050
        sample_count = int(sample_rate * duration_ms / 1000)
        t = np.arange(sample_count) / sample_rate
        samples = (14000 * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _build_intro_melody(self) -> pygame.mixer.Sound | None:
        """Build a retro-style intro melody reminiscent of classic arcade games."""
        if not self.enabled:
            try:
                return pygame.mixer.Sound(buffer=b"")
            except pygame.error:
                return None
        sample_rate = 22050
        sample_count = int(sample_rate * 3000 / 1000)
        melody = [
            (523, 300),
            (659, 300),
            (784, 300),
            (1047, 600),
            (784, 300),
            (659, 300),
            (523, 600),
        ]
        waveform = array("h")
        current_sample = self._append_melody_notes(
            waveform, melody, sample_rate, sample_count
        )
        while current_sample < sample_count:
            waveform.append(0)
            current_sample += 1
        return pygame.mixer.Sound(buffer=waveform.tobytes())

    def _append_melody_notes(
        self,
        waveform: array,
        melody: list[tuple[int, int]],
        sample_rate: int,
        sample_count: int,
    ) -> int:
        """Append square-wave note samples plus inter-note pauses.

        Returns the final sample index.
        """
        current_sample = 0
        for freq, note_duration_ms in melody:
            note_samples = int(sample_rate * note_duration_ms / 1000)
            for i in range(note_samples):
                if current_sample >= sample_count:
                    break
                envelope = min(1.0, (note_samples - i) / (note_samples * 0.1))
                square_wave = 1 if (i * freq // sample_rate) % 2 else -1
                waveform.append(int(8000 * envelope * square_wave))
                current_sample += 1
            pause_samples = int(sample_rate * 0.05)
            for _ in range(pause_samples):
                if current_sample >= sample_count:
                    break
                waveform.append(0)
                current_sample += 1
        return current_sample

    def play(self, name: str) -> None:
        """Play a sound effect by name."""
        if self.enabled and name in self.sounds:
            sound = self.sounds[name]
            if sound:
                sound.play()

    def play_intro(self) -> None:
        """Play the intro melody."""
        if self.enabled and hasattr(self, "intro_melody") and self.intro_melody:
            self.intro_melody.play()


# ---------------------------------------------------------------------------
# AudioMixin – wires SoundBoard events to game actions
# ---------------------------------------------------------------------------


class AudioMixin:
    """Mixin that provides audio helpers for WizardOfWorGame.

    Pre-condition: ``self.soundboard`` is a :class:`SoundBoard` instance,
    initialised in WizardOfWorGame.__init__ before any audio helper is called.
    """

    def _audio_play_spawn(self) -> None:
        """Emit the enemy-spawn sound."""
        self.soundboard.play("spawn")  # type: ignore[attr-defined]

    def _audio_play_wizard(self) -> None:
        """Emit the wizard-arrival sound."""
        self.soundboard.play("wizard")  # type: ignore[attr-defined]

    def _audio_play_shot(self) -> None:
        """Emit the player-shot sound."""
        self.soundboard.play("shot")  # type: ignore[attr-defined]

    def _audio_play_enemy_hit(self) -> None:
        """Emit the enemy-hit sound."""
        self.soundboard.play("enemy_hit")  # type: ignore[attr-defined]

    def _audio_play_player_hit(self) -> None:
        """Emit the player-hit sound."""
        self.soundboard.play("player_hit")  # type: ignore[attr-defined]

    def _audio_play_intro(self) -> None:
        """Play the intro melody."""
        self.soundboard.play_intro()  # type: ignore[attr-defined]
