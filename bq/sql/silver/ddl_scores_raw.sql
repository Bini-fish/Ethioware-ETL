-- Ethioware – silver_trainings.scores_raw
-- Unified schema from November and May score sheets. Strip commas from Learning Minutes; dedupe by row_hash.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.scores_raw` (
  learner_identifier  STRING NOT NULL OPTIONS(description = 'Name, username, or email as in source; map to learner_id in Gold'),
  cohort              STRING NOT NULL OPTIONS(description = 'e.g. Medicine Basics, Engineering Basics, Both'),
  field               STRING OPTIONS(description = 'Derived from cohort or Both'),
  quiz_score          FLOAT64,
  quiz_pct            FLOAT64 OPTIONS(description = 'Quiz percentage, numeric'),
  ka_score            FLOAT64 OPTIONS(description = 'Khan Academy score'),
  learning_minutes    FLOAT64 OPTIONS(description = 'Learning minutes; commas stripped in ETL'),
  total_points_pct    FLOAT64 OPTIONS(description = 'If present in source'),
  rank                INT64,
  source_file         STRING NOT NULL,
  ingestion_time      TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader'),
  row_hash            STRING OPTIONS(description = 'Hash for dedupe; learner+cohort+field+scores')
)
OPTIONS(
  description = 'Per-learner scores from November/May score sheets. Dedupe by (learner_identifier, cohort, field).'
);
