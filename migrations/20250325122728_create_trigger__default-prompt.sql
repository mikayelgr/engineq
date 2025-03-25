-- migrate:up
CREATE FUNCTION create_default_prompt_fn() RETURNS TRIGGER AS $$ BEGIN
INSERT INTO
    prompts (sid, prompt)
VALUES
    (
        NEW.id,
        'Generate a curated playlist with a balanced mix of regular, crowd-friendly music that creates a welcoming and engaging atmosphere for a general business setting throughout the day.'
    );

RETURN NEW;

END;

$$ LANGUAGE plpgsql;

CREATE TRIGGER create_default_prompt
AFTER
INSERT
    ON subscribers FOR EACH ROW EXECUTE FUNCTION create_default_prompt_fn();

-- migrate:down
DROP TRIGGER create_default_prompt ON subscribers;

DROP FUNCTION create_default_prompt_fn();