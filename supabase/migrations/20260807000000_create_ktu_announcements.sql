create table if not exists public.ktu_announcements (
    content_hash text primary key,
    title text not null,
    announcement_date text,
    description text,
    source_url text,
    resource_id text,
    pdf_path text,
    pdf_filename text,
    first_seen_at timestamptz not null default now(),
    telegram_sent_at timestamptz,
    telegram_document_sent_at timestamptz
);

alter table public.ktu_announcements add column if not exists description text;
alter table public.ktu_announcements add column if not exists telegram_sent_at timestamptz;
