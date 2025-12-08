import wave
import math
import struct
import random
import os

sounds_dir = "games/Force Field/assets/sounds"
os.makedirs(sounds_dir, exist_ok=True)

def generate_wave(filename, frequency=440.0, duration=0.5, volume=0.5, type="sine"):
    sample_rate = 44100
    n_frames = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        
        for i in range(n_frames):
            t = i / sample_rate
            value = 0
            if type == "sine":
                value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * t))
            elif type == "square":
                val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
                value = int(volume * 32767.0 * val)
            elif type == "saw":
                val = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
                value = int(volume * 32767.0 * val)
            elif type == "noise":
                value = int(volume * 32767.0 * random.uniform(-1, 1))
            
            # Fade out
            if t > duration - 0.1:
                fade = (duration - t) / 0.1
                value = int(value * fade)
                
            packed_value = struct.pack('h', value)
            wav_file.writeframes(packed_value)

# 1. Weapon Sounds - LOUDER (Increased vol from ~0.5 to ~0.8/0.9)
# Pistol: Sharp crack
def gen_pistol():
    filename = os.path.join(sounds_dir, "shoot_pistol.wav")
    sample_rate = 44100
    duration = 0.3
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            # High freq noise + sine drop
            noise = random.uniform(-1, 1) * math.exp(-t * 20)
            tone = math.sin(2 * math.pi * (800 * math.exp(-t*10)) * t) * math.exp(-t*10)
            val = int(0.9 * 32767 * (noise * 0.7 + tone * 0.3)) # Increased volume
            f.writeframes(struct.pack('h', val))
gen_pistol()

# Rifle: Short pop
def gen_rifle():
    filename = os.path.join(sounds_dir, "shoot_rifle.wav")
    sample_rate = 44100
    duration = 0.15
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            noise = random.uniform(-1, 1) * math.exp(-t * 30)
            val = int(0.8 * 32767 * noise) # Increased volume
            f.writeframes(struct.pack('h', val))
gen_rifle()

# Shotgun: Big Boom
def gen_shotgun():
    filename = os.path.join(sounds_dir, "shoot_shotgun.wav")
    sample_rate = 44100
    duration = 0.6
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            # Low freq sine + lots of noise
            noise = random.uniform(-1, 1) * math.exp(-t * 5)
            boom = math.sin(2 * math.pi * (60 * math.exp(-t*2)) * t) * math.exp(-t*5)
            val = int(0.95 * 32767 * (noise * 0.6 + boom * 0.4)) # Increased volume
            f.writeframes(struct.pack('h', val))
gen_shotgun()

# Plasma: Zap
def gen_plasma():
    filename = os.path.join(sounds_dir, "shoot_plasma.wav")
    sample_rate = 44100
    duration = 0.4
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            freq = 2000 - t * 4000
            val = math.sin(2 * math.pi * freq * t) * math.exp(-t*5)
            f.writeframes(struct.pack('h', int(0.7 * 32767 * val))) # Increased volume
gen_plasma()

# Heartbeat
def gen_heartbeat():
    filename = os.path.join(sounds_dir, "heartbeat.wav")
    sample_rate = 44100
    duration = 0.2
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            # Low thump
            val = math.sin(2 * math.pi * 50 * t) * math.exp(-t*30)
            f.writeframes(struct.pack('h', int(0.8 * 32767 * val)))
gen_heartbeat()

# Player Hit - UGH Sound (Vocal-like formant attempt)
def gen_hit():
    filename = os.path.join(sounds_dir, "player_hit.wav")
    sample_rate = 44100
    duration = 0.4
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            
            # Simulated vocal cord pulse (Sawtooth)
            freq = 120 * (1 - t/duration * 0.5) # Pitch drop 120Hz -> 60Hz
            pulse = 2.0 * (t * freq - math.floor(t * freq + 0.5))
            
            # Simple formants for "Uh" / "Ugh" (F1 ~500Hz, F2 ~1000Hz)
            # Apply AM modulation to simulate throat
            val = pulse * math.sin(2 * math.pi * 500 * t) * 0.5 + pulse * math.sin(2 * math.pi * 1000 * t) * 0.3
            
            val = val * math.exp(-t * 8)
            
            # Clip
            val = max(-1.0, min(1.0, val))
            
            f.writeframes(struct.pack('h', int(0.8 * 32767 * val)))
gen_hit()

# Enemy Scream - Lower pitch, less static
def gen_scream():
    filename = os.path.join(sounds_dir, "scream.wav")
    sample_rate = 44100
    duration = 0.6
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            # Monster Growl/Scream
            # Low Sawtooth/Square mix
            freq = 150 * (1 - t/duration * 0.2) + random.uniform(-20, 20) # 150Hz base
            
            osc1 = (2.0 * (t * freq - math.floor(t * freq + 0.5))) # Saw
            osc2 = 1.0 if math.sin(2 * math.pi * (freq * 0.99) * t) > 0 else -1.0 # Square (detuned)
            
            val = (osc1 + osc2) * 0.5 * math.exp(-t * 3)
            
            f.writeframes(struct.pack('h', int(0.7 * 32767 * val)))
gen_scream()


# Catchphrases (Synthesized robot voice style - poor man's TTS)
def gen_phrase(name, freq_base):
    filename = os.path.join(sounds_dir, f"phrase_{name}.wav")
    sample_rate = 44100
    duration = 1.0
    n_frames = int(sample_rate * duration)
    with wave.open(filename, 'w') as f:
        f.setparams((1, 2, sample_rate, n_frames, 'NONE', 'not compressed'))
        for i in range(n_frames):
            t = i / sample_rate
            # FM Synthish
            mod = math.sin(2 * math.pi * 10 * t) * 50
            val = math.sin(2 * math.pi * (freq_base + mod) * t) * math.exp(-t*2)
            f.writeframes(struct.pack('h', int(0.5 * 32767 * val)))

gen_phrase("cool", 440)
gen_phrase("awesome", 554)
gen_phrase("brutal", 220)
