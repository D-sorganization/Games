import math
import os
import random
import struct
import wave
from pathlib import Path

sounds_dir = "games/Force_Field/assets/sounds"
Path(sounds_dir).mkdir(parents=True, exist_ok=True)


def generate_wave(
    filename: str,
    frequency: float = 440.0,
    duration: float = 0.5,
    volume: float = 0.5,
    wave_type: str = "sine",
) -> None:
    """Generate a sound wave file."""
    sample_rate = 44100
    n_frames = int(sample_rate * duration)

    with wave.open(filename, "w") as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))

        for i in range(n_frames):
            t = i / sample_rate
            value = 0
            if wave_type == "sine":
                value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * t))
            elif wave_type == "square":
                val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
                value = int(volume * 32767.0 * val)
            elif wave_type == "saw":
                val = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
                value = int(volume * 32767.0 * val)
            elif wave_type == "noise":
                value = int(volume * 32767.0 * random.uniform(-1, 1))

            # Fade out
            if t > duration - 0.1:
                fade = (duration - t) / 0.1
                value = int(value * fade)

            packed_value = struct.pack("h", value)
            wav_file.writeframes(packed_value)


# 1. Weapon Sounds - LOUDER (Increased vol from ~0.5 to ~0.8/0.9)
# Pistol: Sharp crack
def gen_pistol() -> None:
    """Generate a pistol firing sound."""
    filename = os.path.join(sounds_dir, "shoot_pistol.wav")
    sample_rate = 44100
    duration = 0.3
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # High freq noise + sine drop
            noise = random.uniform(-1, 1) * math.exp(-t * 20)
            tone = (
                math.sin(2 * math.pi * (800 * math.exp(-t * 10)) * t)
                * math.exp(-t * 10)
            )
            val = int(
                0.9 * 32767 * (noise * 0.7 + tone * 0.3)
            )  # Increased volume
            f.writeframes(struct.pack("h", val))


gen_pistol()


# Rifle: Short pop
def gen_rifle() -> None:
    """Generate a rifle firing sound."""
    filename = os.path.join(sounds_dir, "shoot_rifle.wav")
    sample_rate = 44100
    duration = 0.15
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            noise = random.uniform(-1, 1) * math.exp(-t * 30)
            val = int(0.8 * 32767 * noise)  # Increased volume
            f.writeframes(struct.pack("h", val))


gen_rifle()


# Shotgun: Big Boom
def gen_shotgun() -> None:
    """Generate a shotgun firing sound."""
    filename = os.path.join(sounds_dir, "shoot_shotgun.wav")
    sample_rate = 44100
    duration = 0.6
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # Low freq sine + lots of noise
            noise = random.uniform(-1, 1) * math.exp(-t * 5)
            boom = (
                math.sin(2 * math.pi * (60 * math.exp(-t * 2)) * t) * math.exp(-t * 5)
            )
            # Increased volume
            val = int(0.95 * 32767 * (noise * 0.6 + boom * 0.4))
            f.writeframes(struct.pack("h", val))


gen_shotgun()


# Plasma Weapon Zap
def gen_plasma() -> None:
    """Generate a plasma weapon sound."""
    filename = os.path.join(sounds_dir, "shoot_plasma.wav")
    sample_rate = 44100
    duration = 0.4
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            freq = 2000 - t * 4000
            val = math.sin(2 * math.pi * freq * t) * math.exp(-t * 5)
            # Match other weapon volumes
            f.writeframes(struct.pack("h", int(0.8 * 32767 * val)))


gen_plasma()


# Heartbeat Boosted
def gen_heartbeat() -> None:
    """Generate a heartbeat sound."""
    filename = os.path.join(sounds_dir, "heartbeat.wav")
    sample_rate = 44100
    duration = 0.2
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # Stronger Thump (60Hz + 120Hz harmonic)
            val = (
                math.sin(2 * math.pi * 60 * t) + 0.5 * math.sin(2 * math.pi * 120 * t)
            ) * math.exp(-t * 20)

            # Clip/Limiter
            val = max(-1.0, min(1.0, val))

            f.writeframes(struct.pack("h", int(0.98 * 32767 * val)))


gen_heartbeat()


# Player Hit - UGH Sound (Vocal-like formant attempt)
def gen_hit() -> None:
    """Generate a player hit sound."""
    filename = os.path.join(sounds_dir, "player_hit.wav")
    sample_rate = 44100
    duration = 0.4
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate

            # Simulated vocal cord pulse (Sawtooth)
            freq = 120 * (1 - t / duration * 0.5)  # Pitch drop 120Hz -> 60Hz
            pulse = 2.0 * (t * freq - math.floor(t * freq + 0.5))

            # Simple formants for "Uh" / "Ugh" (F1 ~500Hz, F2 ~1000Hz)
            # Apply AM modulation to simulate throat
            val = (
                pulse * math.sin(2 * math.pi * 500 * t) * 0.5
                + pulse * math.sin(2 * math.pi * 1000 * t) * 0.3
            )

            val = val * math.exp(-t * 8)

            # Clip
            val = max(-1.0, min(1.0, val))

            f.writeframes(struct.pack("h", int(0.8 * 32767 * val)))


