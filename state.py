"""Delivery state stored in PostgreSQL or a local SQLite fallback database."""

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg


class DatabaseError(RuntimeError):
    """Raised when the delivery state cannot be read or recorded."""


PLACEHOLDER_DATABASE_URL = "postgresql://username:password@localhost:5432/ktu_bot"


def _hash(item: dict) -> str:
    raw = "|".join(str(item.get(field, "")) for field in ("title", "date", "description", "link", "resource_id"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _local_database_path() -> Path:
    return Path(os.environ.get("LOCAL_DB_PATH", "ktu_announcements.db"))


def _create_sqlite_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ktu_announcements (
            content_hash TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            announcement_date TEXT,
            source_url TEXT,
            resource_id TEXT,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            telegram_sent_at TEXT
        )
        """
    )
    columns = {row[1] for row in connection.execute("PRAGMA table_info(ktu_announcements)")}
    if "first_seen_at" not in columns:
        connection.execute("ALTER TABLE ktu_announcements ADD COLUMN first_seen_at TEXT")
        if "sent_at" in columns:
            connection.execute("UPDATE ktu_announcements SET first_seen_at = sent_at WHERE first_seen_at IS NULL")
        connection.execute("UPDATE ktu_announcements SET first_seen_at = CURRENT_TIMESTAMP WHERE first_seen_at IS NULL")
    if "telegram_sent_at" not in columns:
        connection.execute("ALTER TABLE ktu_announcements ADD COLUMN telegram_sent_at TEXT")


@contextmanager
def _connection():
    """Use PostgreSQL when configured, otherwise create/use the local backup."""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url == PLACEHOLDER_DATABASE_URL:
        database_url = ""
    if database_url:
        try:
            with psycopg.connect(database_url, connect_timeout=15) as connection:
                yield connection, "%s"
        except psycopg.Error as error:
            raise DatabaseError(f"PostgreSQL connection failed: {error}") from error
        return

    try:
        with sqlite3.connect(_local_database_path()) as connection:
            _create_sqlite_table(connection)
            yield connection, "?"
    except sqlite3.Error as error:
        raise DatabaseError(f"Local SQLite database failed: {error}") from error


def filter_new(items: list[dict]) -> list[dict]:
    """Store scraped announcements and return only those not sent to Telegram."""
    try:
        with _connection() as (connection, placeholder):
            cursor = connection.cursor()
            new_items = []
            for item in items:
                content_hash = _hash(item)
                cursor.execute(
                    f"""
                    INSERT INTO ktu_announcements
                        (content_hash, title, announcement_date, source_url, resource_id)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                    ON CONFLICT (content_hash) DO NOTHING
                    """,
                    (content_hash, item["title"], item.get("date") or None, item.get("link") or None, item.get("resource_id") or None),
                )
                cursor.execute(f"SELECT telegram_sent_at FROM ktu_announcements WHERE content_hash = {placeholder}", (content_hash,))
                sent_at = cursor.fetchone()[0]
                if sent_at is None:
                    item["_hash"] = content_hash
                    new_items.append(item)
            return new_items
    except (psycopg.Error, sqlite3.Error) as error:
        raise DatabaseError(f"Database lookup failed: {error}") from error


def mark_sent(items: list[dict]) -> None:
    """Save only announcements that Telegram accepted successfully."""
    if not items:
        return
    hashes = [(item["_hash"],) for item in items]
    try:
        with _connection() as (connection, placeholder):
            connection.cursor().executemany(
                f"""
                UPDATE ktu_announcements
                SET telegram_sent_at = CURRENT_TIMESTAMP
                WHERE content_hash = {placeholder}
                """,
                hashes,
            )
    except (psycopg.Error, sqlite3.Error) as error:
        raise DatabaseError(f"Database insert failed: {error}") from error
