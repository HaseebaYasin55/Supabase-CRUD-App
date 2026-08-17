create extension if not exists "pgcrypto";

create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    file_name text not null,
    storage_path text not null unique,
    file_type text not null,
    file_size bigint not null check (file_size >= 0),
    description text,
    category text not null default 'General',
    validation_tag text,
    uploaded_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_documents_uploaded_at on public.documents (uploaded_at desc);
create index if not exists idx_documents_category on public.documents (category);

create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_documents_updated_at on public.documents;
create trigger trg_documents_updated_at
    before update on public.documents
    for each row
    execute function public.set_updated_at();

alter table public.documents enable row level security;

drop policy if exists "Allow all access to documents" on public.documents;
create policy "Allow all access to documents"
    on public.documents
    for all
    using (true)
    with check (true);