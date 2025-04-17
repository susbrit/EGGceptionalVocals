import proc_data
import os

def pitch_detection():
    pitch_data = 'data/pitch_data'
    for pitch_file_name in os.listdir(pitch_data):
        pitch_file_path = os.path.join(pitch_data, pitch_file_name)
        print(pitch_file_path)

# Run tests
pitch_detection()
