-- Ethioware – silver_trainings.registrations
-- Microsoft Form exports only. PII (email, full name) in secure_core.secure_id_map; here only learner_id.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.registrations` (
  registration_id     STRING NOT NULL OPTIONS(description = 'Form submission ID (capital ID from form)'),
  learner_id          STRING NOT NULL OPTIONS(description = 'SHA-256(lower(trim(Email2))); join to secure_core for PII'),
  start_time          TIMESTAMP OPTIONS(description = 'Form start time'),
  completion_time     TIMESTAMP OPTIONS(description = 'Form completion time'),
  last_modified_time  TIMESTAMP OPTIONS(description = 'Last modified – from form'),
  highschool_name     STRING,
  citizenship         STRING,
  commitment_per_week STRING OPTIONS(description = 'e.g. 8-10, 11-15, 16-20, 20-22'),
  grade               STRING,
  gpa_4_scale         FLOAT64 OPTIONS(description = 'GPA normalized to 4.0 scale'),
  telegram_username   STRING,
  where_heard_category STRING OPTIONS(description = 'social_media, word_of_mouth, other'),
  linkedin_follow     STRING OPTIONS(description = 'Yes/No from form'),
  program_selection   STRING NOT NULL OPTIONS(description = 'From filename: Engineering Basics, Medicine Basics, SE Basics, Law Basics'),
  cohort_name        STRING OPTIONS(description = 'From filename'),
  source_file         STRING NOT NULL,
  ingestion_time      TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader'),
  schema_version      STRING OPTIONS(description = 'e.g. v1')
)
OPTIONS(
  description = 'Registration records; PII only in secure_core.secure_id_map. One row per submission.'
);
