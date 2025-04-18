import os
from .context import proc_data

def pitch_detection():
    pitch_data = 'src/tests/data/pitch_data'
    for pitch_file_name in os.listdir(pitch_data):
        pitch_file_path = os.path.join(pitch_data, pitch_file_name)
        print(proc_data.find_pitch_bounds(["C4", "C5", "C6"]))
        print(pitch_file_path)

# Run tests
pitch_detection()
