-- migrate:up
ALTER TABLE prompts
DROP CONSTRAINT prompts_sid_fkey;

ALTER TABLE prompts
ADD CONSTRAINT prompts_sid_fkey
FOREIGN KEY (sid)
REFERENCES subscribers(id)
ON DELETE CASCADE;

-- migrate:down
ALTER TABLE prompts DROP CONSTRAINT IF EXISTS prompts_sid_fkey;
ALTER TABLE prompts ADD CONSTRAINT prompts_sid_fkey FOREIGN KEY (sid) REFERENCES subscribers(id);
