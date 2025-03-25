-- migrate:up
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    -- Optional description of the conditions when this prompt must be used
    active_when TEXT,
    sid INT NOT NULL REFERENCES subscribers(id)
);

-- migrate:down
DROP TABLE prompts;