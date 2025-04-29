MacOS:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install portaudio
pip install pyaudio
pip install intervaltree
pip install openpyxl
brew install ffmpeg

Linux:
sudo apt update
sudo apt install portaudio19-dev
pip install pyaudio
pip install intervaltree
pip install openpyxl
sudo apt update
sudo apt install ffmpeg

Windows:
pip install pipwin
pipwin install pyaudio
pip install intervaltree
pip install openpyxl
Download FFmpeg from https://ffmpeg.org/download.html, extract it, and add its bin directory to your system PATH.
