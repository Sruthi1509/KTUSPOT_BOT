"""Send KTU announcements to a Telegram chat via the Bot API."""

import html
import os
import requests

from config import load_environment


load_environment()


def send_announcement(item: dict) -> bool:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        print("Telegram is not configured: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return False
    lines = [f"<b>KTU Announcement: {html.escape(item['title'])}</b>"]
    if item.get("date"):
        lines.append(html.escape(item["date"]))
    if item.get("description"):
        lines.append(html.escape(item["description"])[:3_500])
    if item.get("link"):
        lines.append(f'<a href="{html.escape(item["link"], quote=True)}">View announcement</a>')
    response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                             json={"chat_id": chat_id, "text": "\n\n".join(lines), "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=15)
    if not response.ok:
        print(f"Telegram send failed for '{item['title']}': {response.text}")
    return response.ok
