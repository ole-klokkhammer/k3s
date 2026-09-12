-- surveillance.events + embeddings
--
-- run INSIDE the `surveillance` database on the postgres LXC (core:postgres):
--   psql -h <postgres> -U <admin> -d surveillance -f schema.sql
--
-- the app user (surveillance_user) is provisioned like the opennvr one:
-- role + password live on the host in /env (never in git), and the LXCs
-- connect with the PG_DSN from their env files.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE SCHEMA IF NOT EXISTS surveillance;

CREATE TABLE IF NOT EXISTS surveillance.events (
    id          bigserial,
    ts          timestamptz NOT NULL,
    camera      text NOT NULL,
    class       text NOT NULL,
    conf        real,                 -- detector confidence (NULL when written by the embedder from a still)
    still_path  text,                 -- path inside the camagent LXC (/media/detector/events/...)
    embedding   vector(512),         -- CLIP ViT-B/32 image+text space
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, ts)
);

-- one chunk per day; tune with retention/volume
SELECT create_hypertable('surveillance.events', 'ts',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- query hot paths
CREATE INDEX IF NOT EXISTS events_camera_ts_idx ON surveillance.events (camera, ts DESC);
CREATE INDEX IF NOT EXISTS events_class_ts_idx  ON surveillance.events (class, ts DESC);

-- vector search: build once the table has data (~10k+ rows, ivfflat needs volume):
-- CREATE INDEX events_embedding_idx ON surveillance.events
--     USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- grant to the app user (adjust role name to your provisioned one)
-- GRANT USAGE ON SCHEMA surveillance TO surveillance_user;
-- GRANT SELECT, INSERT ON surveillance.events TO surveillance_user;
