-- Ethioware – silver_trainings.ka_activity
-- Khan Academy (and future providers) activity. One row per learner per source/period.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.ka_activity` (
  learner_identifier    STRING NOT NULL OPTIONS(description = 'student column; map to learner_id in Gold where possible'),
  provider_id           STRING NOT NULL OPTIONS(description = 'e.g. khan_academy'),
  total_learning_minutes INT64,
  skills_worked_on      INT64,
  skills_leveled_up     INT64,
  skills_to_improve     INT64,
  attempted             INT64,
  familiar              INT64,
  proficient            INT64,
  mastered              INT64,
  source_file           STRING NOT NULL,
  ingestion_time        TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader')
)
OPTIONS(
  description = 'KA activity export; one row per learner per file. Cohort/period from context if needed.'
);
