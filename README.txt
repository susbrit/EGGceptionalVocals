MacOS:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install portaudio
pip install pyaudio
pip install intervaltree
pip install openpyxl

Linux:
sudo apt update
sudo apt install portaudio19-dev
pip install pyaudio
pip install intervaltree
pip install openpyxl

Windows:
pip install pipwin
pipwin install pyaudio
pip install intervaltree
pip install openpyxl
