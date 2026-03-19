-- Ethioware – dim_institution (Gold institution dimension)
-- One row per unique highschool/institution from registrations.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.dim_institution` (
  institution_id    INT64 NOT NULL OPTIONS(description = 'Surrogate PK; auto-assigned during backfill'),
  institution_name  STRING NOT NULL OPTIONS(description = 'Highschool or institution name from registrations')
)
OPTIONS(
  description = 'Institution dimension derived from silver_trainings.registrations.highschool_name.'
);
