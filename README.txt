# EGGceptional Vocals

## Setup
MacOS:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install portaudio
<<<<<<< HEAD
pip install pyaudio
pip install intervaltree
pip install openpyxl
brew install ffmpeg
=======
brew install ffmpeg
pip install -r requirements.txt
>>>>>>> 470aeef907aabe208c86306465d145e7eed593d0

Linux:
sudo apt update
sudo apt install portaudio19-dev
<<<<<<< HEAD
pip install pyaudio
pip install intervaltree
pip install openpyxl
sudo apt update
sudo apt install ffmpeg
=======
sudo apt update
sudo apt install ffmpeg
pip install -r requirements.txt
>>>>>>> 470aeef907aabe208c86306465d145e7eed593d0

Windows:
pip install pipwin
pipwin install pyaudio
<<<<<<< HEAD
pip install intervaltree
pip install openpyxl
Download FFmpeg from https://ffmpeg.org/download.html, extract it, and add its bin directory to your system PATH.
=======
Download FFmpeg from https://ffmpeg.org/download.html, extract it, and add its bin directory to your system PATH.
pip install -r requirements.txt

## Run Eggceptional Vocals
python3 src/eggceptional_dpg.py

## Test Eggceptional Vocals
python3 -m src.tests.backend_test.py
>>>>>>> 470aeef907aabe208c86306465d145e7eed593d0
