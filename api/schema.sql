-- Buildings: 3D footprints and structural metadata
CREATE TABLE IF NOT EXISTS buildings (
    id              SERIAL PRIMARY KEY,
    building_code   TEXT UNIQUE NOT NULL,
    name            TEXT,
    height_m        DOUBLE PRECISION,
    floors          INTEGER,
    year_built      INTEGER,
    structure_type  TEXT,
    footprint       GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS buildings_footprint_idx ON buildings USING GIST (footprint);

-- Sensor time series: readings from fixed devices
CREATE TABLE IF NOT EXISTS sensor_readings (
    id            BIGSERIAL PRIMARY KEY,
    sensor_id     TEXT NOT NULL,
    recorded_at   TIMESTAMPTZ NOT NULL,
    metric        TEXT NOT NULL,
    value         DOUBLE PRECISION NOT NULL,
    location      GEOMETRY(POINT, 4326),
    building_id   INTEGER REFERENCES buildings(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS sensor_readings_sensor_time_idx
    ON sensor_readings (sensor_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS sensor_readings_location_idx
    ON sensor_readings USING GIST (location);

-- Derived heat metrics per building per day
CREATE TABLE IF NOT EXISTS heat_metrics (
    id                  BIGSERIAL PRIMARY KEY,
    building_id         INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    metric_date         DATE NOT NULL,
    lst_c               DOUBLE PRECISION,
    ndvi                DOUBLE PRECISION,
    landcover_class     SMALLINT,
    hotspot             BOOLEAN DEFAULT FALSE,
    risk_score          DOUBLE PRECISION,
    UNIQUE (building_id, metric_date)
);
CREATE INDEX IF NOT EXISTS heat_metrics_date_idx ON heat_metrics (metric_date);
