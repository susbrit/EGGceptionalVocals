MacOS:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install portaudio
pip install pyaudio

Linux:
sudo apt update
sudo apt install portaudio19-dev
pip install pyaudio

Windows:
pip install pipwin
pipwin install pyaudio