from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Dict

import pygame
from typing_extensions import Self


class SoundManager:
    """Manages sound effects and music"""

    _instance = None

    def __new__(cls) -> Self:
        """Create singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize SoundManager"""
        if self.initialized:
            return

        # Re-initialize mixer with lower buffer to reduce latency
        with contextlib.suppress(Exception):
            pygame.mixer.quit()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)

        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_channel = None
        self.sound_enabled = True

        # Load assets
        self.load_assets()
        self.initialized = True

    def load_assets(self) -> None:
        """Load all sound files"""
        base_dir = Path(__file__).resolve().parent.parent
        sound_dir = base_dir / "assets" / "sounds"

        # Map logical names to filenames
        sound_files = {
            "shoot": "shoot.wav",
            "shoot_pistol": "shoot_pistol.wav",
            "shoot_rifle": "shoot_rifle.wav",
            "shoot_shotgun": "shoot_shotgun.wav",
            "shoot_plasma": "shoot_plasma.wav",
            "enemy_shoot": "enemy_shoot.wav",
            "ambient": "dark_ambient.wav",
            "bomb": "bomb.wav",
            "scream": "scream.wav",
            "death": "death.wav",
            "heartbeat": "heartbeat.wav",
            "player_hit": "player_hit.wav",
            "phrase_cool": "phrase_cool.wav",
            "phrase_awesome": "phrase_awesome.wav",
            "phrase_brutal": "phrase_brutal.wav",
            "boom_real": "boom-356126.mp3",
            "game_over1": "game-over-417465.mp3",
            "game_over2": "game-over-deep-male-voice-clip-352695.mp3",
            "scream_real": "pathetic-screaming-sound-effect-312867.mp3",
            "water": "stream-sounds-sample-420906.mp3",
            "laugh": "possessed-laugh-94851.mp3",
            "breath": "normal-breath-loop-400151.mp3",
            "oww": "short-oww-46070.mp3",
            "groan": "male-groan-of-pain-357971.mp3",
        }

        for name, filename in sound_files.items():
            path = os.path.join(sound_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    # Lower volume for ambient to be background
                    if name == "ambient":
                        self.sounds[name].set_volume(0.5)
                except Exception as e:  # noqa: BLE001
                    print(f"Failed to load sound {filename} (probably codec issue?): {e}")
                    # If we fail to load a "real" sound, try to fallback to synthesized logic if possible?
                    # For now just log it.
            else:
                print(f"Sound file not found: {path} (Current Dir: {os.getcwd()})")

    def play_sound(self, name: str) -> None:
        """Play a sound effect"""
        if not self.sound_enabled:
            return

        if name in self.sounds:
            self.sounds[name].play()

    def start_music(self) -> None:
        """Start ambient music loop"""
        if not self.sound_enabled:
            return

        if "ambient" in self.sounds:
            # -1 means loop indefinitely
            self.sounds["ambient"].play(loops=-1)

    def stop_music(self) -> None:
        """Stop music"""
        if "ambient" in self.sounds:
            self.sounds["ambient"].stop()
