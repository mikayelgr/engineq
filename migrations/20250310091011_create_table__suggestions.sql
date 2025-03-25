-- migrate:up
create table suggestions (
    pid integer not null references playlists(id) on delete cascade,
    tid integer not null references tracks(id) on delete cascade,
    added_at timestamptz default now(),
    consumed boolean default false,
    PRIMARY KEY (pid, tid)
);

-- migrate:down
drop table suggestions;