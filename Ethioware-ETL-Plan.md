## Ethioware EdTech – GCP Medallion Pipeline Plan

You can use this file as the master reference for the Ethioware pipeline.

---

## 1. Project Overview

**Goal**: Build a secure, scalable, automated **GCP Medallion data pipeline** (Bronze → Silver → Gold) for the **Ethioware EdTech Initiative** that:

- Standardizes **learner registrations, performance, and engagement** across cohorts and fields.
- Automates **marketing & brand reach** analytics (YouTube, LinkedIn, website).
- Supports **role-based dashboards** (admins, marketing, board, public) while protecting PII.

**Core pattern**: Reuse the working architecture from `Household-Data-Analysis-Real-Time-GCP-Pipeline`:

- **GCS** for raw data (Bronze).
- **Cloud Functions / Cloud Run (Python)** for light ETL into BigQuery (Silver).
- **BigQuery** for data modeling, scoring, and analytics (Gold).
- **Looker Studio** for BI.

---

## 2. Requirements & Assumptions

### 2.1 Business Requirements

- Track cohorts every **2 months** across four fields:
  - Engineering, Software Engineering, Medicine, Law.
- Measure:
  - **Registrations & demographics** (school, citizenship, grade, GPA, etc.).
  - **Performance** (quiz scores, learning platform scores, learning minutes).
  - **Engagement** (learning activity, completion, improvement).
  - **Sentiment** (trainee experience).
  - **Marketing reach** (YouTube, LinkedIn, web traffic) and its impact on registrations.

### 2.2 Data Source Assumptions

- **Near term**:
  - Registrations via **Microsoft Form** or **Google Forms / Sheets** exports (programs: Software Engineering, Medicine, Engineering, Law).
  - Quiz & performance via **CSV uploads** (including Khan Academy scores).
  - KA / learning activity via CSV exports.
  - Feedback via Google Forms → CSV/Sheets.
  - Marketing via:
    - YouTube CSV/API (weekly).
    - LinkedIn CSV initially, LinkedIn Marketing API later (weekly/less frequent).
- **Mid term (~6+ months)**:
  - Possible **new learning provider** replacing Khan Academy.
  - Possible move from CSV to **API/Sheet** integrations for scores.

### 2.3 Technical & Governance Assumptions

- **GCP project**: `Ethioware-ETL` already exists.
- **Region**: Prefer region close to Ethiopia (e.g., `me-central1`); if service unavailable, use EU alternative and document.
- **Identity**:
  - Email is the **immutable primary signal** for learner identity, but we store only a **hashed identifier** in analytics layers.
- **PII retention**: No current policies to delete PII; retain but isolate PII and enforce access controls.

---

## 3. High-Level Architecture

### 3.1 Medallion Layers

- **Bronze (Raw) – GCS**
  - Buckets organized by domain and source:
    - `ethioware-bronze-trainings/forms/`
    - `ethioware-bronze-trainings/scores/`
    - `ethioware-bronze-trainings/feedback/`
    - `ethioware-bronze-marketing/youtube/`
    - `ethioware-bronze-marketing/linkedin/`
    - `ethioware-bronze-web/analytics/`
  - Files are **as-received**: no renames, no schema changes, minimal parsing.

- **Silver (Standardized) – BigQuery**
  - Datasets such as:
    - `silver_trainings`
    - `silver_marketing`
    - `silver_web`
    - `secure_core` (for PII mapping)
  - Cloud Functions / Cloud Run:
    - Triggered by **GCS `finalize` events** (Bronze).
    - Do **light ETL only**:
      - Schema validation.
      - Minimal cleaning (e.g., numeric parsing, trimming).
      - Load into typed Silver tables.
      - Record invalid rows in `_rejects` tables.

- **Gold (Analytics / Star Schema) – BigQuery**
  - Datasets such as `gold_trainings`, `gold_marketing`, `gold_web`, `dash_*`.
  - Dimensional model:
    - Dimensions (`dim_*`), bridge tables, and fact tables.
  - Scoring and metrics:
    - Implemented as **SQL views** and **scheduled queries**.

### 3.2 GCP Services

- **Cloud Storage**: Raw data landing (Bronze).
- **Cloud Functions** (or Cloud Run later):
  - Python-based, triggered by GCS.
