#!/usr/bin/env python3
"""
IPO Alert - A script to monitor new IPO listings on nepsealpha.com and send Telegram alerts
"""

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import httpx
import schedule
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ipo_alert.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ipo_alert")

# Load environment variables
load_dotenv()

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Constants
DATABASE_PATH = Path("ipo_data.db")
API_URL = "https://www.nepsealpha.com/investment-calandar/ipo"
API_PARAMS = {
    "draw": 1,
    "columns[0][data]": "symbol",
    "columns[0][name]": "symbol",
    "columns[0][searchable]": "true",
    "columns[0][orderable]": "true",
    "columns[0][search][value]": "",
    "columns[0][search][regex]": "false",
    "columns[1][data]": "units",
    "columns[1][name]": "units",
    "columns[1][searchable]": "true",
    "columns[1][orderable]": "true",
    "columns[1][search][value]": "",
    "columns[1][search][regex]": "false",
    "columns[2][data]": "opening_date",
    "columns[2][name]": "opening_date",
    "columns[2][searchable]": "true",
    "columns[2][orderable]": "true",
    "columns[2][search][value]": "",
    "columns[2][search][regex]": "false",
    "columns[3][data]": "closing_date",
    "columns[3][name]": "closing_date",
    "columns[3][searchable]": "true",
    "columns[3][orderable]": "true",
    "columns[3][search][value]": "",
    "columns[3][search][regex]": "false",
    "columns[4][data]": "issue_manager",
    "columns[4][name]": "issue_manager",
    "columns[4][searchable]": "true",
    "columns[4][orderable]": "true",
    "columns[4][search][value]": "",
    "columns[4][search][regex]": "false",
    "columns[5][data]": "status",
    "columns[5][name]": "status",
    "columns[5][searchable]": "true",
    "columns[5][orderable]": "true",
    "columns[5][search][value]": "",
    "columns[5][search][regex]": "false",
    "columns[6][data]": "view",
    "columns[6][name]": "view",
    "columns[6][searchable]": "true",
    "columns[6][orderable]": "true",
    "columns[6][search][value]": "",
    "columns[6][search][regex]": "false",
    "start": 0,
    "length": 100,  # Increase to get more entries
    "search[value]": "",
    "search[regex]": "false",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.5",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
    "Referer": "https://www.nepsealpha.com/investment-calandar/ipo",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

@dataclass
class IPOEntry:
    """Represents an IPO entry with relevant information"""
    id: int
    symbol: str  # Original HTML symbol
    symbol_clean: str  # Clean symbol text
    company_name: str
    units: str
    opening_date: str
    closing_date: str
    issue_manager: str
    price: str
    status: str
    url: Optional[str] = None

    @classmethod
    def from_api_data(cls, data: Dict) -> "IPOEntry":
        """Create an IPO entry from API data"""
        # Extract clean symbol from HTML
        soup = BeautifulSoup(data["symbol"], "html.parser")
        symbol_clean = soup.get_text().strip()
        
        # Extract clean dates
        soup_opening = BeautifulSoup(data["opening_date"], "html.parser")
        opening_date = soup_opening.get_text().strip()
        
        soup_closing = BeautifulSoup(data["closing_date"], "html.parser")
        closing_date = soup_closing.get_text().strip()
        
        # Extract clean status
        soup_status = BeautifulSoup(data["status"], "html.parser")
        status = soup_status.get_text().strip()
        
        # Extract URL if available
        url = None
        if data["view"]:
            soup_view = BeautifulSoup(data["view"], "html.parser")
            url_tag = soup_view.find("a")
            if url_tag and url_tag.get("href"):
                url = url_tag["href"]
        
        return cls(
            id=data["id"],
            symbol=data["symbol"],
            symbol_clean=symbol_clean,
            company_name=data["company_name"],
            units=data["units"],
            opening_date=opening_date,
            closing_date=closing_date,
            issue_manager=data["issue_manager"],
            price=str(data["price"]),
            status=status,
            url=url or data["url"]
        )

def setup_database() -> None:
    """Set up the SQLite database for storing IPO entries"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ipo_entries (
            id INTEGER PRIMARY KEY,
            symbol_clean TEXT,
            company_name TEXT,
            units TEXT,
            opening_date TEXT,
            closing_date TEXT,
            issue_manager TEXT,
            price TEXT,
            status TEXT,
            url TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

def get_known_ipo_ids() -> Set[int]:
    """Retrieve the IDs of all known IPO entries from the database"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ipo_entries")
        return {row[0] for row in cursor.fetchall()}

