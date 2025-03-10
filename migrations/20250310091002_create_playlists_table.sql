-- migrate:up
create table playlists (
    id serial primary key,
    sid integer references subscribers(id) on delete cascade,
    created_at date default now(),
    UNIQUE(sid, created_at)
);

-- migrate:down
drop table playlists;