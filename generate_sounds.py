import math
import os
import random
import struct
import wave
from pathlib import Path


def generate_sound_assets(sound_dir: str) -> None:
    """Generate procedural placeholders for sounds if they don't exist"""
    sound_path = Path(sound_dir)
    sound_path.mkdir(parents=True, exist_ok=True)

    # 1. Gunshot (White noise burst with decay)
    shoot_path = os.path.join(sound_dir, "shoot.wav")
    # Always regenerate for tuning
    print(f"Generating {shoot_path}...")
    with wave.open(shoot_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)
        data = []
        duration = 0.3
        for i in range(int(44100 * duration)):
            env = 1.0 - (i / (44100 * duration))
            noise = random.uniform(-1, 1)
            sample = int(noise * env * 32767 * 0.5)
            data.append(struct.pack("<h", sample))
        f.writeframes(b"".join(data))

    # 2. Enemy Shoot
    enemy_shoot_path = os.path.join(sound_dir, "enemy_shoot.wav")
    print(f"Generating {enemy_shoot_path}...")
    with wave.open(enemy_shoot_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)
        data = []
        duration = 0.4
        for i in range(int(44100 * duration)):
            env = 1.0 - (i / (44100 * duration))
            # Sawtooth-ish
            angle = i * 200 * 2 * math.pi / 44100
            val = (angle % (2 * math.pi)) / (2 * math.pi) * 2 - 1
            sample = int(val * env * 32767 * 0.3)
            data.append(struct.pack("<h", sample))
        f.writeframes(b"".join(data))

    # 4. Bomb Explosion
    bomb_path = os.path.join(sound_dir, "bomb.wav")
    print(f"Generating {bomb_path}...")
    with wave.open(bomb_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)
        data = []
        duration = 1.0
        for i in range(int(44100 * duration)):
            env = 1.0 - (i / (44100 * duration))
            # Low rumble + noise
            rumble = math.sin(2 * math.pi * 50 * (1.0 - i/44100) * i/44100)
            noise = random.uniform(-1, 1)
            sample_val = (rumble * 0.5 + noise * 0.5) * env * 32767 * 0.8
            data.append(struct.pack("<h", int(sample_val)))
        f.writeframes(b"".join(data))

    # 3. Spooky Musical Soundtrack (Enhanced)
    music_path = os.path.join(sound_dir, "spooky_ambient.wav")
    print(f"Generating {music_path}...")
    with wave.open(music_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)

        # Composition parameters
        tempo = 100  # BPM
        beat_dur = 60.0 / tempo
        total_beats = 64  # Extended loop
        duration = total_beats * beat_dur
        samples = int(44100 * duration)

        # Melodies
        # Bass: E minor drone
        # Lead: High E minor arpeggios
        high_scale = [329.63, 392.00, 493.88, 587.33, 659.25]

        data = []
        
        # Pre-generate melody sequence
        lead_melody = []
        for i in range(total_beats * 4):
            if i % 8 == 0 or (i % 8 > 4 and random.random() > 0.5):
                lead_melody.append(random.choice(high_scale))
            else:
                lead_melody.append(0)

        for i in range(samples):
            t = i / 44100.0
            
            # 1. Bass Drone (Darker)
            bass = math.sin(2 * math.pi * 41.20 * t) * 0.4
            
            # 2. Rhythm (Drums)
            beat_t = t % beat_dur
            beat_idx = int(t / beat_dur)
            kick = 0.0
            snare = 0.0
            hihat = 0.0
            
            # Kick on 1
            if beat_idx % 4 == 0 and beat_t < 0.2:
                kick_freq = 150 * (1.0 - beat_t/0.2)
                kick = math.sin(2 * math.pi * kick_freq * beat_t) * (1.0 - beat_t/0.2)
            
            # Snare on 3
            if beat_idx % 4 == 2 and beat_t < 0.2:
                snare = random.uniform(-0.5, 0.5) * (1.0 - beat_t/0.2)
                
            # Hihat every beat
            if beat_t < 0.05:
                hihat = random.uniform(-0.3, 0.3)
            
            drums = (kick * 0.8 + snare * 0.6 + hihat * 0.3)

            # 3. Lead Melody (The "more melody" request)
            current_16th = int((t / beat_dur) * 4)
            lead_freq = lead_melody[current_16th % len(lead_melody)]
            lead = 0.0
            if lead_freq > 0:
                note_t = t % (beat_dur / 4)
                env = max(0, 1.0 - note_t * 8)
                # Square waveish
                lead = (math.sin(2 * math.pi * lead_freq * t) > 0) * 0.2 * env
                
            final_val = bass + drums + lead
            final_val = max(min(final_val, 1.0), -1.0)
            
            sample = int(final_val * 32767 * 0.5)
            data.append(struct.pack("<h", sample))
        
        f.writeframes(b"".join(data))


if __name__ == "__main__":
    generate_sound_assets("games/Force Field/assets/sounds")