def save_ipo_entries(entries: List[IPOEntry]) -> None:
    """Save IPO entries to the database if they don't exist"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        for entry in entries:
            cursor.execute(
                """
                INSERT OR IGNORE INTO ipo_entries 
                (id, symbol_clean, company_name, units, opening_date, closing_date, 
                issue_manager, price, status, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id, 
                    entry.symbol_clean,
                    entry.company_name,
                    entry.units,
                    entry.opening_date,
                    entry.closing_date,
                    entry.issue_manager,
                    entry.price,
                    entry.status,
                    entry.url
                )
            )
        conn.commit()

async def fetch_ipo_data() -> List[IPOEntry]:
    """Fetch IPO data from the API and parse it into IPOEntry objects"""
    logger.info("Fetching IPO data from API...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                API_URL, 
                params=API_PARAMS, 
                headers=HEADERS
            )
            response.raise_for_status()
            data = response.json()
            
            if "data" not in data:
                logger.error(f"Unexpected API response: {data}")
                return []
            
            entries = [IPOEntry.from_api_data(item) for item in data["data"]]
            logger.info(f"Fetched {len(entries)} IPO entries from API")
            return entries
    except httpx.RequestError as e:
        logger.error(f"Error fetching IPO data: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing API response: {e}")
        return []

async def send_telegram_alert(entry: IPOEntry) -> bool:
    """Send a Telegram alert for a new IPO entry"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram configuration is missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Create a rich text message with formatting
    message = (
        f"🚨 *NEW IPO ALERT* 🚨\n\n"
        f"*Symbol:* {entry.symbol_clean}\n"
        f"*Company:* {entry.company_name}\n"
        f"*Units:* {entry.units}\n"
        f"*Price:* NPR {entry.price}\n"
        f"*Opening Date:* {entry.opening_date}\n"
        f"*Closing Date:* {entry.closing_date}\n"
        f"*Issue Manager:* {entry.issue_manager}\n"
        f"*Status:* {entry.status}\n"
    )
    
    if entry.url:
        message += f"\n[View Details]({entry.url})"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Telegram alert sent for {entry.symbol_clean}")
            return True
    except httpx.RequestError as e:
        logger.error(f"Error sending Telegram alert: {e}")
        return False

async def check_for_new_ipos() -> None:
    """Check for new IPO entries and send alerts if found"""
    logger.info("Checking for new IPO entries...")
    
    # Get current known IPO IDs
    known_ids = get_known_ipo_ids()
    
    # Fetch latest IPO data
    latest_entries = await fetch_ipo_data()
    
    # Identify new entries
    new_entries = [entry for entry in latest_entries if entry.id not in known_ids]
    
    if new_entries:
        logger.info(f"Found {len(new_entries)} new IPO entries")
        
        # Save new entries to database
        save_ipo_entries(new_entries)
        
        # Send alerts for new entries
        for entry in new_entries:
            await send_telegram_alert(entry)
    else:
        logger.info("No new IPO entries found")

async def main() -> None:
    """Main function to run the IPO alert system"""
    logger.info("Starting IPO Alert System")
    
    # Setup database
    setup_database()
    
    # Initial check
    await check_for_new_ipos()
    
    logger.info("Initial check completed. Scheduling regular checks every 2 hours.")
    
    # Schedule regular checks every 2 hours
    schedule.every(2).hours.do(lambda: asyncio.run(check_for_new_ipos()))
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute between checks

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 