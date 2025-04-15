-- migrate:up
ALTER TABLE subscribers
ADD COLUMN note TEXT DEFAULT NULL;

-- migrate:down
ALTER TABLE subscribers
DROP COLUMN note;
