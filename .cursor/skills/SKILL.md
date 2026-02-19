---
name: ethioware-etl
description: Implements and maintains the Ethioware EdTech GCP Medallion pipeline (Bronze/Silver/Gold) using Cloud Functions, BigQuery, and Looker Studio, with strict PII separation and education-specific scoring. Use when working on data ingestion, transformations, schemas, or dashboards for Ethioware.
---

# Ethioware ETL

## Purpose

This skill guides the agent when working on the **Ethioware EdTech GCP Medallion pipeline**, ensuring:

- Consistent architecture (Bronze → Silver → Gold).
- Correct handling of **learner identity and PII**.
- Stable **schemas and scoring logic** over time.
- Correct use of **GCP services** (GCS, Cloud Functions/Run, BigQuery, Looker Studio).

Use this skill whenever modifying or creating:

- Cloud Functions / Cloud Run services for Ethioware ingestion.
- BigQuery datasets, tables, views, or scheduled queries for Ethioware.
- Data models, scoring logic, or dashboards related to Ethioware.

## Project Context

- Ethioware is an **EdTech initiative** with 2‑month cohorts in:
  - Engineering, Software Engineering, Medicine, Law.
- Most near‑term data sources:
  - **Google Forms / Sheets exports** for registrations.
  - **CSV uploads** for quiz / KA scores and some marketing data.
  - **Khan Academy activity** (later possibly another learning provider).
  - **Social media & web analytics** (YouTube, LinkedIn, website).
- Long term:
  - Direct **Sheets API** for registrations.
  - **YouTube Data API v3** and **LinkedIn Marketing API** for marketing automation.

## Architecture Rules

### Medallion Layers

- **Bronze – Raw Landing (GCS)**
  - Raw files exactly as received (Forms/Sheets/CSV/API).
  - Organized by **domain** and **source** (e.g. `trainings/forms`, `trainings/scores`, `marketing/youtube`).
  - No heavy transformations; minimal parsing only if needed to load.

- **Silver – Standardized (BigQuery)**
  - Schema‑on‑write, typed, cleaned tables.
  - Cloud Functions:
    - Triggered by GCS `finalize` events.
    - Do **light ETL** only:
      - Validate schema (required columns, types as much as possible).
      - Normalize obvious text/number formats (e.g. commas in numeric fields).
      - Load into Silver tables.
      - Write failed rows into `_rejects` tables with error reasons.
    - Are **idempotent**: safe if the same file is seen again.

- **Gold – Analytics / Star Schema (BigQuery)**
  - Dim/fact modeling:
    - `dim_learner`, `dim_cohort`, `dim_field`, `dim_institution`, `dim_date`, `dim_channel`, etc.
    - `bridge_learner_field` for multi‑field enrollment (e.g. “Both”).
    - Facts for scores, engagement, feedback, marketing reach.
  - Business logic (scoring, ranks, engagement metrics) lives in **SQL views** and **scheduled queries**, not in functions.

## Identity & PII

- Canonical key: **`learner_id`**, derived from email:
  - Normalize first: trim + lowercase.
  - Hash with a stable algorithm (e.g. SHA‑256) and **never change** without a migration.
- PII separation:
  - `secure_core.secure_id_map` (or similarly named dataset/table) holds:
    - `learner_id`, canonical email, full name, and any other PII.
  - Analytical datasets (`silver_*`, `gold_*`, `dash_*`) must **not** contain direct emails or full names.
- Access:
  - Only **Education Admins** can access PII tables or views that join back to PII.

## Trainings Domain

### Silver Tables (examples)

- `silver_trainings.registrations`
  - From Forms/Sheets.
  - Columns similar to `Engineering_Basics_Learner_Registration_clean_data.csv`:
    - Registration timestamps, `Full Name`, `Email1`, institution, citizenship, grade, GPA, weekly commitment, LinkedIn follow flag, cohort, intended field(s).
- `silver_trainings.scores_raw`
  - From CSV uploads such as **November score sheet** and `May_Cohort_Scores_clean_data.csv`.
  - Handle:
    - Numeric fields with commas (e.g. `"2,561.00"` minutes).
    - Duplicate or partial rows (dedupe and send incomplete rows to `_rejects`).
    - `Cohort` values like `Both` for multi‑field learners.
- `silver_trainings.ka_activity`
  - From `learner_activity_khan_academy_clean_data.csv` and similar.
  - Grain: per learner per provider (initially Khan Academy) with total minutes and skill mastery counts.
- `silver_trainings.feedback`
  - Seeded from existing `*_sentiment.csv`.
  - New feedback:
    - If sentiment is missing, call Cloud Natural Language API.
    - Store `sentiment_label`, `sentiment_score`, and `model_version`.

### Gold Tables / Views

- Dimensions:
  - `dim_learner`, `dim_cohort` (2‑month cycles), `dim_field`, `dim_institution`, `dim_date`, `dim_learning_provider`.
  - `bridge_learner_field` for mapping learners to fields and cohorts.
- Facts:
  - `fact_scores`: quiz scores, KA/learning platform scores, learning minutes, and derived metrics.
  - `fact_engagement`: composites built from KA/future provider activity (minutes, skills, mastery).
  - `fact_feedback`: feedback with sentiment and metadata.
- Scoring:
  - Implement formulas as **versioned views** (e.g. `gold_trainings.v_scores_v1`).
  - Relative metrics (e.g. `%KA`, total points, ranks) always computed with:
    - `PARTITION BY cohort_id, field_id` (and provider if needed).
    - Dynamic `MAX()` based on current cohort data, not constants.

## Marketing & Brand Reach

- Ingestion cadence:
  - **Weekly** YouTube and LinkedIn data preferred (API or standardized CSV snapshots).
- Silver:
  - Store UTC timestamps, raw counts (views, watch time, clicks, impressions, reactions, etc.).
  - Maintain `source`, `granularity` (daily/weekly), and `campaign`/`content` identifiers when available.
- Gold:
  - `dim_channel`, `dim_content`, `dim_campaign`.
  - `fact_marketing_reach` at daily/weekly grain.
  - Views joining marketing metrics with registrations/cohorts for ROI analysis.

## Dashboards & Access

- Back dashboards with `dash_*` views that:
  - Hide PII by default.
  - Pre‑aggregate heavy computations.
- Target audiences:
  - **Admins**: detailed learner‑level metrics (still anonymized; optional authorized view for reveal).
  - **Marketing**: campaign/channel performance by cohort and time.
  - **Board**: high‑level KPIs and trends only.
  - **Public**: fully anonymized, aggregate metrics fit for the company website.

## Implementation Guidelines

- Prefer **BigQuery SQL** for joins, aggregations, scoring, and backfills.
- Keep Cloud Functions/Cloud Run services:
  - Small, focused, and idempotent.
  - Limited to schema checks, parsing, and loading into Silver.
- Always:
  - Validate schemas from Forms/Sheets/CSVs and fail fast to `_rejects` on mismatch.
  - Track ingestion in `pipeline_run_log` / audit tables with row counts and error counts.
  - Partition big facts by date; cluster by key IDs (e.g. `learner_id`, `video_id`) where appropriate.
- When future providers replace Khan Academy:
  - Add them as rows in `dim_learning_provider`.
  - Keep Silver tables source‑specific but map to a common Gold schema.
