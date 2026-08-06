# KTU Announcement Telegram Bot

Scrapes KTU announcements, sends only unseen ones to Telegram, and stores
successful deliveries in PostgreSQL or a local SQLite database.

## Quick local run (no database URL)

No database setup is required to test the bot. With `DATABASE_URL` unset, it
automatically creates `ktu_announcements.db` beside the Python files and uses
it to prevent repeat messages. Keep this file as your local backup. Set
`LOCAL_DB_PATH` only if you want it stored elsewhere.

## PostgreSQL setup

PostgreSQL is optional. To use it instead of the local backup:

1. Create a database, for example `ktu_bot`.
2. Run [postgres_schema.sql](postgres_schema.sql) against that database:

   ```bash
   psql "$DATABASE_URL" -f postgres_schema.sql
   ```

3. Set `DATABASE_URL` to a standard PostgreSQL connection URL:

   ```text
   postgresql://username:password@hostname:5432/ktu_bot
   ```

## Telegram setup

1. In Telegram, open **@BotFather**, send `/newbot`, and follow the prompts.
2. Copy the bot token BotFather returns. This is `TELEGRAM_BOT_TOKEN`.
3. Add the bot to the target group/channel. For a channel, promote it to an
   administrator with permission to post messages.
4. Send a message in the target group, or send a direct message to the bot.
5. In a browser, open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`.
   Find `"chat":{"id":...}` in the response. This numeric value is
   `TELEGRAM_CHAT_ID`. Group and channel IDs commonly begin with `-100`.

For a private channel, post one message after adding the bot before calling
`getUpdates`. Do not commit the bot token or database password.

## Install and run

```bash
pip install -r requirements.txt
playwright install chromium
```

Create a file named `.env` in this folder using `.env.example` as the format:

```dotenv
TELEGRAM_BOT_TOKEN=token-from-botfather
TELEGRAM_CHAT_ID=your-chat-id
```

`main.py` loads `.env` automatically. Leave `DATABASE_URL` out to use the
local SQLite backup database, then run `python main.py`.

Every scraped announcement is stored in `ktu_announcements` immediately.
The `telegram_sent_at` field is set only after Telegram confirms delivery, so
failed sends can be retried. Each run prints the scraped data and pending
Telegram items as formatted JSON in the terminal.

Only announcements dated today or within the previous two calendar days are
scraped. Older KTU announcements are ignored.

To inspect KTU's current rendered announcements:

```bash
python scraper.py
```
