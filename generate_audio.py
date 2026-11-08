import numpy as np
from scipy.io import wavfile

sample_rate = 16000
duration_sec = 3
t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)

# Define the 3 distinct testing profiles
profiles = {
    "test_flow.wav": {"freq": 1450.0, "noise": 0.15, "desc": "Turbulent Drain Flow"},
    "test_downpour.wav": {"freq": 3500.0, "noise": 0.2, "desc": "Heavy Downpour"},
    "test_stable.wav": {"freq": 700.0, "noise": 0.05, "desc": "Stable Sub-surface Flow"}
}

for filename, props in profiles.items():
    audio_data = 0.5 * np.sin(2 * np.pi * props["freq"] * t)
    noise = props["noise"] * np.random.normal(size=audio_data.shape)
    audio_signal = np.int16((audio_data + noise) * 32767)
    
    wavfile.write(filename, sample_rate, audio_signal)
    print(f"Generated {filename} -> Profile: {props['desc']} ({props['freq']} Hz)")

print("\nAll 3 test audio files generated successfully!")