gen_hit()


# Enemy Scream - Lower pitch, less static
def gen_scream() -> None:
    """Generate a monster scream sound."""
    filename = os.path.join(sounds_dir, "scream.wav")
    sample_rate = 44100
    duration = 0.6
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # Monster Growl/Scream
            # Low Sawtooth/Square mix
            freq = 150 * (1 - t / duration * 0.2) + random.uniform(
                -20, 20
            )  # 150Hz base

            osc1 = 2.0 * (t * freq - math.floor(t * freq + 0.5))  # Saw
            osc2 = (
                1.0 if math.sin(2 * math.pi * (freq * 0.99) * t) > 0 else -1.0
            )  # Square (detuned)

            val = (osc1 + osc2) * 0.5 * math.exp(-t * 3)

            f.writeframes(struct.pack("h", int(0.7 * 32767 * val)))


gen_scream()


# Bomb Explosion
def gen_bomb() -> None:
    """Generate a bomb explosion sound."""
    filename = os.path.join(sounds_dir, "bomb.wav")
    sample_rate = 44100
    duration = 1.0
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # Deep rumble + noise
            noise = random.uniform(-1, 1) * math.exp(-t * 2)
            rumble = math.sin(2 * math.pi * (50 * math.exp(-t)) * t)

            val = (noise * 0.7 + rumble * 0.4) * math.exp(-t * 2)
            # Clip
            val = max(-1.0, min(1.0, val))

            f.writeframes(struct.pack("h", int(0.9 * 32767 * val)))


gen_bomb()


# Catchphrases (Synthesized robot voice style - poor man's TTS)
def gen_phrase(name: str, freq_base: float) -> None:
    """Generate a synthesized voice phrase."""
    filename = os.path.join(sounds_dir, f"phrase_{name}.wav")
    sample_rate = 44100
    duration = 1.0
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # FM Synthish
            mod = math.sin(2 * math.pi * 10 * t) * 50
            val = math.sin(2 * math.pi * (freq_base + mod) * t) * math.exp(-t * 2)
            f.writeframes(struct.pack("h", int(0.5 * 32767 * val)))


gen_phrase("cool", 440)
gen_phrase("awesome", 554)
gen_phrase("brutal", 220)


# Music Tracks
def gen_music_intro() -> None:
    """Generate the intro music track."""
    filename = os.path.join(sounds_dir, "music_intro.wav")
    sample_rate = 44100
    duration = 10.0  # Short loop or intro
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))

        # Sequence of notes (frequencies) for music box
        # Spooky chromatic / diminished scale
        notes = [660, 587, 523, 622, 660, 784, 523, 440, 392, 440, 523, 660]
        note_len = 0.5  # seconds

        for i in range(n_frames):
            t = i / sample_rate

            # Which note?
            note_idx = int(t / note_len) % len(notes)
            freq: float = notes[note_idx]

            # Detune - sinusoidal pitch wobble (record player warp / untuned)
            freq = freq * (1.0 + 0.02 * math.sin(2 * math.pi * 0.5 * t))

            # Note envelope (Attack Decay)
            local_t = t % note_len
            env = math.exp(-local_t * 5)

            # Tintinnabulation (Sine + high harmonics)
            val = (
                math.sin(2 * math.pi * freq * t) * 0.5
                + math.sin(2 * math.pi * freq * 2.01 * t) * 0.2
                + math.sin(2 * math.pi * freq * 3.5 * t) * 0.1
            )

            val = val * env * 0.6

            f.writeframes(struct.pack("h", int(val * 32767)))


gen_music_intro()


def gen_music_loop() -> None:
    """Generate the looping music track."""
    filename = os.path.join(sounds_dir, "music_loop.wav")
    sample_rate = 44100
    duration = 8.0  # Loopable
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))

        # Halloween Trap / Bells
        # Minor arpeggio
        notes = [440, 523, 659, 523, 440, 392, 349, 392]  # A C E C A G F G
        note_len = 0.5

        for i in range(n_frames):
            t = i / sample_rate

            note_idx = int(t / note_len / 2) % len(notes)  # Slower? No
            # Actually let's do fast arpeggios
            note_idx = int(t * 4) % len(notes)
            freq = notes[note_idx]

            local_t = (t * 4) % 1.0

            # Bell sound: FM synthesis?
            # Carrier freq, Modulator
            val = math.sin(2 * math.pi * freq * t) * math.exp(-local_t * 3)

            # Add creepy drone bass
            bass = math.sin(2 * math.pi * 110 * t) * 0.3

            val = (val * 0.5 + bass * 0.5) * 0.8

            f.writeframes(struct.pack("h", int(val * 32767)))


gen_music_loop()


# Backup Oww if mp3 fails
def gen_oww_backup() -> None:
    """Generate a backup pain sound."""
    filename = os.path.join(sounds_dir, "oww.wav")
    sample_rate = 44100
    duration = 0.4
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # Falling pitch "ow"
            freq = 400 * (1 - t / duration)
            val = math.sin(2 * math.pi * freq * t) * math.exp(-t * 3)
            f.writeframes(struct.pack("h", int(0.8 * 32767 * val)))


gen_oww_backup()
