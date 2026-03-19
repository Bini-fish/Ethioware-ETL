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

**After Sprint 2:** Also run DDL for and verify `silver_trainings.registrations`, `silver_trainings.scores_raw`, `silver_trainings.ka_activity`, and `silver_trainings.feedback` (see “Running the DDL scripts” below).

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

**Routing guardrails (current behavior):**
- `scores` skips non-score files (e.g. filenames containing `learner_activity`, `khan`, `ka_activity`, `all_assignments`) and logs status `SKIPPED`.
- `scores` and `ka_activity` both apply lightweight schema checks; if a file lands in the wrong function it is logged as `SKIPPED` rather than generating bulk rejects.

---

## pipeline_run_log

Every ingestion run writes one row to **`silver_trainings.pipeline_run_log`** (all domains use this table; identify by `source`).

| Column | Meaning |
|--------|---------|
| `run_id` | Unique run identifier (e.g. UUID or bucket+path+timestamp) |
| `source` | e.g. `ethioware-bronze-trainings/forms/`, `registrations`, `scores` |
| `status` | `SUCCESS`, `PARTIAL`, `FAILED`, `SKIPPED` |
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

4. **File routed to wrong function**  
   - Check `pipeline_run_log` for `status = 'SKIPPED'` and inspect `message` (`unsupported_*_schema` or route message).  
   - This indicates the file reached a function that intentionally skipped it (expected for mixed prefixes).

5. **PII / learner_id**  
   - Only `secure_core.secure_id_map` holds email/name; Silver/Gold use only `learner_id`. If joins break, confirm `learner_id` is written on insert and that hash algorithm matches (SHA-256 of normalized email).

6. **Schema drift**  
   - If a form or export changes columns, the function may reject rows. Update the expected schema in code and, if needed, add a new schema_version; backfill rejects after fixing.

7. **Function appears to never trigger (no logs at all)**  
   This was the root cause of a multi-day debugging effort on `ethioware-registrations`. Two compounding issues:

   **a) Per-row BigQuery MERGE timeout:**  
   The original `_upsert_secure_id_map` ran one BigQuery `MERGE` per unique learner (~3.5 seconds each). A 258-learner CSV required ~903 seconds, exceeding both the 60-second default and 540-second extended timeouts. The function was killed mid-execution.

   **b) Python stdout buffering hid the evidence:**  
   In Cloud Run containers, Python `print()` uses full buffering (not line buffering). When the function was killed by the timeout, the entire stdout buffer was lost — making it appear as if the function was never invoked at all.

   **Fix applied:**
   - Replaced per-row MERGE with batched `UNNEST(ARRAY<STRUCT<...>>)` MERGE (100 learners per batch). 258 learners now completes in ~8 seconds instead of ~903 seconds.
   - All `print()` calls in Cloud Functions now use `flush=True` so logs appear immediately in Cloud Logging, even if the function is killed.

   **Prevention rules:**
   - **Always use `flush=True`** on `print()` in Cloud Functions. Without it, logs may be silently lost on timeout or crash.
   - **Never do per-row BigQuery DML** (MERGE, INSERT, UPDATE) in a loop. Always batch using `UNNEST`, temp tables, or `insert_rows_json`.
   - **Set `--timeout=540s`** on functions that process large files (the default 60s is too low).
   - **Check Cloud Run request logs** (`logName:run.googleapis.com%2Frequests`) for `latency` and `status` when diagnosing trigger issues — these are always present even when user-code logs are missing.

---

## Running the DDL scripts

From the repo root, with `bq` CLI and project set:

```bash
# Core (pre–Sprint 2)
bq query --use_legacy_sql=false < bq/sql/silver/ddl_secure_core.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_audit.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_rejects.sql
bq query --use_legacy_sql=false < bq/sql/gold/ddl_dim_date.sql

# Silver Trainings (Sprint 2)
bq query --use_legacy_sql=false < bq/sql/silver/ddl_registrations.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_scores_raw.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_ka_activity.sql
bq query --use_legacy_sql=false < bq/sql/silver/ddl_feedback.sql
```

Or run each file in the BigQuery console (copy-paste). Replace `ethioware-etl` in the SQL with your project ID if different.

---

## Testing ingestion locally (before deploy)

You can run the same Cloud Function logic on your machine against **local files** (no GCS) and **real BigQuery**. Use this to validate files and logic before deploying.

**1. Install dependencies for the function you’re testing** (from repo root):

```bash
# For registrations (Excel)
pip install -r functions/registrations/requirements.txt

# For scores or ka_activity (CSV)
pip install -r functions/scores/requirements.txt
# or: pip install -r functions/ka_activity/requirements.txt

# For feedback (Excel + optional NLP)
pip install -r functions/feedback/requirements.txt
```

Or install all at once:  
`pip install -r functions/registrations/requirements.txt -r functions/scores/requirements.txt -r functions/ka_activity/requirements.txt -r functions/feedback/requirements.txt`

**2. Set GCP credentials** (so BigQuery and, if used, GCS work):

```bash
gcloud auth application-default login
# Optional: set project
export GCP_PROJECT=ethioware-etl
```

**3. Run with a local file** (reads from disk; writes to BigQuery):

```bash
# From repo root
python scripts/run_local.py registrations --local path/to/registration.xlsx
python scripts/run_local.py scores       --local path/to/scores.csv
python scripts/run_local.py ka_activity   --local path/to/learner_activity.csv
python scripts/run_local.py feedback      --local path/to/Session_Feedback_Form.xlsx
```

