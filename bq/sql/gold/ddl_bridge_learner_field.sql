-- Ethioware – bridge_learner_field (Gold bridge table)
-- Maps learners to fields and cohorts. Handles multi-field enrollment
-- (e.g. "Both" in November scores → two rows, one per field).
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.bridge_learner_field` (
  learner_id  STRING NOT NULL OPTIONS(description = 'FK → dim_learner.learner_id'),
  field_id    INT64  NOT NULL OPTIONS(description = 'FK → dim_field.field_id'),
  cohort_id   STRING NOT NULL OPTIONS(description = 'FK → dim_cohort.cohort_id'),
  source      STRING OPTIONS(description = 'How this mapping was derived: registration, scores, manual')
)
OPTIONS(
  description = 'Bridge table: learner × field × cohort. One row per enrollment. Supports multi-field via multiple rows.'
);
