-- migrate:up
create table tracks (
    id serial primary key,
    title varchar not null,
    artist varchar not null,
    explicit boolean default false,
    duration integer not null,
    uri text not null,
    image text,
    UNIQUE(title, artist)
);

-- migrate:down
drop table tracks;