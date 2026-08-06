"""Supabase-backed announcement state for the Telegram delivery workflow."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

TABLE = "ktu_announcements"


class StateStoreError(RuntimeError):
    """Raised when Supabase cannot read or update announcement state."""


def _content_hash(item: dict) -> str:
    fields = ("title", "date", "description", "link", "resource_id")
    content = "|".join(str(item.get(field, "")) for field in fields)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SupabaseClient:
    url: str
    api_key: str

    @classmethod
    def from_environment(cls) -> "SupabaseClient":
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        api_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not api_key:
            raise StateStoreError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        return cls(url=url, api_key=api_key)

    @property
    def headers(self) -> dict[str, str]:
        return {"apikey": self.api_key, "Authorization": f"Bearer {self.api_key}"}

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        try:
            response = requests.request(method, f"{self.url}{path}", headers=headers, timeout=15, **kwargs)
        except requests.RequestException as error:
            raise StateStoreError(f"Supabase request failed: {error}") from error
        if not response.ok:
            raise StateStoreError(f"Supabase returned {response.status_code}: {response.text}")
        return response


def filter_new(items: list[dict]) -> list[dict]:
    """Persist scraped announcements and return the subset pending Telegram."""
    if not items:
        return []

    client = SupabaseClient.from_environment()
    rows = []
    hashes: dict[str, dict] = {}
    for item in items:
        content_hash = _content_hash(item)
        hashes[content_hash] = item
        rows.append(
            {
                "content_hash": content_hash,
                "title": item["title"],
                "announcement_date": item.get("date") or None,
                "description": item.get("description") or None,
                "source_url": item.get("link") or None,
                "resource_id": item.get("resource_id") or None,
            }
        )

    client.request(
        "POST",
        f"/rest/v1/{TABLE}",
        headers={**client.headers, "Content-Type": "application/json", "Prefer": "resolution=ignore-duplicates,return=minimal"},
        params={"on_conflict": "content_hash"},
        json=rows,
    )

    pending_items = []
    for content_hash, item in hashes.items():
        response = client.request(
            "GET",
            f"/rest/v1/{TABLE}",
            params={"select": "telegram_sent_at", "content_hash": f"eq.{content_hash}", "limit": "1"},
        )
        records = response.json()
        if not records:
            raise StateStoreError("Supabase did not return a stored announcement.")
        if records[0]["telegram_sent_at"] is None:
            item["_hash"] = content_hash
            pending_items.append(item)
    return pending_items


def mark_sent(items: list[dict]) -> None:
    """Record Telegram delivery only after the Telegram API accepted it."""
    if not items:
        return

    client = SupabaseClient.from_environment()
    for item in items:
        client.request(
            "PATCH",
            f"/rest/v1/{TABLE}",
            headers={**client.headers, "Content-Type": "application/json", "Prefer": "return=minimal"},
            params={"content_hash": f"eq.{item['_hash']}"},
            json={"telegram_sent_at": datetime.now(timezone.utc).isoformat()},
        )
