# New IPO Alert

A Python script to monitor new IPO listings on [NepseAlpha](https://www.nepsealpha.com/investment-calandar/ipo) and send alerts via Telegram when new entries are detected.

## Features

- Scrapes IPO data from NepseAlpha website
- Stores previously seen IPOs in a SQLite database
- Detects new IPO listings automatically
- Sends formatted alerts to Telegram
- Runs checks periodically every 2 hours

## Requirements

- Python 3.7 or higher
- Dependencies listed in `requirements.txt`
- Telegram Bot Token (from @BotFather)
- Telegram Chat ID (your chat with the bot)

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the `.env.example` template:

```bash
cp .env.example .env
```

4. Edit the `.env` file and add your Telegram bot token and chat ID:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

## Getting Telegram Bot Token and Chat ID

1. On Telegram, search for `@BotFather` and start a chat
2. Send `/newbot` and follow the instructions to create a new bot
3. Once created, you'll receive a token that looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`
4. To get your Chat ID, search for `@userinfobot` on Telegram and send any message. It will reply with your Chat ID.

## Usage

Run the script:

```bash
python ipo_alert.py
```

The script will:
1. Check for new IPO entries immediately
2. Schedule checks every 2 hours
3. Send Telegram alerts when new IPOs are found
4. Log all activities to `ipo_alert.log`

## Running as a Background Service

### Using systemd (Linux)

Create a service file:

```bash
sudo nano /etc/systemd/system/ipo-alert.service
```

Add the following content (adjust paths accordingly):

```
[Unit]
Description=IPO Alert Service
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/ipo-alert
ExecStart=/usr/bin/python3 /path/to/ipo-alert/ipo_alert.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable ipo-alert.service
sudo systemctl start ipo-alert.service
```

### Using launchd (macOS)

Create a plist file:

```bash
nano ~/Library/LaunchAgents/com.user.ipo-alert.plist
```

Add the following content (adjust paths accordingly):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.ipo-alert</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/ipo-alert/ipo_alert.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/path/to/ipo-alert/error.log</string>
    <key>StandardOutPath</key>
    <string>/path/to/ipo-alert/output.log</string>
</dict>
</plist>
```

Load the service:

```bash
launchctl load ~/Library/LaunchAgents/com.user.ipo-alert.plist
```

## License

MIT 