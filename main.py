"""
Orchestrates: scrape -> filter new -> notify -> mark as sent.

Run this on a schedule (cron / GitHub Actions) every 15-30 min.
"""

import json
import os

from config import load_environment
from scraper import fetch_announcements
from state import StateStoreError, filter_new, mark_document_sent, mark_sent
from notifier import send_announcement


def run():
    load_environment()
    try:
        all_items = fetch_announcements()
    except Exception as e:
        print(f"Scrape failed: {e}")
        return

    print(json.dumps({"scraped_count": len(all_items), "announcements": _log_items(all_items)}, indent=2, ensure_ascii=False))

    try:
        new_items = filter_new(all_items)
    except StateStoreError as error:
        print(f"Supabase store/check failed: {error}")
        return

    print(json.dumps({"telegram_pending_count": len(new_items), "telegram_pending": _log_items(new_items)}, indent=2, ensure_ascii=False))

    if not new_items:
        print("No new announcements.")
        return

    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        print("Telegram is not configured; announcements were stored locally and remain pending.")
        return

    sent_ok = []
    for item in new_items:
        message_sent, document_sent = send_announcement(item)
        if document_sent:
            try:
                mark_document_sent(item)
            except StateStoreError as error:
                print(f"Telegram PDF was sent but its delivery could not be recorded: {error}")
                continue
        if message_sent:
            sent_ok.append(item)

    try:
        mark_sent(sent_ok)
    except StateStoreError as error:
        print(f"Telegram sent {len(sent_ok)} announcement(s), but Supabase recording failed: {error}")
        return
    print(f"Sent {len(sent_ok)} new announcement(s).")


def _log_items(items: list[dict]) -> list[dict]:
    """Keep binary PDFs and delivery bookkeeping out of diagnostic JSON."""
    return [
        {key: value for key, value in item.items() if key not in {"pdf_content", "_hash", "_document_sent"}}
        | {"has_pdf": bool(item.get("pdf_content"))}
        for item in items
    ]


if __name__ == "__main__":
    run()
