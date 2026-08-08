# KTU Announcement Telegram Bot

Scrapes recent KTU announcements, stores them in a local Supabase Docker
instance, and sends only pending announcements to Telegram.

## Start Supabase locally

Install the [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started)
and Docker Desktop, then run this in the project folder:

```powershell
supabase init
supabase start
```

`supabase start` prints the local API URL and `service_role key`. Apply the
included migration with:

```powershell
supabase db reset
```

The table migration is stored in
[20260807000000_create_ktu_announcements.sql](supabase/migrations/20260807000000_create_ktu_announcements.sql).
Existing databases can apply the new PDF-storage migration with:

```powershell
supabase migration up
```

## Configure the bot

Create `.env` beside `main.py` with these values:

```dotenv
TELEGRAM_BOT_TOKEN=token-from-botfather
TELEGRAM_CHAT_ID=your-chat-id
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=service-role-key-from-supabase-start
```

The service-role key is appropriate for this local server-side bot. Never put
it in a browser application or commit `.env`.

## Install and run

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\playwright.exe install chromium
.\.venv\Scripts\python.exe main.py
```

Each run prints structured JSON, stores every scraped item in Supabase, and
uploads each available notification PDF to the private `announcement-pdfs`
Supabase Storage bucket. Its object path is recorded in `ktu_announcements`.
The bot sends the PDF as a Telegram document before sending the announcement
text, and records each delivery so retries do not resend an already-delivered
PDF. The scraper only returns announcements dated today or within the
preceding two days.
