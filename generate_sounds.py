import wave
import math
import struct
import random
import os

def generate_wave(filename, frequency=440.0, duration=1.0, volume=0.5, type="sine"):
    sample_rate = 44100
    n_frames = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        
        for i in range(n_frames):
            t = i / sample_rate
            if type == "sine":
                value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * t))
            elif type == "sawtooth":
                value = int(volume * 32767.0 * (2.0 * (t * frequency - math.floor(t * frequency + 0.5))))
            elif type == "noise":
                value = int(volume * 32767.0 * random.uniform(-1, 1))
            elif type == "dark_drone":
                 # Multiple low frequencies
                 v1 = math.sin(2.0 * math.pi * 55.0 * t)
                 v2 = math.sin(2.0 * math.pi * 110.0 * t * 1.01) # Detuned
                 v3 = math.sin(2.0 * math.pi * 27.5 * t)
                 value = int(volume * 32767.0 * (v1 * 0.5 + v2 * 0.3 + v3 * 0.2))
            
            packed_value = struct.pack('h', value)
            wav_file.writeframes(packed_value)

sounds_dir = "games/Force Field/assets/sounds"
os.makedirs(sounds_dir, exist_ok=True)

# Dark Ambient
generate_wave(os.path.join(sounds_dir, "dark_ambient.wav"), duration=5.0, type="dark_drone", volume=0.4)

# Scream (High pitch sliding down noise/saw)
def generate_scream(filename):
    sample_rate = 44100
    duration = 0.8
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            freq = 800 * (1 - t/duration) + random.uniform(-50, 50) # Slide down
            value = int(0.5 * 32767.0 * math.sin(2 * math.pi * freq * t))
            wav_file.writeframes(struct.pack('h', value))

generate_scream(os.path.join(sounds_dir, "scream.wav"))

# Death (Low thud/crunch)
def generate_death(filename):
    sample_rate = 44100
    duration = 0.5
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            freq = 100 * (1 - t/duration)
            value = int(0.6 * 32767.0 * (random.random() * math.sin(2 * math.pi * freq * t)))
            wav_file.writeframes(struct.pack('h', value))

generate_death(os.path.join(sounds_dir, "death.wav"))
