-- migrate:up
ALTER TABLE suggestions
DROP COLUMN consumed;

-- migrate:down

