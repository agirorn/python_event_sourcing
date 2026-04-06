-- events
--
-- Stores all events for a single events for the aggregate
CREATE TABLE events (
    -- event
    --
    -- stores all the event data for each event
    event        JSONB NOT NULL,

    -- Convenience columns for filtering/indexing
    event_id     UUID GENERATED ALWAYS AS ((event->>'event_id')::uuid) STORED NOT NULL,
    aggregate_id TEXT GENERATED ALWAYS AS ((event->>'aggregate_id')::text) STORED NOT NULL,
    event_name   TEXT GENERATED ALWAYS AS (event->>'name') STORED NOT NULL,

    -- occ_version serves as a OPTIMIZING CONCURRENT VERSIONS and per-aggregate ordering
    --
    -- OPTIMIZING CONCURRENT VERSIONS: Prevents more than 1 user from performing
    -- changes to the aggregate at any one time.
    occ_version  BIGINT GENERATED ALWAYS AS ((event->>'occ_version')::bigint) STORED NOT NULL,


    -- Optional: duplicate timestamp for easier querying
    -- event_ts      timestamptz GENERATED ALWAYS AS ((envelope->>'timestamp')::timestamptz) STORED,

    -- saved_at: stores the time of when the event was saved to the database.
    saved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (aggregate_id, occ_version),
    UNIQUE (event_id)
);


-- state
--
-- Store the latest state of the aggregate for fast lookup and processing.
-- This might need to be rebuild when the state object changes unless the new
-- version of the state can deserialize an ol version of the state.
CREATE TABLE states (
  state        JSONB NOT NULL,
  aggregate_id TEXT GENERATED ALWAYS AS ((state->>'aggregate_id')::text) STORED PRIMARY KEY NOT NULL,

  -- occ_version serves as a OPTIMIZING CONCURRENT VERSIONS
  occ_version  BIGINT GENERATED ALWAYS AS ((state->>'occ_version')::bigint) STORED NOT NULL,

  -- saved_at: stores the time of when the event was saved to the database.
  saved_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE todos (
   id TEXT PRIMARY KEY,
   message text UNIQUE NOT NULL,
   deleted boolean UNIQUE NOT NULL DEFAULT false
);
