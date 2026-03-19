-- Ethioware – dim_cohort (Gold cohort dimension)
-- One row per cohort. Cohort ID follows YYYY-MM convention from Silver.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.gold_trainings.dim_cohort` (
  cohort_id    STRING NOT NULL OPTIONS(description = 'YYYY-MM format, e.g. 2025-05; PK'),
  cohort_name  STRING OPTIONS(description = 'Human-readable, e.g. May 2025, November 2024'),
  start_date   DATE OPTIONS(description = 'Cohort start date'),
  end_date     DATE OPTIONS(description = 'Cohort end date (~2 months after start)')
)
OPTIONS(
  description = 'Cohort dimension. ~6 cohorts per year, each lasting ~2 months.'
);