- **BigQuery**:
  - Silver staging and standardized tables.
  - Gold dim/fact star schema and analytic views.
- **Looker Studio**:
  - Dashboards built on curated BigQuery views.

---

## 4. Data Model

### 4.1 Identity & PII

- **Learner identifier**: `learner_id`
  - Derived from **normalized email**:
    - `trim(email)` → lowercase → hash (e.g. SHA‑256).
  - The hashing function is **stable and never changed** without migration.
- **PII dataset**: `secure_core`
  - `secure_core.secure_id_map`:
    - `learner_id`
    - `email_canonical`
    - `full_name_raw`
    - optional PII (phone, telegram handle if considered PII, etc.)
  - Access restricted to **Education Admins**.

All other datasets (`silver_*`, `gold_*`, `dash_*`) use only `learner_id` and non-PII attributes.

### 4.2 Shared Dimensions

- `dim_learner`
  - `learner_id`
  - Non-PII attributes (e.g., grade band, citizenship, cohort enrollment flags via joins).
- `dim_cohort`
  - 2‑month cohorts:
    - `cohort_id`, `cohort_name`, `cohort_start_date`, `cohort_end_date`, `field_group`.
- `dim_field`
  - `field_id`, `field_name` (Engineering, Software Engineering, Medicine, Law).
- `dim_institution`
  - `institution_id`, `institution_name`, type, city/region.
- `dim_date`
  - Standard date dimension table for analytics.
- `dim_learning_provider`
  - `provider_id` (e.g., Khan Academy, FutureProviderX), provider name, type.
- `dim_channel` (for marketing)
  - `channel_id` (YouTube, LinkedIn, Web), etc.
- **Bridge**:
  - `bridge_learner_field`:
    - `learner_id`, `field_id`, `cohort_id`, `role`, `start_date`, `end_date`.
    - Supports multi-field enrollment (e.g., “Both” in November sheet).

### 4.3 Trainings Domain – Silver

Examples (exact columns will be refined from the CSVs):

- `silver_trainings.registrations`
  - From Microsoft Form or Google Forms/Sheets.
  - Columns:
    - `registration_id`, `form_submission_id`
    - `full_name_raw`, `Email1`
    - `Highschool Name`, `Citizenship`
    - `Grade`, `GPA(4)`
    - Commitment per week, LinkedIn follow flag
    - `cohort_name`, `field_selection` (may be one or two fields)
    - `source_file`, `ingestion_time`, `schema_version`.

- `silver_trainings.scores_raw`
  - From score sheets (e.g., November, May).
  - Columns:
    - `learner_identifier` (name + username + email where available)
    - `Cohort`, `Field` or `CohortField`
    - `Quiz score`, `Quiz percentage`
    - `Khan Academy score` (or platform score)
    - `Learning Minutes`
    - Any precomputed metrics for reference (but **Gold recomputes authoritative ones**).
    - `source_file`, `ingestion_time`, `row_hash`.
  - **Parsing rules**:
    - Strip commas from numeric strings (`"2,561.00"` → 2561.00).
    - Dedupe duplicate rows (same learner/cohort/field/quiz).
    - Route blank/incomplete rows to `silver_trainings.scores_rejects`.

- `silver_trainings.ka_activity`
  - From `learner_activity_khan_academy_clean_data.csv`.
  - Grain: per learner per provider (Khan Academy) over a time window or cohort.
  - Columns:
    - `learner_identifier`, `provider_id`
    - `total_learning_minutes`, `skills_worked_on`, `skills_leveled_up`
    - `Attempted`, `Familiar`, `Proficient`, `Mastered`
    - `cohort_id` (if reasonably assigned) or `activity_period_start/end`.

- `silver_trainings.feedback`
  - From feedback CSVs.
  - Columns:
    - `feedback_id`, `learner_identifier`, `cohort_id`, `field_id`
    - `feedback_text`, `feedback_type` (e.g., mentor, learner)
    - `sentiment_label`, `sentiment_score`, `model_version` (seeded from existing sentiment CSVs).
    - For new rows: sentiment computed using **Cloud Natural Language API** only when missing.

### 4.4 Trainings Domain – Gold

