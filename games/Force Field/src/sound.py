from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Dict

import pygame

logger = logging.getLogger(__name__)


class SoundManager:
    """Manages sound effects and music"""

    _instance: SoundManager | None = None
    initialized: bool

    def __new__(cls) -> SoundManager:  # noqa: PYI034
        """Create singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        assert cls._instance is not None
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
        self.current_music: str | None = None

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
            "shoot_pistol": "pistol-shot-233473.mp3",
            "reload_pistol": "gun-reload-2-395177.mp3",
            "shoot_rifle": "shoot_rifle.wav",
            "reload_rifle": "gun-reload-2-395177.mp3",
            "shoot_shotgun": "shotgun-firing-3-14483.mp3",
            "reload_shotgun": "realistic-shotgun-cocking-sound-38640.mp3",
            "shoot_plasma": "bfg-laser-89662.mp3",  # BFG Sound
            "shoot_stormtrooper": "sci-fi-weapon-laser-shot-04-316416.mp3",
            "shoot_laser": "sci-fi-weapon-laser-shot-04-316416.mp3",
            "enemy_shoot": "enemy_shoot.wav",
            "ambient": "music_loop.wav",  # New spooky background
            "bomb": "bomb.wav",
            "scream": "cartoon-scream-1-6835.mp3",  # Cartoon scream
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
            "oww": "oww.wav",  # Using generated wav backup as MP3 failed
            "groan": "male-groan-of-pain-357971.mp3",
            "music_intro": "creepy-untuned-music-box-427400.mp3",
            "music_loop": "creepy-halloween-bell-trap-melody-247720.mp3",
            "music_drums": "creepy-drum-ambience-443142.mp3",
            "music_horror": "scary-horror-theme-song-382733.mp3",
            "music_piano": "creepy-piano-for-scary-stories-158423.mp3",
            "music_action": "horror-thriller-action-247745.mp3",
            "music_wind": "creepy-wind-410541.mp3",
            "beast": "beast-408442.mp3",
        }

        for name, filename in sound_files.items():
            path = sound_dir / filename
            if path.exists():
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    # Lower volume for ambient to be background
                    if "music" in name or name == "ambient":
                        self.sounds[name].set_volume(0.5)
                except Exception:
                    logger.exception("Failed to load sound %s (probably codec issue?)", filename)
                    # If we fail to load a "real" sound, try to fallback
                    # to synthesized logic if possible?
                    # For now just log it.
            else:
                logger.warning("Sound file not found: %s (Current Dir: %s)", path, Path.cwd())

    def play_sound(self, name: str) -> None:
        """Play a sound effect"""
        if not self.sound_enabled:
            return

        if name in self.sounds:
            try:
                self.sounds[name].play()
            except BaseException:
                logger.exception("Sound play failed for %s", name)

    def start_music(self, name: str = "music_loop") -> None:
        """Start ambient music loop"""
        if not self.sound_enabled:
            return

        self.stop_music()

        if name in self.sounds:
            # -1 means loop indefinitely
            self.sounds[name].play(loops=-1)
            self.current_music = name

    def stop_music(self) -> None:
        """Stop music"""
        if (
            hasattr(self, "current_music")
            and self.current_music
            and self.current_music in self.sounds
        ):
            self.sounds[self.current_music].stop()

        # Fallback
        if "ambient" in self.sounds:
            self.sounds["ambient"].stop()
