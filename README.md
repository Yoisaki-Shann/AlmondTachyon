# AlmondTachyon
A Discord bot designed to track Club Fan Counts, Member Activity, and Weekly Growth for Uma Musume Pretty Derby.


## Features
📊 Live Leaderboards: Scrapes real-time fan counts for all 30 members.
📈 Growth Tracking: Automatically calculates weekly fan gains and daily averages.
🕒 Activity Monitor: Checks "Last Login" times to identify inactive members.
🔗 Discord Linking: Bind In-Game Names (IGN) to Discord Users for easier pinging.
🏢 Multi-Club Support: Monitor multiple clubs (e.g., Main & Sub) simultaneously.
🤖 Automated Reporting: Runs a full report every Sunday at 20:00 (8 PM).
💾 Data Persistence: Saves history to CSV for long-term analysis.

## Directory Structure
```text
AlmondTachyon/
├── .env                 # Discord Token (Not uploaded to GitHub)
├── main.py              # Bot Entry Point
├── utils.py             # Configuration & Helper Functions
├── Cogs/                # Bot Commands
│   ├── Public.py        # Commands for everyone (!members, !player)
│   └── Staff.py         # Commands for Mods (!link, !weekly)
└── Data/                # Database Storage
    ├── json/            # Bindings & Weekly Snapshots
    └── csv/             # Long-term history logs
```

## ⚠️ Disclaimer
This bot is for educational and community management purposes.
Do not close the Chrome window while the bot is running.
Do not turn off the PC if you require 24/7 uptime. (need to keep Chrome open)
This tool is not affiliated with Cygames. Use responsibly.