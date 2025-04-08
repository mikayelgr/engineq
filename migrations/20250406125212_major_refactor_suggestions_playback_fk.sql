-- migrate:up
-- 1. Add UUID column to suggestions with default value
-- added in previous migrations

-- 2. Add suggestion_id column to playback
ALTER TABLE playback
ADD COLUMN suggestion_id UUID;

-- 3. Populate suggestion_id using existing (pid, tid) relation
UPDATE playback p
SET suggestion_id = s.id
FROM suggestions s
WHERE p.last_pid = s.pid AND p.last_tid = s.tid;

-- 4. Drop existing FK on (last_pid, last_tid)
ALTER TABLE playback
DROP CONSTRAINT playback_last_pid_last_tid_fkey;

-- 5. Drop old (last_pid, last_tid) columns
ALTER TABLE playback
DROP COLUMN last_pid,
DROP COLUMN last_tid;

-- 6. Drop old PK on suggestions
ALTER TABLE suggestions
DROP CONSTRAINT IF EXISTS suggestions_pkey;

-- 7. Add new PK on suggestions(id)
ALTER TABLE suggestions
ADD CONSTRAINT suggestions_pkey PRIMARY KEY (id);

-- 8. Optionally preserve uniqueness of (pid, tid)
-- ALTER TABLE suggestions
-- ADD CONSTRAINT suggestions_pid_tid_unique UNIQUE (pid, tid);

-- 9. Add FK on playback.suggestion_id -> suggestions(id)
ALTER TABLE playback
ADD CONSTRAINT playback_suggestion_id_fkey
FOREIGN KEY (suggestion_id) REFERENCES suggestions(id) ON DELETE CASCADE;

ALTER TABLE playback
RENAME COLUMN sid TO subscriber_id;

-- migrate:down
-- Note: This operation is irreversible