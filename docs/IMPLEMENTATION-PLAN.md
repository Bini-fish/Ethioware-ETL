# Ethioware ETL – Implementation Plan (from workspace scan)

This document maps **Ethioware-ETL-Plan.md** to concrete implementation steps based on a full scan of the repository. Use it as the execution checklist.

---

## 1. Current state (from scan)

### 1.1 Repository layout

| Path | Status |
|------|--------|
| `README.md` | Exists – describes planned structure |
| `Ethioware-ETL-Plan.md` | Exists – master blueprint |
| `.gitignore` | Exists – ignores `Household-Data-Analysis-Real-Time-GCP-Pipeline/` |
| `.cursor/rules/`, `.cursor/skills/` | Exist – pipeline rules and ethioware-etl skill |
| `functions/` | **Missing** – to create |
| `bq/` | **Missing** – to create |
| `docs/` | **Missing** – to create |
| `Datasets/` | Exists – **gitignored**; reference CSVs for schema design and backfill. Layout: **trainings/** (registration, feedback, scores, ka_activity, cohort, legacy), **marketing/** (linkedin, youtube, web_analytics), **reference/**, **archive/** (old structure). |

No Python or SQL files exist yet. All pipeline code and BigQuery artifacts need to be created.

### 1.2 Datasets scanned (source → Silver/Gold mapping)

**Trainings**

| Source file (in Datasets) | Purpose | Silver table | Notes |
|----------------------------|--------|---------------|--------|
| `trainings/cohort/Cohort registration.csv` | Cohort-level aggregates | Reference only / Gold aggregation | Cohort, Training Type, Total Registrations, Conversion rate |
| `trainings/scores/November score sheet - Score sheet.csv` | Per-learner scores | `scores_raw` | Name, Email, User name, Cohort (incl. "Both"), Quiz score, Quiz %, KA score, Learning Minutes (e.g. "2,561.00"), KA Score, %KA, Total points, Rank. **Comma stripping and dedupe required.** |
| `trainings/scores/May_Cohort_Scores_clean_data.csv` | Per-learner scores | `scores_raw` | Name, User-name, Cohort, Quiz score, Quiz %, Khan Academy score, Relative % to top, Average, Rank. **Different column set from November.** |
| `trainings/ka_activity/learner_activity_khan_academy_clean_data.csv` | KA activity | `ka_activity` | student, Total Learning minutes, skills worked on/leveled up/to improve, Attempted, Familiar, Proficient, Mastered |
| `trainings/feedback/SessionFeedbackFromTheMentors_clean_data_sentiment.csv` | Mentor feedback | `feedback` | Rating columns, free text, Attribute/Value sentiment (e.g. "General experience Sentiment", "Neutral") |
| `trainings/feedback/Anonymous_rating_Engineering_basics_clean_data_sentiment.csv` | Learner feedback | `feedback` | Different columns; Rating1/2/3, free text, Attribute/Value sentiment (Positive/Neutral) |
| `trainings/registration/*.xlsx` | **Current** registration (Microsoft Form) | `registrations` | Email2, Last modified time, Where heard → category; program from filename |
| `trainings/legacy/Engineering_Basics_Learner_Registration_clean_data.csv`, Medicine | Legacy Forms registration | `registrations` (backfill) | Id, Start/Completion time, Full Name, Email1, etc. |
| `trainings/legacy/Feb_Cohort_Slides.csv`, `May_Cohort_Slides.csv` | Qualitative / session content | Optional or future | Presenter name, Field, Key concepts, etc. – not in current ETL plan |

**Marketing & web**

| Source file | Purpose | Silver table | Notes |
|-------------|--------|---------------|--------|
| `marketing/linkedin/linkedin-cleaned.csv` | LinkedIn metrics | `linkedin_metrics_*` | Date, Impressions (organic/sponsored/total), Clicks, Reactions, Comments, Reposts, Engagement rate. Daily grain; store in UTC. |
| `marketing/linkedin/ethioware_followers_*.xls`, `ethioware_visitors_*.xls`, competitor_analytics_*.xlsx | LinkedIn (new) | `linkedin_*`, `linkedin_competitor_analytics` | Followers, visitors, competitor dimension. |
| `marketing/youtube/YouTube Analytics - Summary.csv` | Channel summary | `youtube_metrics_*` | Metric, Value (Total Views, Watch Time, Subscribers) – snapshot; may need Top Content CSVs for content-level metrics |
| `marketing/web_analytics/website-cleaned.csv` | Web traffic by country | `silver_web.analytics` | name (country), requests |

### 1.3 Schema and parsing requirements (from plan + data)

- **Identity**: `learner_id` = SHA-256(lower(trim(email))). PII only in `secure_core.secure_id_map`.
- **Numeric parsing**: Strip commas before casting (e.g. `"2,561.00"` → 2561.00); unparseable → `_rejects`.
- **Scores**: Dedupe by (learner, cohort, field) and/or `row_hash`; blank/incomplete rows → `scores_rejects`.
- **Multi-field**: "Both" and multi-field enrollment → `bridge_learner_field`; facts keyed by `learner_id` + `field_id`.
- **Feedback**: Sentiment from CSV if present; else Cloud Natural Language API; store `model_version`.

---

## 2. Implementation roadmap (aligned with 12-week plan)

### Sprint 1 (Weeks 1–3): Foundation & governance

**GCP (manual / Terraform / gcloud)**

1. Set project `Ethioware-ETL` and region (e.g. `me-central1`; document fallbacks).
2. Create GCS buckets and prefixes (Bronze):
   - `ethioware-bronze-trainings/forms/`, `scores/`, `feedback/`
   - `ethioware-bronze-marketing/youtube/`, `linkedin/`
   - `ethioware-bronze-web/analytics/`
3. Create BigQuery datasets:
   - `secure_core`, `silver_trainings`, `silver_marketing`, `silver_web`
   - `gold_trainings`, `gold_marketing`, `gold_web`
   - `dash_admin`, `dash_marketing`, `dash_board`, `dash_public` (or single `dash` with views)
4. Define IAM: Education Admin, Data Engineer, BI/Marketing, Public (least privilege per dataset).
5. Create `secure_core.secure_id_map` (learner_id, email_canonical, full_name_raw, etc.).
6. Create `dim_date` (e.g. in `gold_trainings` or shared) and audit tables:
   - `pipeline_run_log` (run_id, source, status, row_count, error_count, timestamp)
   - Rejects table templates: `silver_trainings.registrations_rejects`, `scores_rejects`, `ka_activity_rejects`, `feedback_rejects`.

**Repo**

7. Add `docs/` with:
   - `architecture.md` (high-level diagram and Medallion boundaries),
   - `runbook.md` (ingestion triggers, troubleshooting, pipeline_run_log usage).
8. Add `bq/sql/` skeleton:
   - `bq/sql/silver/` (DDL for Silver + rejects),
   - `bq/sql/gold/` (DDL for dim/fact + views).

**Deliverables**: GCS layout, BQ datasets, IAM, secure_core + audit tables, docs and `bq/sql` skeleton.

---

### Sprint 2 (Weeks 4–6): Trainings – Silver layer

**BigQuery DDL (`bq/sql/silver/`)**

1. **registrations**
   - Define table `silver_trainings.registrations` from Forms columns: registration_id, form_submission_id, full_name_raw, Email1, Highschool Name, Citizenship, Grade, GPA(4), commitment_per_week, linkedin_follow, cohort_name, field_selection, source_file, ingestion_time, schema_version.
   - Normalize email in ETL to produce `learner_id` (hash) and write PII to `secure_core.secure_id_map`; store only `learner_id` in registrations.
   - DDL for `registrations_rejects` (same columns + reject_reason).

2. **scores_raw**
   - Define `silver_trainings.scores_raw`: learner_identifier (name/username/email as received), cohort, field, quiz_score, quiz_pct, ka_score, learning_minutes (numeric), source_file, ingestion_time, row_hash.
   - Parsing: strip commas from numeric strings; reject unparseable rows to `scores_rejects` with reason (e.g. "numeric_parse_error", "duplicate", "incomplete").
   - DDL for `scores_rejects`.

3. **ka_activity**
   - Define `silver_trainings.ka_activity`: learner_identifier, provider_id, total_learning_minutes, skills_worked_on, skills_leveled_up, Attempted, Familiar, Proficient, Mastered, cohort_id or activity_period_start/end, source_file, ingestion_time.
   - DDL for `ka_activity_rejects`.

4. **feedback**
   - Define `silver_trainings.feedback`: feedback_id, learner_identifier, cohort_id, field_id, feedback_text, feedback_type, sentiment_label, sentiment_score, model_version, source_file, ingestion_time.
   - DDL for `feedback_rejects`.

**Cloud Functions (`functions/`)**

5. **Registrations**
   - `functions/registrations/`: GCS finalize trigger; read CSV/JSON; validate schema; normalize email → learner_id; upsert `secure_core.secure_id_map`; insert into `silver_trainings.registrations`; write bad rows to `registrations_rejects`; log to `pipeline_run_log`.

6. **Scores**
   - `functions/scores/`: GCS finalize trigger; read CSV; normalize numerics (strip commas); dedupe (row_hash / learner+cohort+field); insert into `scores_raw`; reject bad/duplicate rows to `scores_rejects`; log run.

7. **KA activity**
   - `functions/ka_activity/` (or combined with scores if same bucket): GCS trigger; parse; load into `ka_activity`; rejects and log.

8. **Feedback**
   - `functions/feedback/`: GCS trigger; load into `feedback`; for rows without sentiment call Cloud Natural Language API; write sentiment_label, sentiment_score, model_version; reject to `feedback_rejects`; log.

**Config and testing**

9. Add `requirements.txt` per function (e.g. google-cloud-bigquery, google-cloud-storage, google-cloud-language).
10. Use **`Datasets/trainings/`** (and **`Datasets/marketing/`**) CSVs/Excel as test payloads: upload to Bronze buckets and verify Silver rows and rejects. See **docs/schema.md** for exact paths.

**Deliverables**: Silver DDL, all four ingestion functions, rejects tables, pipeline_run_log usage, backfill test with existing CSVs.

---

### Sprint 3 (Weeks 7–9): Trainings – Gold layer & scoring

**BigQuery DDL (`bq/sql/gold/`)**

1. **Dimensions**
   - `gold_trainings.dim_learner` (learner_id, non-PII attributes; join to secure_core only for admins).
   - `gold_trainings.dim_cohort` (cohort_id, cohort_name, start_date, end_date, field_group).
   - `gold_trainings.dim_field` (field_id, field_name: Engineering, Software Engineering, Medicine, Law).
   - `gold_trainings.dim_institution` (from Highschool Name / registrations).
   - `gold_trainings.dim_learning_provider` (e.g. Khan Academy; future providers added here).
   - `gold_trainings.dim_date` (if not in shared location).

2. **Bridge**
   - `gold_trainings.bridge_learner_field` (learner_id, field_id, cohort_id, role, start_date, end_date) – support "Both" and multi-field.

3. **Facts**
   - `gold_trainings.fact_scores`: grain (learner_id, cohort_id, field_id) or per assessment; quiz scores, KA score, learning minutes, plus derived in views.
   - `gold_trainings.fact_engagement`: from ka_activity (minutes, skills, mastery levels).
   - `gold_trainings.fact_feedback`: feedback_id, learner_id, cohort_id, field_id, sentiment, model_version.

4. **Views (versioned)**
   - `gold_trainings.v_scores_v1`: relative % KA per (cohort_id, field_id) via PARTITION BY and MAX(); total points / engagement composite as in plan; no hard-coded denominators.
   - Optional: `v_engagement_v1` for engagement metrics.

5. **Population**
   - SQL scripts or scheduled queries to backfill Gold from Silver (all available history).
   - Partition fact tables by date; cluster by learner_id, field_id, cohort_id as appropriate.

**Deliverables**: Gold DDL, dim/fact/bridge tables, v_scores_v1 (and optional engagement view), backfill scripts, partitioning/clustering.

---

### Sprint 4 (Weeks 10–12): Marketing, web, BI

**Silver/Gold for marketing and web**

1. **YouTube**
   - Silver: table(s) for channel summary and/or top content (e.g. `silver_marketing.youtube_metrics_daily` or `_weekly`); UTC timestamps.
   - Gold: `dim_channel`, `dim_content`; `fact_marketing_reach` at daily/weekly grain.
   - Ingestion: weekly Cloud Function (CSV upload or YouTube Data API v3); write to Bronze then Silver.

2. **LinkedIn**
   - Silver: `silver_marketing.linkedin_metrics_daily` (or weekly) from `linkedin-cleaned.csv` schema; UTC.
   - Gold: same `fact_marketing_reach` or separate fact; join with dim_channel.
   - Ingestion: weekly CSV to Bronze → Function → Silver; later replace with LinkedIn Marketing API.

3. **Web**
   - Silver: `silver_web.analytics` (e.g. country, requests, date); Gold: `fact_web_traffic` (daily) joined to `dim_date`.

**Dashboard views and Looker Studio**

4. **dash_* views**
   - `dash_admin`: learner-level metrics (anonymized); optional authorized view joining to PII for admins only.
   - `dash_marketing`: campaign/channel metrics, no PII.
   - `dash_board`: high-level KPIs and trends.
   - `dash_public`: anonymized aggregates for website.

5. **Looker Studio**
   - Connect to `dash_*` views; build four dashboards (Admin, Marketing, Board, Public).
   - Document data sources and refresh cadence in `docs/`.

**Documentation and runbook**

6. Finalize `docs/architecture.md`, `docs/runbook.md`, and add `docs/data_dictionary.md` (table/column descriptions).
7. Optional: Pipeline Health dashboard (data freshness, last run status, error counts from `pipeline_run_log`).

**Deliverables**: Marketing/web Silver and Gold, ingestion for YouTube/LinkedIn/web, dash_* views, Looker dashboards, data dictionary, runbook updates.

---

## 3. File and folder creation checklist

Create the following in the repo (order matches sprints):

```
bq/
  sql/
    silver/
      ddl_secure_core.sql
      ddl_registrations.sql
      ddl_scores_raw.sql
      ddl_ka_activity.sql
      ddl_feedback.sql
      ddl_rejects.sql
    gold/
      ddl_dimensions.sql
      ddl_bridge.sql
      ddl_facts.sql
      views_v_scores_v1.sql
      backfill_*.sql
    marketing/
      ddl_silver_marketing.sql
      ddl_gold_marketing.sql
functions/
  registrations/
    main.py
    requirements.txt
  scores/
    main.py
    requirements.txt
  ka_activity/
    main.py
    requirements.txt
  feedback/
    main.py
    requirements.txt
  marketing_youtube/
    main.py
    requirements.txt
  marketing_linkedin/
    main.py
    requirements.txt
docs/
  architecture.md
  runbook.md
  data_dictionary.md
```

Optional: `infrastructure/` for Terraform or deployment scripts; `tests/` for unit/integration tests on parsers and schema validation.

---

## 4. Source schema notes (for DDL and parsers)

- **Registrations**: Unify `Engineering_Basics_Learner_Registration_clean_data.csv` and `Medicine_Basics_Learner_Registration_clean_data.csv` – same columns; add `cohort_name` and `field_selection` from form or filename.
- **Scores**: November sheet has Email, User name, "Both"; May sheet has different column names – support both via schema manifest or separate ingest paths and merge in Silver/Gold.
- **KA activity**: Single CSV schema; `student` can be username or name – map to learner_id in Gold via secure_id_map where possible.
- **Feedback**: Multiple forms (SessionFeedback, Anonymous_rating) with different column sets; normalize into common `feedback_text`, `feedback_type`, sentiment columns; store raw form identifier in metadata if needed.
- **LinkedIn**: One row per date; standardize column names (snake_case) and store all impression/click/engagement columns.
- **YouTube**: Summary is key-value; Top Content CSVs add content-level grain – decide daily vs weekly and channel vs content in Silver schema.
- **Web**: Country + requests; add ingestion date for time series.

---

## 5. Risk and mitigation (from plan §9)

- **Numeric parsing**: Implement comma stripping and store both raw string and parsed number; reject unparseable.
- **Duplicates**: Use row_hash and (learner, cohort, field) in scores; reject duplicates with reason.
- **Multi-field ("Both")**: Populate `bridge_learner_field`; never duplicate learner rows in facts without field_id.
- **Schema drift**: Maintain expected schema manifests per source; reject on mismatch and log.
- **Cost**: Partition and cluster large tables; use weekly aggregation for marketing where appropriate; incremental loads by last_run_timestamp.

---

## 6. How to use this implementation plan

- **Start with Sprint 1**: Create GCP resources and repo skeleton before writing ingestion code.
- **Use Datasets as truth**: When writing DDL and parsers, align with the actual CSV headers and sample rows listed in §1.2.
- **Keep ETL plan as master**: For identity, PII, scoring formulas, and governance, always refer to **Ethioware-ETL-Plan.md** and the **.cursor** rules/skill.
- **Implement in order**: Silver tables and functions (Sprint 2) before Gold (Sprint 3); Gold and scoring before dashboards (Sprint 4).
