This project creates a speech to text system designed for Linux systemd systems.
It is based on the OpenAI whisper model.

#### 1. Clone the Repository
Clone the repository to your desired directory:

```bash
git clone https://github.com/BasedLukas/speech_to_text.git
cd speech_to_text
```

#### 2. Create and Set Up the Virtual Environment
The service requires a Python virtual environment named `venv`.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Run the Install Script
The install.sh script configures the service and ensures it dynamically uses the current working directory.

```bash
chmod +x install.sh
./install.sh
```

The script performs the following:
Sets up the whisper.service file with the current working directory.
Copies the modified service file to `~/.config/systemd/user/`.
Reloads systemd and enables the service.

#### 4. Start the Service

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

#### 5. Usage
- default keybinding is `ctrl + F1`

- Hold to record

- Text will be inserted at cursor location



#### 6. Known Bugs / TODO
- allow user to select different models
- doesnt work in terminal
- text overides copy buffer
- very long recordings break system
- no indication for user that system is recording or not
- need a config file for microphone choice, keybindings etc
