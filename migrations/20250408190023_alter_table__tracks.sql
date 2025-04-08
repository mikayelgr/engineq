-- migrate:up
ALTER TABLE tracks
ADD COLUMN genres TEXT[] DEFAULT NULL;

-- migrate:down
-- This migration cannot be reverted.
