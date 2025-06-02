-- migrate:up
ALTER TABLE suggestions
DROP COLUMN consumed;

-- migrate:down
ALTER TABLE suggestions
ADD COLUMN consumed BOOLEAN DEFAULT false;
