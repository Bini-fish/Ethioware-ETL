-- Ethioware – dim_field (Gold field/program dimension)
-- Static seed: 4 known fields + Other. Surrogate INT key.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.dim_field` (
  field_id    INT64 NOT NULL OPTIONS(description = 'Surrogate PK'),
  field_name  STRING NOT NULL OPTIONS(description = 'e.g. Engineering Basics, SE Basics, Medicine Basics, Law Basics, Other')
)
OPTIONS(
  description = 'Field/program dimension. Seeded with known Ethioware fields.'
);
