import random
import wave
import struct
import math
import os

def generate_sound_assets(sound_dir: str):
    """Generate procedural placeholders for sounds if they don't exist"""
    if not os.path.exists(sound_dir):
        os.makedirs(sound_dir)

    # 1. Gunshot (White noise burst with decay)
    shoot_path = os.path.join(sound_dir, "shoot.wav")
    if not os.path.exists(shoot_path):
        print(f"Generating {shoot_path}...")
        with wave.open(shoot_path, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            data = []
            duration = 0.3
            for i in range(int(44100 * duration)):
                # Decay envelope
                env = 1.0 - (i / (44100 * duration))
                # White noise
                noise = random.uniform(-1, 1)
                sample = int(noise * env * 32767 * 0.5)
                data.append(struct.pack('<h', sample))
            f.writeframes(b''.join(data))

    # 2. Enemy Shoot (Different pitch/envelope)
    enemy_shoot_path = os.path.join(sound_dir, "enemy_shoot.wav")
    if not os.path.exists(enemy_shoot_path):
        print(f"Generating {enemy_shoot_path}...")
        with wave.open(enemy_shoot_path, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            data = []
            duration = 0.4
            for i in range(int(44100 * duration)):
                env = 1.0 - (i / (44100 * duration))
                noise = random.uniform(-1, 1)
                # Lower pitch feel by filtering? Hard in raw loops. Just volume/speed
                sample = int(noise * env * 32767 * 0.4) 
                data.append(struct.pack('<h', sample))
            f.writeframes(b''.join(data))

    # 3. Spooky Soundtrack (Low drone / eerie chords)
    # Using simple sine wave superposition
    music_path = os.path.join(sound_dir, "spooky_ambient.wav")
    if not os.path.exists(music_path):
        print(f"Generating {music_path}...")
        with wave.open(music_path, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            data = []
            duration = 10.0 # Short loop
            
            # Frequencies for a D minor dim chord or similar: D2, F2, G#2
            freqs = [73.42, 87.31, 103.83, 146.83] 
            
            for i in range(int(44100 * duration)):
                t = i / 44100.0
                val = 0
                for freq in freqs:
                    # Add some modulation
                    mod = math.sin(t * 0.5) * 2
                    val += math.sin(2 * math.pi * (freq + mod) * t)
                
                # Normalize roughly
                val = (val / len(freqs)) * 0.3
                sample = int(val * 32767)
                data.append(struct.pack('<h', sample))
            f.writeframes(b''.join(data))

if __name__ == "__main__":
    generate_sound_assets("games/Force Field/assets/sounds")
