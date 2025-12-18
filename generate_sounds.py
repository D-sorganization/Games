import math
import random
import struct
import wave
from pathlib import Path


def generate_wave(
    filename: str,
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5,
    wave_type: str = "sine",
) -> None:
    """Generate a sound wave file with specified parameters."""
    sample_rate = 44100
    n_frames = int(sample_rate * duration)

    with wave.open(filename, "w") as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))

        for i in range(n_frames):
            t = i / sample_rate
            value = 0
            if wave_type == "sine":
                value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * t))
            elif wave_type == "sawtooth":
                val = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
                value = int(volume * 32767.0 * val)
            elif wave_type == "noise":
                value = int(volume * 32767.0 * random.uniform(-1, 1))
            elif wave_type == "dark_drone":
                # Multiple low frequencies
                v1 = math.sin(2.0 * math.pi * 55.0 * t)
                v2 = math.sin(2.0 * math.pi * 110.0 * t * 1.01)  # Detuned
                v3 = math.sin(2.0 * math.pi * 27.5 * t)
                value = int(volume * 32767.0 * (v1 * 0.5 + v2 * 0.3 + v3 * 0.2))

            packed_value = struct.pack("h", value)
            wav_file.writeframes(packed_value)


sounds_dir = Path("games/Force_Field/assets/sounds")
sounds_dir.mkdir(parents=True, exist_ok=True)

# Dark Ambient
generate_wave(
    str(sounds_dir / "dark_ambient.wav"),
    duration=5.0,
    wave_type="dark_drone",
    volume=0.4,
)


# Scream (High pitch sliding down noise/saw)
def generate_scream(filename: str) -> None:
    """Generate a scream sound effect."""
    sample_rate = 44100
    duration = 0.8
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            # Slide down
            base_freq = 800 * (1 - t / duration)
            freq = base_freq + random.uniform(-50, 50) if duration > 0 else 800
            value = int(0.5 * 32767.0 * math.sin(2 * math.pi * freq * t))
            wav_file.writeframes(struct.pack("h", value))


generate_scream(str(sounds_dir / "scream.wav"))


# Death (Low thud/crunch)
def generate_death(filename: str) -> None:
    """Generate a death sound effect."""
    sample_rate = 44100
    duration = 0.5
    n_frames = int(sample_rate * duration)
    with wave.open(filename, "w") as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, "NONE", "not compressed"))
        for i in range(n_frames):
            t = i / sample_rate
            freq = 100 * (1 - t / duration) if duration > 0 else 100
            osc = math.sin(2 * math.pi * freq * t)
            value = int(0.6 * 32767.0 * (random.random() * osc))
            wav_file.writeframes(struct.pack("h", value))


generate_death(str(sounds_dir / "death.wav"))
