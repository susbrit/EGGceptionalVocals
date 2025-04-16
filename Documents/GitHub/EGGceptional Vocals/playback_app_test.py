import tkinter as tk
from tkinter import filedialog
import pyaudio
import wave
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import simpleaudio as sa
import time

class EGGceptionalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EGGceptional Vocals")
        
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        self.pages = {}
        for Page in (HomePage, RecordPage, PlaybackPage):
            page = Page(self.container, self)
            self.pages[Page] = page
            page.grid(row=0, column=0, sticky="nsew")
        
        self.show_page(HomePage)
    
    def show_page(self, page_class):
        page = self.pages[page_class]
        page.tkraise()

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        tk.Label(self, text="EGGceptional Vocals", font=("Arial", 16)).pack(pady=10)
        tk.Button(self, text="Record Repertoire", command=lambda: controller.show_page(RecordPage)).pack(pady=5)
        tk.Button(self, text="Playback", command=lambda: controller.show_page(PlaybackPage)).pack(pady=5)

class RecordPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.recording = False
        self.label = tk.Label(self, text="Press 'Start' to record", font=("Arial", 14))
        self.label.pack(pady=10)
        self.start_button = tk.Button(self, text="Start Recording", command=self.start_recording)
        self.start_button.pack(pady=5)
        self.stop_button = tk.Button(self, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        tk.Button(self, text="Back to Home", command=lambda: controller.show_page(HomePage)).pack(pady=5)
    
    def record_audio(self):
        self.recording = True
        self.label.config(text="Recording...")
        
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        
        while self.recording:
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        with wave.open("recorded_audio.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b"".join(frames))
        
        self.label.config(text="Recording saved as 'recorded_audio.wav'")
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
    
    def start_recording(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.record_audio, daemon=True).start()
    
    def stop_recording(self):
        self.recording = False
        self.stop_button.config(state=tk.DISABLED)

class PlaybackPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.playing = False
        self.play_obj = None
        self.instruction_label = tk.Label(self, text="Select WAV or MP3 File")
        self.select_button = tk.Button(self, text="Select File...", command=self.select_file, state=tk.NORMAL)
        
        self.instruction_label.pack(pady=5)
        self.select_button.pack(pady=5)
        self.play_button = tk.Button(self, text="Play Recording", command=self.toggle_play_pause, state=tk.DISABLED)
        self.play_button.pack(pady=5)
        self.fig, self.ax = plt.subplots(figsize=(5, 2))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack()
        tk.Button(self, text="Back to Home", command=lambda: controller.show_page(HomePage)).pack(pady=5)
    
    def select_file(self):
      file_path = filedialog.askopenfilename(
          title="Select an audio file",
          filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3")]
      )
      if file_path:
          self.audio_file = file_path
          self.play_button.config(state=tk.NORMAL)
          self.plot_waveform(self.audio_file)
          self.instruction_label.config(text=f"Selected: {file_path}")

    def toggle_play_pause(self):
        if self.playing:
            self.playing = False
            if self.play_obj:
                self.play_obj.stop()
            self.play_button.config(text="Play Recording")
        else:
            self.playing = True
            self.play_button.config(text="Pause Recording")
            threading.Thread(target=self.play_audio, daemon=True).start()
    
    def play_audio(self):
        audio = AudioSegment.from_file(self.audio_file)
        self.play_obj = _play_with_simpleaudio(audio)
        self.play_obj.wait_done()
        self.playing = False
        self.play_button.config(text="Play Recording")

    # ChatGPT function
    def plot_waveform(self, file_path):
      # Load the audio file
      audio = AudioSegment.from_file(file_path)
      
      # Convert audio to raw data (PCM)
      samples = np.array(audio.get_array_of_samples())

      # If stereo, take only one channel
      if audio.channels == 2:
          samples = samples[::2]

      # Clear previous plot and plot new waveform
      self.ax.clear()
      self.ax.plot(samples, color='blue')
      self.ax.set_xlabel("Sample Index")
      self.ax.set_ylabel("Amplitude")
      
      # Update canvas
      self.canvas.draw()

if __name__ == "__main__":
    app = EGGceptionalApp()
    app.mainloop()
