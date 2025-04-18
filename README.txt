# EGGceptional Vocals

## Setup
MacOS:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install portaudio
brew install ffmpeg
pip install -r requirements.txt

Linux:
sudo apt update
sudo apt install portaudio19-dev
sudo apt update
sudo apt install ffmpeg
pip install -r requirements.txt

Windows:
pip install pipwin
pipwin install pyaudio
Download FFmpeg from https://ffmpeg.org/download.html, extract it, and add its bin directory to your system PATH.
pip install -r requirements.txt

## Run Eggceptional Vocals
python3 src/eggceptional_dpg.py

## Test Eggceptional Vocals
python3 -m src.tests.backend_test.py
