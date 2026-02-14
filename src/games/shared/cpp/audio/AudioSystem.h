#pragma once
#include <SDL.h>
#include <SDL_audio.h>
#include <string>
#include <map>
#include <vector>
#include <iostream>

namespace qe {
namespace audio {

// Simple WAV loader and mixer using SDL2 Audio
class AudioSystem {
public:
    struct SoundData {
        Uint8* buffer;
        Uint32 length;
        SDL_AudioSpec spec;
    };

    SDL_AudioDeviceID deviceId = 0;
    std::map<std::string, SoundData> sounds;
    
    // Simple mixing: keep track of playing sounds if needed, 
    // but for now let's use SDL_QueueAudio which is fire-and-forget for simple effects.
    // NOTE: SDL_QueueAudio queues data. If we want overlapping sounds, we need a mixer callback.
    // Let's implement a very simple mixer callback.

    struct PlayingSound {
        Uint8* position;
        Uint32 remaining;
        bool active = false;
    };
    std::vector<PlayingSound> playing_sounds;
    SDL_AudioSpec deviceSpec;

    static void AudioCallback(void* userdata, Uint8* stream, int len) {
        AudioSystem* sys = static_cast<AudioSystem*>(userdata);
        SDL_memset(stream, 0, len); // Silence

        if (!sys) return;

        for (auto& s : sys->playing_sounds) {
            if (!s.active) continue;

            Uint32 mix_len = (len > (int)s.remaining) ? s.remaining : len;
            SDL_MixAudioFormat(stream, s.position, sys->deviceSpec.format, mix_len, SDL_MIX_MAXVOLUME / 2);
            
            s.position += mix_len;
            s.remaining -= mix_len;
            
            if (s.remaining == 0) {
                s.active = false;
            }
        }
        
        // Cleanup inactive (optional, might need lock)
    }

    bool init() {
        if (SDL_InitSubSystem(SDL_INIT_AUDIO) < 0) {
            std::cerr << "SDL Audio Init Failed: " << SDL_GetError() << std::endl;
            return false;
        }

        SDL_AudioSpec want;
        SDL_zero(want);
        want.freq = 44100;
        want.format = AUDIO_S16LSB;
        want.channels = 2;
        want.samples = 1024;
        want.callback = AudioCallback;
        want.userdata = this;

        deviceId = SDL_OpenAudioDevice(NULL, 0, &want, &deviceSpec, 0); // 0 = allow changes? No, force same format
        if (deviceId == 0) {
             std::cerr << "Failed to open audio: " << SDL_GetError() << std::endl;
             return false;
        }

        // Pre-allocate slots
        playing_sounds.resize(16);
        SDL_PauseAudioDevice(deviceId, 0);
        return true;
    }

    bool load_wav(const std::string& name, const std::string& path) {
        SoundData sound;
        if (SDL_LoadWAV(path.c_str(), &sound.spec, &sound.buffer, &sound.length) == NULL) {
            std::cerr << "Failed to load WAV " << path << ": " << SDL_GetError() << std::endl;
            return false;
        }
        
        // Convert if needed? 
        // For this simple example, assume WAVs match the device spec or rely on luck/pre-conversion.
        // In robust engine, we'd use SDL_AudioCVT.
        // Let's assume input assets are 44.1k stereo S16 for now.
        
        sounds[name] = sound;
        return true;
    }

    void play(const std::string& name) {
        if (sounds.find(name) == sounds.end()) return;
        
        SoundData& sd = sounds[name];
        
        // Find free slot
        SDL_LockAudioDevice(deviceId);
        for (auto& s : playing_sounds) {
            if (!s.active) {
                s.position = sd.buffer;
                s.remaining = sd.length;
                s.active = true;
                break;
            }
        }
        SDL_UnlockAudioDevice(deviceId);
    }
    
    // Synthesize a simple beep/boop if no file
    void play_synthetic(float freq, float duration) {
        // Generate a square wave buffer
        static std::vector<Uint8> synth_buffer;
        int samples = (int)(duration * deviceSpec.freq);
        int bytes = samples * deviceSpec.channels * 2; // 16bit = 2 bytes
        if (synth_buffer.size() < bytes) synth_buffer.resize(bytes);
        
        Sint16* raw = (Sint16*)synth_buffer.data();
        int period = (int)(deviceSpec.freq / freq);
        
        for (int i=0; i < samples; ++i) {
             Sint16 val = ((i / (period/2)) % 2) ? 3000 : -3000;
             for(int c=0; c<deviceSpec.channels; ++c) {
                 *raw++ = val;
             }
        }
        
        SDL_LockAudioDevice(deviceId);
        for (auto& s : playing_sounds) {
            if (!s.active) {
                s.position = synth_buffer.data();
                s.remaining = bytes;
                s.active = true;
                break;
            }
        }
        SDL_UnlockAudioDevice(deviceId);
    }

    void cleanup() {
        if (deviceId) {
            SDL_CloseAudioDevice(deviceId);
            deviceId = 0;
        }
        for (auto& pair : sounds) {
            SDL_FreeWAV(pair.second.buffer);
        }
        sounds.clear();
    }
};

} // namespace audio
} // namespace qe
