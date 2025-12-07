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

    # 3. Spooky Musical Soundtrack
    music_path = os.path.join(sound_dir, "spooky_ambient.wav")
    print(f"Generating {music_path}...")
    with wave.open(music_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)

        # Composition parameters
        tempo = 100  # BPM
        beat_dur = 60.0 / tempo
        total_beats = 32  # 8 bars of 4/4
        duration = total_beats * beat_dur
        samples = int(44100 * duration)

        # Melody scale (E Minor / Diminished vibes)
        # E2, G2, A#2, B2, D3, E3
        scale = [82.41, 98.00, 116.54, 123.47, 146.83, 164.81]

        data = []

        # Generate Note Sequence
        melody_notes = []
        for i in range(total_beats * 4):  # 16th notes
            if i % 4 == 0 or random.random() > 0.6:
                note = random.choice(scale)
                melody_notes.append(note)
            else:
                melody_notes.append(0)  # Rest

        for i in range(samples):
            t = i / 44100.0

            # 1. Bass Drone (Low E)
            # AM synthesis for pulsing
            lfo = 0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t)
            bass = math.sin(2 * math.pi * 41.20 * t) * 0.4 * lfo
            # Add some harmonics
            bass += math.sin(2 * math.pi * 41.20 * 3 * t) * 0.1

            # 2. Weird Melody
            current_16th = int((t / beat_dur) * 4)
            freq = melody_notes[current_16th % len(melody_notes)]
            melody = 0.0
            if freq > 0:
                # Envelope for each 16th note
                local_t = t % (beat_dur / 4)
                env = max(0, 1.0 - (local_t * 6))  # Quick decay
                # FM Synthesis for "weird" tone
                mod = math.sin(2 * math.pi * freq * 2.5 * t) * 100 * env
                melody = math.sin(2 * math.pi * (freq + mod) * t) * 0.3 * env

            # 3. Rhythm (Metallic Clank on standard beats)
            rhythm = 0.0
            beat_pos = t % beat_dur
            if beat_pos < 0.1:
                # Noise burst
                rhythm = (random.random() * 2 - 1) * 0.3 * (1.0 - beat_pos * 10)

            # Mix
            final_val = bass + melody + rhythm
            # Clip
            final_val = min(final_val, 1.0)
            final_val = max(final_val, -1.0)

            sample = int(final_val * 32767 * 0.6)
            data.append(struct.pack("<h", sample))

        f.writeframes(b"".join(data))


if __name__ == "__main__":
    generate_sound_assets("games/Force Field/assets/sounds")
