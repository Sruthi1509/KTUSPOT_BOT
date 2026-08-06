create table if not exists ktu_announcements (
    content_hash text primary key,
    title text not null,
    announcement_date text,
    source_url text,
    resource_id text,
    first_seen_at timestamptz not null default now(),
    telegram_sent_at timestamptz
);

-- Supports upgrades from the earlier schema.
alter table ktu_announcements add column if not exists first_seen_at timestamptz;
alter table ktu_announcements add column if not exists telegram_sent_at timestamptz;
update ktu_announcements set first_seen_at = now() where first_seen_at is null;
