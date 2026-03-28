# dbq-bid-monitor

A lightweight Python bot that monitors [Databoutique](https://www.databoutique.com) for new **Open** bids and sends instant **Telegram** notifications. Never miss a bid again.

![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey)

---

## How It Works

1. Polls the Databoutique API on a configurable interval (default: 15 min)
2. Filters for bids with status `Open`
3. Compares results against previously seen bid IDs (`seen_bids.json`)
4. Sends a Telegram alert for any new bid — no duplicate notifications
5. Alerts you automatically if your session cookie expires

---

## Prerequisites

| Requirement | Version | Download |
|-------------|---------|----------|
| Python | 3.8+ | [python.org](https://www.python.org/downloads/) |
| pip | latest | Bundled with Python |
| Telegram account | — | [telegram.org](https://telegram.org) |
| Databoutique account | — | [databoutique.com](https://www.databoutique.com) |

---

## Project Structure

```
dbq-bid-monitor/
├── bid_monitor.py       # Main bot script
├── env.template        # Config template — copy to .env and fill in
├── requirements.txt     # Python dependencies
├── bid-monitor.service  # systemd service (Linux — run on boot)
├── seen_bids.json       # Auto-generated — tracks notified bid IDs
└── bid_monitor.log      # Auto-generated — runtime logs
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Anzywiz/dbq-bid-monitor.git
cd dbq-bid-monitor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> On Linux you may need `pip3` instead of `pip`.

---

## Configuration

### Step 1 — Set up your Telegram Bot

1. Open Telegram and message **[@BotFather](https://t.me/BotFather)**
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** (looks like `7123456789:AAFxxx...`)
4. Message **[@userinfobot](https://t.me/userinfobot)** and send `/start`
5. Copy your numeric **Chat ID** (e.g. `123456789`)
6. **Important:** Open your new bot in Telegram and press **Start** before running the script

### Step 2 — Get your Databoutique session cookie

1. Log into [databoutique.com](https://www.databoutique.com) in Chrome or Firefox
2. Press `F12` → **Network** tab → reload the page
3. Click any request to `www.databoutique.com`
4. In the **Headers** panel, find `cookie:` and copy the entire value

> ⚠️ Session cookies expire after a few days. When you see a `401` error in the logs, repeat this step and update your `.env`.

### Step 3 — Create your `.env` file

```bash
cp .env.template .env
```

Open `.env` and fill in your values:

```dotenv
DATABOUTIQUE_COOKIE=your_full_cookie_string_here
TELEGRAM_BOT_TOKEN=7123456789:AAFxxx...
TELEGRAM_CHAT_ID=123456789
CHECK_INTERVAL=900
```

> `CHECK_INTERVAL` is in seconds. `900` = 15 min, `300` = 5 min, `1800` = 30 min.

---

## Usage

### Linux

**Run manually:**
```bash
python3 bid_monitor.py
```

**Run as a background service (survives reboots):**
```bash
# Copy files to /opt
sudo mkdir -p /opt/bid-monitor
sudo cp bid_monitor.py requirements.txt .env /opt/bid-monitor/
sudo chmod 600 /opt/bid-monitor/.env

# Edit the service file — set User= to your Linux username
nano bid-monitor.service

# Install and enable
sudo cp bid-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bid-monitor

# Useful commands
sudo systemctl status bid-monitor       # check status
sudo journalctl -u bid-monitor -f       # live logs
sudo systemctl restart bid-monitor      # restart after config change
```

### Windows

**Run manually:**
```powershell
python bid_monitor.py
```

**Run on startup (Task Scheduler):**
1. Open **Task Scheduler** → *Create Basic Task*
2. Set trigger to **At log on**
3. Action: **Start a program**
   - Program: `python`
   - Arguments: `C:\path\to\bid_monitor.py`
   - Start in: `C:\path\to\dbq-bid-monitor\`
4. Check *Run whether user is logged on or not*

> On Windows, ensure Python is added to your `PATH` during installation.

---

## Updating an Expired Cookie

```bash
# Linux (systemd)
nano /opt/bid-monitor/.env        # paste new cookie
sudo systemctl restart bid-monitor

# Linux / Windows (manual run)
# Just edit .env and restart the script
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Missing required config` | `.env` not filled in or not found | Ensure `.env` is in the same folder as `bid_monitor.py` |
| `401 Auth failed` | Cookie expired | Copy a fresh cookie from your browser |
| `chat not found` (Telegram) | Bot never received a message | Open your bot in Telegram and press **Start** |
| No alerts for new bids | Cookie expired silently | Check `bid_monitor.log` for errors |
| Script exits immediately | Unhandled error | Run in terminal and read the traceback |

---

## License

MIT