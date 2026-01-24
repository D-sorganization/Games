"""Sound manager for Zombie Survival game."""

from __future__ import annotations

from src.games.shared.sound_manager_base import SoundManagerBase


class SoundManager(SoundManagerBase):
    """Manages sound effects and music for Zombie Survival."""

    # Map logical names to filenames
    SOUND_FILES = {
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
