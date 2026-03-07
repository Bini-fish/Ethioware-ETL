-- Ethioware – Silver rejects tables (templates)
-- Rows that fail validation go here with reject_reason. Same dataset as main Silver tables.
-- Run in project: ethioware-etl

-- Registrations: mirror key columns + reject_reason (full Silver shape added in Sprint 2)
CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.registrations_rejects` (
  source_file     STRING OPTIONS(description = 'GCS path or file name'),
  ingestion_time  TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader to CURRENT_TIMESTAMP()'),
  reject_reason   STRING NOT NULL OPTIONS(description = 'e.g. schema_mismatch, invalid_email, duplicate'),
  raw_row         STRING OPTIONS(description = 'Original row as JSON for debugging')
);

-- Scores: key identifiers + reject_reason
CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.scores_rejects` (
  source_file     STRING,
  ingestion_time  TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader to CURRENT_TIMESTAMP()'),
  reject_reason   STRING NOT NULL OPTIONS(description = 'e.g. numeric_parse_error, duplicate, incomplete'),
  raw_row         STRING
);

-- KA activity
CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.ka_activity_rejects` (
  source_file     STRING,
  ingestion_time  TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader to CURRENT_TIMESTAMP()'),
  reject_reason   STRING NOT NULL,
  raw_row         STRING
);

-- Feedback
CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.feedback_rejects` (
  source_file     STRING,
  ingestion_time  TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader to CURRENT_TIMESTAMP()'),
  reject_reason   STRING NOT NULL,
  raw_row         STRING
);
