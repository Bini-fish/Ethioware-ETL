-- Ethioware – dim_learner (Gold learner dimension)
-- One row per learner; no PII. Join to secure_core.secure_id_map for email/name.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.dim_learner` (
  learner_id          STRING NOT NULL OPTIONS(description = 'SHA-256 hash; PK; join to secure_core for PII'),
  first_seen_date     DATE OPTIONS(description = 'Earliest registration or score date'),
  latest_cohort_id    STRING OPTIONS(description = 'Most recent cohort_id (YYYY-MM)'),
  registration_count  INT64 OPTIONS(description = 'Number of registration records')
)
OPTIONS(
  description = 'Learner dimension. No PII stored; use secure_core.secure_id_map for name/email.'
);
