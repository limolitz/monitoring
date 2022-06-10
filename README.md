# Quantified Self Scripts

My Quantified Self scripts. I should probably call this just monitoring.

Each folder consists of a script which logs its data to a MQTT script you can find [here](https://github.com/wasmitnetzen/mqttsend). Whatever you do when the data is written to your MQTT broker is up to you, I store it in an InfluxDB and visualize it in Grafana.

Currently working scripts:
* Logging of currently opened tabs in Firefox (Linux only, currently unmaintained)
* Logging of traffic (Linux and MacOs only)
* Logging of RAM usage (Linux and MacOS only)
* Logging of CPU usage (Linux and MacOS only)
* Presence checking of devices in local network
* Logging of eMail traffic over IMAP

Possible future features:
* Logging of visited sites and duration in Firefox


## Systemd timers

Some of the scripts should be run via a classical cronjob, some rather with a systemd timer. To set this up, copy the `.service` and `.timer` files to `~/.config/systemd/user`, adjust the paths inside them and run `systemctl enable --user --now UNIT.timer`.
