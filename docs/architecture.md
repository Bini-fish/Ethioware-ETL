# Ethioware – Architecture (high-level)

**Project:** `ethioware-etl`  
**BigQuery location:** `us-central1` (Iowa) – datasets and queries run here  
**GCS (Bronze):** US multi-region – main buckets use US multi-region

---

## Medallion flow

```
Bronze (GCS)          Silver (BigQuery)              Gold (BigQuery)           Dashboards
────────────          ─────────────────             ─────────────────         ──────────
raw files             standardized tables            dim/fact/views            Looker Studio
                      + rejects                      + scoring views            (dash_* views)
```

- **Bronze:** As close to source as possible; no renames or type coercion beyond what’s needed to load.
- **Silver:** Stable schemas; Cloud Functions do light ETL (validation, parse, load) and write bad rows to `_rejects`; log runs to `pipeline_run_log`.
- **Gold:** SQL only (no ETL in Cloud Functions); dim/fact modeling; versioned scoring views (e.g. `v_scores_v1`).

---

## GCS (Bronze) layout

| Bucket | Prefixes | Purpose |
|--------|----------|---------|
| `ethioware-bronze-trainings` | `forms/`, `scores/`, `feedback/` | Microsoft Form exports, score sheets, feedback CSVs/Excel |
| `ethioware-bronze-marketing` | `youtube/`, `linkedin/` | YouTube and LinkedIn exports |
| `ethioware-bronze-web` | `analytics/` | Web analytics (e.g. by country) |

Uploads trigger Cloud Functions (GCS finalize). Prefix determines which pipeline runs.

---

## BigQuery datasets

| Dataset | Contents |
|---------|----------|
| `secure_core` | `secure_id_map` (learner_id ↔ email/name); PII only; restricted access |
| `silver_trainings` | `registrations`, `scores_raw`, `ka_activity`, `feedback`, `*_rejects`, `pipeline_run_log` |
| `silver_marketing` | LinkedIn, YouTube tables (Sprint 4) |
| `silver_web` | Web analytics (Sprint 4) |
| `gold_trainings` | `dim_date`, `dim_learner`, `dim_cohort`, `dim_field`, `dim_institution`, `bridge_learner_field`, `fact_scores`, `fact_engagement`, `fact_feedback`, `v_scores_v1` |
| `gold_marketing` | Marketing facts and dims (Sprint 4) |
| `gold_web` | Web traffic facts (Sprint 4) |
| `dash_admin`, `dash_marketing`, `dash_board`, `dash_public` | Views for each dashboard layer; no PII except via authorized view for admins |

---

## Identity and PII

- **learner_id** = SHA-256(lower(trim(email_canonical))). Stable algorithm; do not change without a migration plan.
- PII lives only in `secure_core.secure_id_map`. Silver/Gold/dash store only `learner_id` (or anonymized aggregates).
- Education Admins: can join to `secure_id_map` for PII; other roles use anonymized data only.

---

## Repo layout (DDL and code)

- **`bq/sql/silver/`** – DDL for Silver tables and rejects (`ddl_secure_core.sql`, `ddl_audit.sql`, `ddl_rejects.sql`, then `ddl_registrations.sql`, etc.).
- **`bq/sql/gold/`** – DDL for Gold (`ddl_dim_date.sql`, `ddl_dimensions.sql`, `ddl_facts.sql`, `views_v_scores_v1.sql`, backfill scripts).
- **`functions/`** – Cloud Functions per source (registrations, scores, ka_activity, feedback; later marketing, web).

See **docs/IMPLEMENTATION-PLAN.md** for the full file checklist and sprint order.
