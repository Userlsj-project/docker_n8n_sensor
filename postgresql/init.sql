CREATE TABLE IF NOT EXISTS sensor_data (
  id          SERIAL PRIMARY KEY,
  temperature FLOAT,
  humidity    FLOAT,
  pressure    FLOAT,
  recorded_at TIMESTAMP DEFAULT NOW()
);
