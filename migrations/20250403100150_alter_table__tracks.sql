-- migrate:up
ALTER TABLE tracks
ADD COLUMN search_embedding VECTOR(1024) NULL;

CREATE INDEX ON tracks USING hnsw (search_embedding vector_cosine_ops);

-- migrate:down
DROP INDEX tracks_search_embedding_idx;

ALTER TABLE tracks
DROP COLUMN search_embedding;