-- migrate:up
create table playback (
    sid integer primary key references subscribers(id) on delete cascade,
    last_pid integer,
    -- whicih playlist the user was left on
    last_tid integer,
    -- which track the user was left on
    foreign key (last_pid, last_tid) references suggestions(pid, tid)
);

-- migrate:down
drop table playback;
