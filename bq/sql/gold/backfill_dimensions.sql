-- Ethioware – Gold dimension backfill from Silver
-- Idempotent: uses MERGE or INSERT … WHERE NOT EXISTS to avoid duplicates.
-- Run statements in order (dims before bridge).
-- Run in project: ethioware-etl

-- ═══════════════════════════════════════════════════════════════════════════
-- 1. dim_date  (calendar dates covering all Silver data)
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.dim_date` AS t
USING (
  SELECT
    date_id,
    EXTRACT(YEAR FROM date_id)      AS year,
    EXTRACT(MONTH FROM date_id)     AS month,
    EXTRACT(DAY FROM date_id)       AS day,
    EXTRACT(ISOWEEK FROM date_id)   AS week,
    EXTRACT(QUARTER FROM date_id)   AS quarter,
    EXTRACT(DAYOFWEEK FROM date_id) AS day_of_week,
    EXTRACT(DAYOFWEEK FROM date_id) IN (1, 7) AS is_weekend
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE('2020-01-01'), CURRENT_DATE())) AS date_id
) AS s
ON t.date_id = s.date_id
WHEN NOT MATCHED THEN
  INSERT (date_id, year, month, day, week, quarter, day_of_week, is_weekend)
  VALUES (s.date_id, s.year, s.month, s.day, s.week, s.quarter, s.day_of_week, s.is_weekend);

-- ═══════════════════════════════════════════════════════════════════════════
-- 2. dim_field  (static seed: 4 programs + Other)
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.dim_field` AS t
USING (
  SELECT field_id, field_name FROM UNNEST([
    STRUCT(1 AS field_id, 'Engineering Basics' AS field_name),
    STRUCT(2, 'SE Basics'),
    STRUCT(3, 'Medicine Basics'),
    STRUCT(4, 'Law Basics'),
    STRUCT(99, 'Other')
  ])
) AS s
ON t.field_id = s.field_id
WHEN NOT MATCHED THEN
  INSERT (field_id, field_name)
  VALUES (s.field_id, s.field_name);

-- ═══════════════════════════════════════════════════════════════════════════
-- 3. dim_learning_provider  (static seed)
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.dim_learning_provider` AS t
USING (
  SELECT provider_id, provider_name FROM UNNEST([
    STRUCT(1 AS provider_id, 'Khan Academy' AS provider_name)
  ])
) AS s
ON t.provider_id = s.provider_id
WHEN NOT MATCHED THEN
  INSERT (provider_id, provider_name)
  VALUES (s.provider_id, s.provider_name);

-- ═══════════════════════════════════════════════════════════════════════════
-- 4. dim_cohort  (from Silver registrations)
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.dim_cohort` AS t
USING (
  SELECT DISTINCT
    cohort_name AS cohort_id,
    CASE
      WHEN cohort_name = '2024-11' THEN 'November 2024'
      WHEN cohort_name = '2025-05' THEN 'May 2025'
      WHEN cohort_name = '2025-07' THEN 'July 2025'
      WHEN cohort_name = '2025-09' THEN 'September 2025'
      ELSE CONCAT('Cohort ', cohort_name)
    END AS cohort_name_display,
    SAFE.PARSE_DATE('%Y-%m', cohort_name) AS start_date,
    DATE_ADD(SAFE.PARSE_DATE('%Y-%m', cohort_name), INTERVAL 2 MONTH) AS end_date
  FROM `ethioware-etl.silver_trainings.registrations`
  WHERE cohort_name IS NOT NULL AND cohort_name != 'Unknown'
) AS s
ON t.cohort_id = s.cohort_id
WHEN NOT MATCHED THEN
  INSERT (cohort_id, cohort_name, start_date, end_date)
  VALUES (s.cohort_id, s.cohort_name_display, s.start_date, s.end_date);

-- ═══════════════════════════════════════════════════════════════════════════
-- 5. dim_institution  (from Silver registrations)
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.dim_institution` AS t
USING (
  SELECT
    ROW_NUMBER() OVER (ORDER BY institution_name) + COALESCE(
      (SELECT MAX(institution_id) FROM `ethioware-etl.gold_trainings.dim_institution`), 0
    ) AS institution_id,
    institution_name
  FROM (
    SELECT DISTINCT TRIM(highschool_name) AS institution_name
    FROM `ethioware-etl.silver_trainings.registrations`
    WHERE highschool_name IS NOT NULL
      AND TRIM(highschool_name) != ''
      AND TRIM(highschool_name) NOT IN (
        SELECT institution_name FROM `ethioware-etl.gold_trainings.dim_institution`
      )
  )
) AS s
ON t.institution_name = s.institution_name
WHEN NOT MATCHED THEN
  INSERT (institution_id, institution_name)
  VALUES (s.institution_id, s.institution_name);

-- ═══════════════════════════════════════════════════════════════════════════
-- 6. dim_learner  (from Silver registrations)
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.dim_learner` AS t
USING (
  SELECT
    learner_id,
    DATE(MIN(COALESCE(start_time, ingestion_time))) AS first_seen_date,
    MAX(cohort_name)                                 AS latest_cohort_id,
    COUNT(*)                                         AS registration_count
  FROM `ethioware-etl.silver_trainings.registrations`
  WHERE learner_id IS NOT NULL
  GROUP BY learner_id
) AS s
ON t.learner_id = s.learner_id
WHEN MATCHED THEN
  UPDATE SET
    first_seen_date    = LEAST(t.first_seen_date, s.first_seen_date),
    latest_cohort_id   = s.latest_cohort_id,
    registration_count = s.registration_count
WHEN NOT MATCHED THEN
  INSERT (learner_id, first_seen_date, latest_cohort_id, registration_count)
  VALUES (s.learner_id, s.first_seen_date, s.latest_cohort_id, s.registration_count);

-- ═══════════════════════════════════════════════════════════════════════════
-- 7. bridge_learner_field  (from Silver registrations)
--    Maps program_selection → field_id via dim_field.
--    "Both" in scores cohort will be handled separately (fact-building phase).
-- ═══════════════════════════════════════════════════════════════════════════
MERGE `ethioware-etl.gold_trainings.bridge_learner_field` AS t
USING (
  SELECT DISTINCT
    r.learner_id,
    f.field_id,
    r.cohort_name AS cohort_id,
    'registration' AS source
  FROM `ethioware-etl.silver_trainings.registrations` r
  JOIN `ethioware-etl.gold_trainings.dim_field` f
    ON LOWER(TRIM(r.program_selection)) = LOWER(f.field_name)
  WHERE r.learner_id IS NOT NULL
    AND r.cohort_name IS NOT NULL
    AND r.cohort_name != 'Unknown'
) AS s
ON  t.learner_id = s.learner_id
AND t.field_id   = s.field_id
AND t.cohort_id  = s.cohort_id
WHEN NOT MATCHED THEN
  INSERT (learner_id, field_id, cohort_id, source)
  VALUES (s.learner_id, s.field_id, s.cohort_id, s.source);
