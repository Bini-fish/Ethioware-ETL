# Ethioware – Runbook (ingestion and troubleshooting)

Use this when operating the pipeline: where data lands, how runs are triggered, and how to check health.

---

## Pre–Sprint 2 verification (foundation check)

Run these **before starting Sprint 2** to confirm everything so far works.

### 1. BigQuery – tables exist and are queryable

In BigQuery (Console or `bq`), run:

```sql
-- Should return 7 rows (one per table). Empty tables return cnt = 0.
SELECT 'secure_core.secure_id_map' AS tbl, COUNT(*) AS cnt FROM `ethioware-etl.secure_core.secure_id_map`
UNION ALL SELECT 'silver_trainings.pipeline_run_log', COUNT(*) FROM `ethioware-etl.silver_trainings.pipeline_run_log`
UNION ALL SELECT 'silver_trainings.registrations_rejects', COUNT(*) FROM `ethioware-etl.silver_trainings.registrations_rejects`
UNION ALL SELECT 'silver_trainings.scores_rejects', COUNT(*) FROM `ethioware-etl.silver_trainings.scores_rejects`
UNION ALL SELECT 'silver_trainings.ka_activity_rejects', COUNT(*) FROM `ethioware-etl.silver_trainings.ka_activity_rejects`
UNION ALL SELECT 'silver_trainings.feedback_rejects', COUNT(*) FROM `ethioware-etl.silver_trainings.feedback_rejects`
UNION ALL SELECT 'gold_trainings.dim_date', COUNT(*) FROM `ethioware-etl.gold_trainings.dim_date`
ORDER BY tbl;
```

Or check in the BigQuery Explorer: all of the above tables should be listed under their datasets. Empty tables are fine.

### 2. GCS – buckets and prefixes

In Cloud Shell or `gsutil`:

```bash
gsutil ls gs://ethioware-bronze-trainings/
gsutil ls gs://ethioware-bronze-marketing/
gsutil ls gs://ethioware-bronze-web/
```

You should see the buckets (and optionally prefixes like `forms/`, `scores/`, etc. after an upload). As Data Engineer you should be able to list and upload.

### 3. IAM – role access

- **Data Engineer:** In BigQuery, run any query (e.g. `SELECT 1`) and confirm you can see all datasets and run jobs.
- **Education Admin:** Log in as that principal (or ask them to). In BigQuery they should see only `secure_core`, `silver_trainings`, `gold_trainings`, `dash_admin`. They should **not** see `silver_marketing`, `gold_marketing`, etc.
- **BI/Marketing:** Log in as that principal. They should see only `silver_marketing`, `gold_marketing`, `dash_marketing`, `dash_board`.

### 4. Docs and repo

- `docs/architecture.md` – project ID, locations, dataset list match your GCP setup.
- `docs/iam.md` – role-to-dataset mapping (§0) matches the roles you created.
- `bq/sql/silver/` and `bq/sql/gold/` – DDL files present and reference `ethioware-etl`.

If all of the above pass, you’re ready for Sprint 2 (Silver tables + Cloud Functions).

---

## Ingestion triggers

| Source | Bronze location | Trigger | Silver target |
|--------|------------------|---------|---------------|
| Registration (Microsoft Form export) | `gs://ethioware-bronze-trainings/forms/<file>.xlsx` | GCS finalize → Cloud Function **registrations** | `silver_trainings.registrations`; PII → `secure_core.secure_id_map` |
| Score sheets (CSV) | `gs://ethioware-bronze-trainings/scores/<file>.csv` | GCS finalize → Cloud Function **scores** | `silver_trainings.scores_raw` |
| KA activity (CSV) | `gs://ethioware-bronze-trainings/scores/` or dedicated prefix | GCS finalize → Cloud Function **ka_activity** | `silver_trainings.ka_activity` |
| Feedback (Excel/CSV) | `gs://ethioware-bronze-trainings/feedback/<file>` | GCS finalize → Cloud Function **feedback** | `silver_trainings.feedback` |
| YouTube / LinkedIn | `gs://ethioware-bronze-marketing/youtube/`, `linkedin/` | GCS finalize (or scheduled) → marketing functions | `silver_marketing.*` |
| Web analytics | `gs://ethioware-bronze-web/analytics/` | GCS finalize → web function | `silver_web.analytics` |

**Idempotency:** Functions should handle re-uploads (e.g. dedupe by row_hash or source_file + batch_id) so re-running the same file doesn’t double-count.

---

## pipeline_run_log

Every ingestion run writes one row to **`silver_trainings.pipeline_run_log`** (all domains use this table; identify by `source`).

| Column | Meaning |
|--------|---------|
| `run_id` | Unique run identifier (e.g. UUID or bucket+path+timestamp) |
| `source` | e.g. `ethioware-bronze-trainings/forms/`, `registrations`, `scores` |
| `status` | `SUCCESS`, `PARTIAL`, `FAILED` |
| `row_count` | Rows inserted into Silver |
| `error_count` | Rows written to the corresponding `_rejects` table |
| `message` | Optional error or summary text |
| `timestamp` | When the run finished |

**Useful queries:**

- Last run per source:  
  `SELECT * FROM \`ethioware-etl.silver_trainings.pipeline_run_log\` WHERE source = 'registrations' ORDER BY timestamp DESC LIMIT 1`
- Failed runs:  
  `SELECT * FROM ... WHERE status = 'FAILED' ORDER BY timestamp DESC`
- Data freshness:  
  Check `MAX(timestamp)` per `source` to see when each pipeline last ran.

---

## Rejects tables

Bad rows (schema mismatch, parse error, duplicate, etc.) go to the matching **`*_rejects`** table in the same dataset:

- `silver_trainings.registrations_rejects`
- `silver_trainings.scores_rejects`
- `silver_trainings.ka_activity_rejects`
- `silver_trainings.feedback_rejects`

Each has `reject_reason`, `source_file`, `ingestion_time`, and optionally `raw_row` (JSON) for debugging. Query by `source_file` or `reject_reason` to find patterns.

---

## Troubleshooting

1. **No rows in Silver after upload**  
   - Check `pipeline_run_log` for that source: status and `message`.  
   - Check Cloud Function logs (Logging → filter by function name).  
   - Check the corresponding `*_rejects` table for the same `source_file`; `reject_reason` explains why rows were rejected.

2. **Duplicate rows**  
   - Ensure dedupe logic (e.g. row_hash or learner+cohort+field) is in place in the Cloud Function.  
   - Check if the same file was uploaded multiple times; idempotency should prevent double-counting.

3. **Numeric parse errors (scores)**  
   - Strip commas in Learning Minutes (e.g. `2,561.00` → 2561.00) before casting; unparseable → `scores_rejects` with reason `numeric_parse_error`.

4. **PII / learner_id**  
   - Only `secure_core.secure_id_map` holds email/name; Silver/Gold use only `learner_id`. If joins break, confirm `learner_id` is written on insert and that hash algorithm matches (SHA-256 of normalized email).

5. **Schema drift**  
   - If a form or export changes columns, the function may reject rows. Update the expected schema in code and, if needed, add a new schema_version; backfill rejects after fixing.

---

## Running the DDL scripts

From the repo root, with `bq` CLI and project set:

```bash
bq query --use_legacy_sql=false < bq/sql/silver/ddl_secure_core.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_audit.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_rejects.sql
bq query --use_legacy_sql=false < bq/sql/gold/ddl_dim_date.sql
```

Or run each file in the BigQuery console (copy-paste). Replace `ethioware-etl` in the SQL with your project ID if different.
