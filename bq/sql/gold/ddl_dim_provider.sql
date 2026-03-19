-- Ethioware – dim_learning_provider (Gold learning provider dimension)
-- Static seed: Khan Academy initially; add more providers as they are onboarded.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.dim_learning_provider` (
  provider_id    INT64 NOT NULL OPTIONS(description = 'Surrogate PK'),
  provider_name  STRING NOT NULL OPTIONS(description = 'e.g. Khan Academy')
)
OPTIONS(
  description = 'Learning provider dimension. Currently Khan Academy only; extensible.'
);
