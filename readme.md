1 create symlink:
`sudo ln -s /home/lukas/coding/speech_to_text/whisper.service /home/lukas/.config/systemd/user/whisper.service`

view logs:
`journalctl --user -u whisper.service -f`

view status:
`systemctl --user status  whisper.service`