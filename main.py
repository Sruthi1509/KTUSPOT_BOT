"""
Orchestrates: scrape -> filter new -> notify -> mark as sent.

Run this on a schedule (cron / GitHub Actions) every 15-30 min.
"""

import json
import os

from config import load_environment
from scraper import fetch_announcements
from state import DatabaseError, filter_new, mark_sent
from notifier import send_announcement


def run():
    load_environment()
    try:
        all_items = fetch_announcements()
    except Exception as e:
        print(f"Scrape failed: {e}")
        return

    print(json.dumps({"scraped_count": len(all_items), "announcements": all_items}, indent=2, ensure_ascii=False))

    try:
        new_items = filter_new(all_items)
    except DatabaseError as error:
        print(f"Database store/check failed: {error}")
        return

    print(json.dumps({"telegram_pending_count": len(new_items), "telegram_pending": new_items}, indent=2, ensure_ascii=False))

    if not new_items:
        print("No new announcements.")
        return

    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        print("Telegram is not configured; announcements were stored locally and remain pending.")
        return

    sent_ok = []
    for item in new_items:
        if send_announcement(item):
            sent_ok.append(item)

    try:
        mark_sent(sent_ok)
    except DatabaseError as error:
        print(f"Telegram sent {len(sent_ok)} announcement(s), but database recording failed: {error}")
        return
    print(f"Sent {len(sent_ok)} new announcement(s).")


if __name__ == "__main__":
    run()