- `gold_trainings.dim_learner` (joins to secure map when PII needed).
- `gold_trainings.dim_cohort`, `dim_field`, `dim_institution`, `dim_learning_provider`.
- `gold_trainings.bridge_learner_field`.
- `gold_trainings.fact_scores`
  - Grain: per `(learner_id, cohort_id, field_id)` or more granular if multiple tests.
  - Columns:
    - Raw inputs: quiz scores, percentages, KA/platform score, learning minutes.
    - Derived columns (could be in view):
      - `ka_score_normalized`
      - `ka_relative_to_top` (per cohort/field).
      - `total_points`, `engagement_score`, etc.
- `gold_trainings.fact_engagement`
  - Derived from activity (minutes, skill mastery).
- `gold_trainings.fact_feedback`
  - Grain: per feedback entry with sentiment and dimensions.

Scoring and engagement logic live in **versioned views**, e.g.:

- `gold_trainings.v_scores_v1` (first version of scoring model).
- Future changes create `v_scores_v2` etc., while preserving old logic for reproducibility.

### 4.5 Marketing & Web – Silver & Gold

- **Silver**:
  - `silver_marketing.youtube_metrics_daily` or `_weekly`.
  - `silver_marketing.linkedin_metrics_daily` or `_weekly`.
  - `silver_web.analytics` (e.g., website requests by country).
  - All timestamps converted to **UTC**, with source timezone tracked where necessary.

- **Gold**:
  - `gold_marketing.dim_channel`, `dim_content`, `dim_campaign`.
  - `gold_marketing.fact_marketing_reach` (daily/weekly).
  - `gold_marketing.fact_web_traffic` (daily).
  - Views that join:
    - Marketing spikes → registrations/cohort start dates → conversion metrics and ROI.

---

## 5. Scoring & Metrics Design

### 5.1 Principles

- Implement all complex metrics in **BigQuery SQL**, not in Cloud Functions.
- Use **partitioned, versioned views** so the scoring model is auditable and easy to update.

### 5.2 Core Calculations (Examples)

Exact formulas can be refined, but the structure:

- **Base KA Score** (if needed):
  - Combination of raw KA/platform score and learning minutes.
- **Relative KA %**:
  - For each `(cohort_id, field_id)`:
    - `%KA = learner_KA_score / MAX(learner_KA_score)` over that cohort + field.
- **Total Points**:
  - Combine `%KA` and quiz percentage (e.g., `( %KA + quiz_percentage ) / 2`).
- **Engagement Score**:
  - Composite based on:
    - Completion, timeliness, improvement, efficiency.
  - Use weights that can be changed in a new view version.

---

## 6. Ingestion & Scheduling

### 6.1 Trainings

- **Registrations**:
  - Short term: manual or scheduled Sheet → CSV → GCS.
  - Medium term: direct **Google Sheets API** to GCS or BigQuery.
  - Trigger: GCS `finalize` → Cloud Function → `silver_trainings.registrations`.

- **Scores & KA Activity**:
  - CSV uploads (e.g., November and May score sheets, KA activity).
  - Trigger: GCS `finalize` → Cloud Function → Silver tables.
  - Important:
    - Normalize numeric formats.
    - Deduplicate and validate key constraints.

- **Feedback**:
  - CSV/Forms exports → Bronze.
  - Cloud Function:
    - Write to `silver_trainings.feedback`.
    - For rows without sentiment: send to **NLP API** and store labels.

### 6.2 Marketing & Web

- **YouTube**:
  - Weekly scheduled Cloud Function:
    - Calls YouTube Data API v3.
    - Writes raw JSON/CSV to Bronze; transforms to Silver.
- **LinkedIn**:
  - Initially weekly CSV exports to Bronze.
  - Later:
    - Weekly LinkedIn Marketing API calls → Bronze → Silver.
- **Web Analytics**:
  - CSV exports (e.g., requests by country).
  - Regular ingestion into Silver.

### 6.3 Orchestration & Monitoring

- Use **Cloud Scheduler** where needed to trigger functions.
- Maintain:
  - `pipeline_run_log` table with per-source ingestion status.
  - `_rejects` tables for invalid records.
  - Optional: a small **Pipeline Health dashboard** in Looker Studio (data freshness, last run status, error counts).

---

## 7. Security, Governance, and Access

- **Datasets**:
  - `secure_core`: PII mapping; admins only.
  - `silver_*`: ETL/service accounts + data engineers.
  - `gold_*`: analytics/data, used for dashboards.
  - `dash_*`: views specifically for dashboards; role-based.
