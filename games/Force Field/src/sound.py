import pygame
import os
from typing import Dict

class SoundManager:
    """Manages sound effects and music"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        # Re-initialize mixer with lower buffer to reduce latency
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_channel = None
        self.sound_enabled = True
        
        # Load assets
        self.load_assets()
        self.initialized = True

    def load_assets(self):
        """Load all sound files"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sound_dir = os.path.join(base_path, "assets", "sounds")
        
        # Map logical names to filenames
        sound_files = {
            "shoot": "shoot.wav",
            "enemy_shoot": "enemy_shoot.wav",
            "ambient": "spooky_ambient.wav"
        }
        
        for name, filename in sound_files.items():
            path = os.path.join(sound_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    # Lower volume for ambient to be background
                    if name == "ambient":
                        self.sounds[name].set_volume(0.5) 
                except Exception as e:
                    print(f"Failed to load sound {filename}: {e}")
            else:
                print(f"Sound file not found: {path}")

    def play_sound(self, name: str):
        """Play a sound effect"""
        if not self.sound_enabled:
            return
            
        if name in self.sounds:
            self.sounds[name].play()

    def start_music(self):
        """Start ambient music loop"""
        if not self.sound_enabled:
            return
            
        if "ambient" in self.sounds:
            # -1 means loop indefinitely
            self.sounds["ambient"].play(loops=-1)

    def stop_music(self):
        """Stop music"""
        if "ambient" in self.sounds:
            self.sounds["ambient"].stop()
