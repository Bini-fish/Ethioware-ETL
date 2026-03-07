-- Ethioware – pipeline_run_log (audit for ingestion runs)
-- Lives in silver_trainings; all domains (trainings, marketing) log here with source column.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.pipeline_run_log` (
  run_id       STRING NOT NULL OPTIONS(description = 'Unique run identifier (e.g. UUID or bucket+path+timestamp)'),
  source       STRING NOT NULL OPTIONS(description = 'Source identifier: bucket/prefix or domain name, e.g. ethioware-bronze-trainings/forms/, registrations'),
  status       STRING NOT NULL OPTIONS(description = 'SUCCESS, PARTIAL, FAILED'),
  row_count    INT64 OPTIONS(description = 'Rows inserted into Silver'),
  error_count  INT64 OPTIONS(description = 'Rows written to rejects'),
  message      STRING OPTIONS(description = 'Optional error or summary message'),
  timestamp    TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader to CURRENT_TIMESTAMP()')
)
OPTIONS(
  description = 'Log each ingestion run for troubleshooting and data freshness. Query by source and timestamp.'
);
