alter table public.ktu_announcements add column if not exists pdf_path text;
alter table public.ktu_announcements add column if not exists pdf_filename text;
alter table public.ktu_announcements add column if not exists telegram_document_sent_at timestamptz;

insert into storage.buckets (id, name, public)
values ('announcement-pdfs', 'announcement-pdfs', false)
on conflict (id) do nothing;
