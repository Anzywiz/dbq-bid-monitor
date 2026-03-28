#!/usr/bin/env python3
"""
Databoutique Open Bid Monitor
Polls for Open bids and sends Telegram alerts when new ones appear.
"""

import requests
import json
import time
import logging
import os
from dotenv import load_dotenv

# Auto-load .env file from the same directory as this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ──────────────────────────────────────────────────────────────
#  ALL CONFIG IS READ FROM .env (or environment variables)
#  Never hardcode secrets here. Edit the .env file instead.
# ──────────────────────────────────────────────────────────────

DATABOUTIQUE_COOKIE = os.environ.get("DATABOUTIQUE_COOKIE", "")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL      = int(os.environ.get("CHECK_INTERVAL", "900"))  # default 15 min

# ──────────────────────────────────────────────────────────────
#  API SETTINGS
# ──────────────────────────────────────────────────────────────

API_URL = (
    "https://www.databoutique.com/v1/datasource/airtable/"
    "dcd71be8-aa8c-4249-9343-99cc36daabf3/"
    "2a1d1c6a-4426-44c4-9eb5-d730f2d08fe9/"
    "2a026384-9040-4969-b313-badb5be85d22/"
    "ff845401-a0b2-4d14-aa8a-dbae586e05fb/data"
)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://www.databoutique.com",
    "referer": "https://www.databoutique.com/seller-bid-list",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

PAYLOAD = {
    "options": {"cellFormat": "string", "timeZone": "UTC", "userLocale": "en-US"},
    "pageContext": None,
    "filterCriteria": {
        "filterConditionGroup": {
            "logicalOperator": "AND",
            "filterGroups": [
                {
                    "logicalOperator": "OR",
                    "filters": [
                        {
                            "subject": "Bid Status",
                            "operator": "INLINE_CONTAINS",
                            "value": "Open"
                        }
                    ],
                }
            ],
        }
    },
    "pagingOption": {"offset": None, "count": 50},
    "sortingOption": {"sortingField": "Created date", "sortType": "DESC"},
}

# ──────────────────────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bid_monitor.log"),
    ],
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
#  STATE — persists seen bid IDs across restarts
# ──────────────────────────────────────────────────────────────

STATE_FILE = "seen_bids.json"

def load_seen_bids() -> set:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_bids(seen: set):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f)

# ──────────────────────────────────────────────────────────────
#  DATABOUTIQUE API
# ──────────────────────────────────────────────────────────────

def fetch_open_bids() -> list:
    headers = {**HEADERS, "cookie": DATABOUTIQUE_COOKIE}
    try:
        resp = requests.post(API_URL, headers=headers, json=PAYLOAD, timeout=20)
        if resp.status_code == 401:
            log.error("Auth failed (401) — cookie has expired. Update DATABOUTIQUE_COOKIE in .env")
            send_telegram("⚠️ *Bid Monitor*: Databoutique cookie expired\\. Please update it\\.")
            return []
        resp.raise_for_status()
        return resp.json().get("records", [])
    except requests.exceptions.RequestException as e:
        log.error(f"Network error: {e}")
        return []

# ──────────────────────────────────────────────────────────────
#  TELEGRAM
# ──────────────────────────────────────────────────────────────

def send_telegram(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            log.info("Telegram message sent.")
            return True
        log.warning(f"Telegram error {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Failed to send Telegram message: {e}")
        return False

def format_message(bids: list) -> str:
    count = len(bids)
    lines = [f"🔔 *{count} New Open Bid{'s' if count > 1 else ''}* on Databoutique!\n"]
    for b in bids:
        f = b.get("fields", {})
        lines.append(
            f"📦 *{f.get('Macro Product (from Product)', 'N/A')}*\n"
            f"   💰 {f.get('Bid Price', '?')}  |  🌍 {f.get('Geography Code (from Product)', '?')}\n"
            f"   🗓️ Expires: {f.get('Expiration Date', '?')}\n"
            f"   🔁 {f.get('Frequency', '?')}  |  Type: {f.get('Product Type (from Product)', '?')}\n"
        )
    lines.append("👉 [View on Databoutique](https://www.databoutique.com/seller-bid-list)")
    return "\n".join(lines)

# ──────────────────────────────────────────────────────────────
#  CONFIG VALIDATION
# ──────────────────────────────────────────────────────────────

def validate_config() -> bool:
    missing = []
    if not DATABOUTIQUE_COOKIE:
        missing.append("DATABOUTIQUE_COOKIE")
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        log.error("Missing required config: %s", ", ".join(missing))
        log.error("Set these in your .env file — see README.md.")
        return False
    return True

# ──────────────────────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────────────────────

def run():
    log.info("=" * 55)
    log.info("  Databoutique Bid Monitor starting up")
    log.info("  Check interval: %d seconds (%d min)", CHECK_INTERVAL, CHECK_INTERVAL // 60)
    log.info("=" * 55)

    if not validate_config():
        return

    seen_bids = load_seen_bids()
    log.info("Loaded %d previously seen bid IDs.", len(seen_bids))

    send_telegram(
        f"✅ *Bid Monitor started*\n"
        f"Checking every {CHECK_INTERVAL // 60} min for Open bids."
    )

    while True:
        log.info("Checking for open bids...")
        records = fetch_open_bids()

        if records:
            new_bids = [r for r in records if r["id"] not in seen_bids]
            if new_bids:
                log.info("Found %d new open bid(s)!", len(new_bids))
                send_telegram(format_message(new_bids))
                for r in new_bids:
                    seen_bids.add(r["id"])
                save_seen_bids(seen_bids)
            else:
                log.info("%d open bid(s) found — all already seen.", len(records))
        else:
            log.info("No open bids right now.")

        log.info("Next check in %d seconds.\n", CHECK_INTERVAL)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()