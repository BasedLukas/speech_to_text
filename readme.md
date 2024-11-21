**This project creates a speech to text system designed for Linux / systemd. It is based on the [OpenAI whisper model](https://github.com/openai/whisper).**

#### 1. Clone the Repository

```bash
git clone https://github.com/BasedLukas/speech_to_text.git
cd speech_to_text
```

#### 2. Create and Set Up the Virtual Environment

```bash
# it must be named `venv`.
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Install
Optional: Modify the `src/config.py` file to change the model size.

```bash
sudo apt install portaudio19-dev
chmod +x install.sh
./install.sh
```

The script performs the following:

- Ensures your venv is setup correctly, and all the packages have been installed. 
- Sets up the whisper.service file with the current working directory.
- Copies the modified service file to `~/.config/systemd/user/`.
- Reloads systemd and enables the service.


#### 4. Usage
- Default keybinding is `ctrl + F1`

- Hold to record (note icon in system tray)

- Text will be inserted at cursor location

- Model will be unloaded from memory after inactivity, and reloaded when again active


#### 5. Observe

```bash
#Start service
systemctl --user start whisper.service

#Check Service Status:
systemctl --user status whisper.service

#View Logs:
journalctl --user -u whisper.service -f

#Stop the Service
systemctl --user stop whisper.service
```


#### 6. Known Bugs / TODO /Development
