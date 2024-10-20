#############################################################
### This file takes care of the voice input from the user
#############################################################


### When the user hits the spacebar, record and when they hit again stop

import sounddevice as sd
from pynput import keyboard
import numpy as np
from scipy.io.wavfile import write

# Global variables
fs = 44100  # Sampling rate
recording = False
audio_data = []

def on_press(key):
    global recording, audio_data, stream

    if key == keyboard.Key.space:
        if not recording:
            print("Recording started... Press spacebar again to stop.")
            recording = True
            audio_data = []  # Reset audio data
            # Start a new audio stream
            stream = sd.InputStream(samplerate=fs, channels=1, callback=audio_callback)
            stream.start()
        else:
            print("Recording stopped.")
            recording = False
            stream.stop()
            stream.close()
            # Convert list to numpy array
            audio_array = np.concatenate(audio_data, axis=0)
            # Normalize audio data
            audio_array = np.int16(audio_array / np.max(np.abs(audio_array)) * 32767)
            write('output.wav', fs, audio_array)
            print("Audio saved to 'output.wav'")

def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.append(indata.copy())

def on_release(key):
    # Stop listener if ESC is pressed
    if key == keyboard.Key.esc:
        return False

def main():
    print("Press spacebar to start/stop recording. Press ESC to exit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()

