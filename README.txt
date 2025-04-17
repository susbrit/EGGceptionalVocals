MacOS:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install portaudio
pip install pyaudio
brew install ffmpeg

Linux:
sudo apt update
sudo apt install portaudio19-dev
pip install pyaudio
sudo apt update
sudo apt install ffmpeg

Windows:
pip install pipwin
pipwin install pyaudio
Download FFmpeg from https://ffmpeg.org/download.html, extract it, and add its bin directory to your system PATH.