-- migrate:up
ALTER TABLE suggestions
ADD COLUMN id UUID NOT NULL DEFAULT gen_random_uuid();

-- migrate:down
ALTER TABLE suggestions
DROP COLUMN id;
