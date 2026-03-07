-- Ethioware – dim_date (Gold date dimension)
-- Used for partitioning and joining facts. Populate via backfill script or one-time INSERT.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.dim_date` (
  date_id    DATE NOT NULL OPTIONS(description = 'Calendar date; primary key'),
  year       INT64 NOT NULL,
  month      INT64 NOT NULL,
  day        INT64 NOT NULL,
  week       INT64 OPTIONS(description = 'ISO week of year'),
  quarter    INT64 NOT NULL OPTIONS(description = '1-4'),
  day_of_week INT64 OPTIONS(description = '1=Monday, 7=Sunday'),
  is_weekend BOOL OPTIONS(description = 'Saturday or Sunday')
)
OPTIONS(
  description = 'Date dimension for Gold facts. Backfill with date range covering all Silver data.'
);

-- Example backfill (run separately or in a backfill_*.sql):
-- INSERT INTO `ethioware-etl.gold_trainings.dim_date` (date_id, year, month, day, week, quarter, day_of_week, is_weekend)
-- SELECT date_id, EXTRACT(YEAR FROM date_id), EXTRACT(MONTH FROM date_id), EXTRACT(DAY FROM date_id),
--   EXTRACT(WEEK FROM date_id), EXTRACT(QUARTER FROM date_id),
--   EXTRACT(DAYOFWEEK FROM date_id), EXTRACT(DAYOFWEEK FROM date_id) IN (1, 7)
-- FROM UNNEST(GENERATE_DATE_ARRAY(DATE('2020-01-01'), CURRENT_DATE())) AS date_id;
