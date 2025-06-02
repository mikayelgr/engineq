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

-- 1. Rename subscriber_id back to sid on playback
ALTER TABLE playback RENAME COLUMN subscriber_id TO sid;

-- 2. Drop the new FK on playback.suggestion_id -> suggestions(id)
ALTER TABLE playback DROP CONSTRAINT IF EXISTS playback_suggestion_id_fkey;

-- 3. Drop the new PK on suggestions(id) (which was named suggestions_pkey in the 'up' script)
ALTER TABLE suggestions DROP CONSTRAINT IF EXISTS suggestions_pkey;

-- 4. Restore old PK on suggestions(pid, tid)
ALTER TABLE suggestions ADD CONSTRAINT suggestions_pkey PRIMARY KEY (pid, tid);

-- 5. Add back last_pid and last_tid columns to playback
ALTER TABLE playback ADD COLUMN last_pid INTEGER;
ALTER TABLE playback ADD COLUMN last_tid INTEGER;

-- 6. Populate last_pid and last_tid from suggestion_id
-- This relies on suggestions.id, suggestions.pid, and suggestions.tid still being available.
-- Ensure that the suggestions table has not been altered and that the id, pid, and tid columns are intact.
-- The following UPDATE statement assumes that each playback.suggestion_id corresponds to a valid suggestions.id.
UPDATE playback p
SET last_pid = s.pid, last_tid = s.tid
FROM suggestions s
WHERE p.suggestion_id = s.id;

-- 7. Restore FK on playback(last_pid, last_tid) -> suggestions(pid, tid)
-- This assumes the original FK name was playback_last_pid_last_tid_fkey, which is stated in the 'up' script
ALTER TABLE playback ADD CONSTRAINT playback_last_pid_last_tid_fkey
FOREIGN KEY (last_pid, last_tid) REFERENCES suggestions(pid, tid);

-- 8. Drop the suggestion_id column from playback
ALTER TABLE playback DROP COLUMN suggestion_id;
