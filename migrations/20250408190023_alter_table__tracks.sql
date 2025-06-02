-- migrate:up
ALTER TABLE tracks
ADD COLUMN genres TEXT[] DEFAULT NULL;

-- migrate:down
ALTER TABLE tracks
DROP COLUMN genres;
