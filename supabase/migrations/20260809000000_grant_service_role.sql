-- Grant necessary privileges to the Supabase service role
GRANT SELECT, INSERT ON public.ktu_announcements TO service_role;