Use **`--dry-run`** to skip BigQuery writes and only validate read/parse/transform (no GCP credentials needed):

```bash
python scripts/run_local.py scores --local path/to/scores.csv --dry-run
```

**4. Or run against a real GCS object**:

```bash
python scripts/run_local.py registrations --gcs gs://ethioware-bronze-trainings/forms/MyExport.xlsx
```

The script builds a GCS-like event and calls the function’s `main(event, context)`. When `--local` is used, the event includes `local_path` so the function reads from that file instead of GCS. BigQuery inserts/rejects and `pipeline_run_log` are real. After a run, check `pipeline_run_log` and the Silver tables (or rejects) in BigQuery.

---

## Deploying Cloud Functions (Sprint 2 – Trainings)

**Prerequisites**

- APIs enabled: `run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com`, `eventarc.googleapis.com`
- Bucket `ethioware-bronze-trainings` is in multi-region **`us`** (trigger location must match bucket location).
- GCS → Eventarc: grant **Pub/Sub Publisher** to the GCS service agent on the project:
  ```bash
  # Get GCS service agent (format: service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com)
  gcloud projects add-iam-policy-binding ethioware-etl \
    --member="serviceAccount:service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"
  ```
- Optional: grant **Storage Object Viewer** on the bucket to the default compute service account so Eventarc can validate the bucket.

From the repo root, with `gcloud` and project `ethioware-etl`:

**Gen2 uses Eventarc:** use `--trigger-location` and `--trigger-event-filters` only (do **not** use `--trigger-bucket`).

```bash
# Registrations: forms/*.xlsx or *.csv (function filters by name.startswith("forms/"))
gcloud functions deploy ethioware-registrations \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=functions/registrations --entry-point=cf_main \
  --trigger-location=us \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ethioware-bronze-trainings" \
  --set-env-vars=GCP_PROJECT=ethioware-etl \
  --memory=512MiB --timeout=540s --project=ethioware-etl

# Scores: scores/*.csv
gcloud functions deploy ethioware-scores \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=functions/scores --entry-point=main \
  --trigger-location=us \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ethioware-bronze-trainings" \
  --set-env-vars=GCP_PROJECT=ethioware-etl \
  --memory=512MB --project=ethioware-etl

# KA activity: scores/*.csv with "learner_activity" or "khan" in filename
gcloud functions deploy ethioware-ka-activity \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=functions/ka_activity --entry-point=main \
  --trigger-location=us \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ethioware-bronze-trainings" \
  --set-env-vars=GCP_PROJECT=ethioware-etl \
  --memory=512MB --project=ethioware-etl

# Feedback: feedback/*
gcloud functions deploy ethioware-feedback \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=functions/feedback --entry-point=main \
  --trigger-location=us \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ethioware-bronze-trainings" \
  --set-env-vars=GCP_PROJECT=ethioware-etl \
  --memory=512MB --project=ethioware-etl
```

**Note:** All four triggers listen to the same bucket; each function filters by object name (forms/, scores/, feedback/ or filename). For optional sentiment on feedback, set `--set-env-vars=GCP_PROJECT=ethioware-etl,USE_NLP_SENTIMENT=true` and grant the function’s service account `roles/cloudnaturallanguage.viewer`.

---

## Checking if an upload worked

After uploading a file to Bronze (e.g. `gs://ethioware-bronze-trainings/forms/YourFile.xlsx`), verify the pipeline ran and wrote data.

### 1. Pipeline run log

In BigQuery, run:

```sql
SELECT run_id, source, status, row_count, error_count, message, timestamp
FROM `ethioware-etl.silver_trainings.pipeline_run_log`
ORDER BY timestamp DESC
LIMIT 10;
```

Look for a row where:
- **source** is the GCS path of your file (e.g. `gs://ethioware-bronze-trainings/forms/Enginerring_Basics_Registration...xlsx`).
- **status** is `SUCCESS` (or `PARTIAL` if some rows were rejected).
- **row_count** is the number of rows inserted.

### 2. Silver table

- **Registrations:**  
  `SELECT COUNT(*) FROM \`ethioware-etl.silver_trainings.registrations\`;`  
  and  
  `SELECT * FROM \`ethioware-etl.silver_trainings.registrations\` ORDER BY ingestion_time DESC LIMIT 10;`
- **Scores:**  
  `SELECT * FROM \`ethioware-etl.silver_trainings.scores_raw\` ORDER BY ingestion_time DESC LIMIT 10;`
- **Feedback:**  
  `SELECT * FROM \`ethioware-etl.silver_trainings.feedback\` ORDER BY ingestion_time DESC LIMIT 10;`

### 3. Rejects (if status was PARTIAL or FAILED)

```sql
SELECT source_file, reject_reason, ingestion_time
FROM `ethioware-etl.silver_trainings.registrations_rejects`
ORDER BY ingestion_time DESC
LIMIT 10;
```

### 4. Cloud Logging (if no log row or errors)

In Cloud Console: **Logging → Logs Explorer**. Filter by:

- Resource type: **Cloud Run Revision**
- Resource labels: **service_name** = `ethioware-registrations` (or `ethioware-scores`, etc.)

Search for your filename or errors. If the function was never invoked, check that the object name matches what the function expects (e.g. under `forms/` for registrations).
