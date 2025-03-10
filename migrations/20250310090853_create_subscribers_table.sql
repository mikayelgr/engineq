-- migrate:up
create table subscribers (
    id serial primary key,
    license uuid not null default gen_random_uuid(),
    created_at timestamptz default now()
);

-- migrate:down
drop table subscribers;