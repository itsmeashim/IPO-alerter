# IPO Alert System

A Python script to monitor new IPO listings on nepsealpha.com and send Telegram alerts when new offerings are detected.

## Features

- Monitors the nepsealpha.com website for new IPO listings
- Bypasses Cloudflare protection using multiple methods
- Sends alerts via Telegram when new IPOs are detected
- Stores IPO data in SQLite database to track new listings
- Runs on a schedule to check for updates periodically

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/new-ipo-alert.git
   cd new-ipo-alert
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Playwright browsers (optional, but recommended for fallback):
   ```
   playwright install firefox
   ```

4. Create a `.env` file with your Telegram bot information:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

## Usage

Run the script:
```
python ipo_alert.py
```

The script will:
1. Check for new IPO listings immediately
2. Schedule regular checks every 2 hours
3. Send Telegram alerts for any new IPOs found

## Configuration

You can modify the following parameters in the script:
- `API_URL`: The URL of the API endpoint
- `API_PARAMS`: Parameters for the API request
- The check interval (default: 2 hours)

## Troubleshooting

If you encounter Cloudflare protection issues:

1. The script uses cloudscraper as the primary method to bypass protection
2. If cloudscraper fails, it will attempt to use Playwright as a fallback
3. Both methods include retry logic with exponential backoff

If you still face issues:
- Check the logs in `ipo_alert.log`
- Ensure you have the latest version of cloudscraper and Playwright
- Try running with different user agents or browser settings

## License

MIT 