- **Dashboards**:
  - **Admin dashboard**:
    - Detailed metrics; optional authorized view that can reveal PII for approved users.
  - **Marketing dashboard**:
    - Campaign & channel performance; no PII.
  - **Board dashboard**:
    - High-level KPIs, trends.
  - **Public dashboard**:
    - Fully anonymized, aggregated metrics suitable for the website.

---

## 8. Implementation Plan (12-Week Sprints)

### Sprint 1 (Weeks 1–3): Foundation & Governance

- Set region and project settings.
- Create **GCS buckets** (Bronze) with folder structure for Trainings/Marketing/Web.
- Create **BigQuery datasets**:
  - `secure_core`, `silver_trainings`, `silver_marketing`, `silver_web`, `gold_trainings`, `gold_marketing`, `gold_web`, `dash_*`.
- Define **IAM roles**:
  - Education Admin, Data Engineer, BI/Marketing, Public.
- Set up **`secure_core.secure_id_map`** table and base `dim_date`.
- Create **audit/log tables** (`pipeline_run_log`, rejects templates).

### Sprint 2 (Weeks 4–6): Trainings – Silver Layer

- Design schemas and create:
  - `silver_trainings.registrations`
  - `silver_trainings.scores_raw`
  - `silver_trainings.ka_activity`
  - `silver_trainings.feedback`
  - Associated `_rejects` tables.
- Implement Cloud Functions for:
  - Registrations ingestion.
  - Score/KA CSV ingestion (handle commas, duplicates, blanks).
  - Feedback ingestion + conditional NLP sentiment calls.
- Test using existing **Datasets/trainings/** (and **Datasets/marketing/**) CSVs as historical backfill.

### Sprint 3 (Weeks 7–9): Trainings – Gold Layer & Scoring

- Define and create:
  - `dim_learner`, `dim_cohort`, `dim_field`, `dim_institution`, `dim_learning_provider`.
  - `bridge_learner_field`.
  - `fact_scores`, `fact_engagement`, `fact_feedback`.
- Implement **scoring and ranking** as SQL:
  - Create `v_scores_v1` and any needed engagement views.
  - Ensure partitioning and clustering for cost and performance.
- Run backfill queries to populate Gold from Silver for all available history.

### Sprint 4 (Weeks 10–12): Marketing + BI

- Design and create Silver/Gold tables for:
  - YouTube metrics.
  - LinkedIn metrics.
  - Web analytics.
- Implement weekly ingestion (CSV initially; API where available).
- Create `dash_*` views for:
  - Admin, Marketing, Board, Public dashboards.
- Build Looker Studio dashboards:
  - Wire them to `dash_*` views.
- Finalize documentation:
  - Architecture diagrams.
  - Data dictionary.
  - Runbook for ingestion and troubleshooting.

---

## 9. Common Pitfalls & Mitigations (Ethioware-Specific)

- **Numeric parsing errors** (e.g., `"2,561.00"` learning minutes):
  - Always strip commas before casting.
  - Keep raw string + parsed numeric; route unparseable to `_rejects`.
- **Duplicate / partial rows in score sheets**:
  - Use `row_hash` and `(learner, cohort, field)` keys to dedupe.
  - Send incomplete records to rejects with reasons.
- **“Both” / multi-field enrollment**:
  - Avoid duplicating learner rows.
  - Use `bridge_learner_field` and ensure facts are keyed with both `learner_id` and `field_id`.
- **Schema drift from Forms/Sheets**:
  - Maintain **expected schema manifests** by source.
  - Reject mismatches and alert rather than silently breaking.
- **Future provider changes (Khan Academy → other)**:
  - Use `dim_learning_provider`.
  - Keep Silver source-specific; map to common Gold metrics.
- **Cost & quota blow-ups**:
  - Partition and cluster big tables.
  - Use weekly aggregation for marketing where possible.
  - Implement incremental loads based on `last_run_timestamp`.

---

## 10. How to Use This Plan

- Treat this document as the **master blueprint** for Ethioware ETL.
- When working in Cursor:
  - Load this plan and the **`ethioware-etl` skill** so any model understands the context.
- When adding new features:
  - Check changes against:
    - Medallion boundaries.
    - Identity & PII rules.
    - Dim/fact & view structure.
    - Role-based dashboard requirements.

