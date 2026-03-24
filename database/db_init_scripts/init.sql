\c

\set db_name 'pitstop_db'

SELECT 'CREATE DATABASE ' || :'db_name' || ';' AS create_db_query
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db_name')
\gexec

\c :db_name

CREATE EXTENSION IF NOT EXISTS postgis;  -- For spatial data support

CREATE TABLE IF NOT EXISTS parking_spots (
    id SERIAL PRIMARY KEY,
    description VARCHAR(100) NOT NULL UNIQUE,
    coordinates GEOMETRY(POINT, 4326) NOT NULL,
    rack_type VARCHAR(20),
    rack_count INT,
    shelter_indicator VARCHAR(1)
);

-- For quicker nearest-neighbor searches
CREATE INDEX coordinates_idx
ON parking_spots
USING GIST (coordinates);
