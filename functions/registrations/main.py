"""
Ethioware – Registrations ingestion.
Trigger  : GCS finalize on ethioware-bronze-trainings/forms/
Supports : CSV and Excel (Microsoft Forms export) with these columns –
           Id, Start time, Completion time, Email, Full Name, Email1,
           Highschool Name, Citizenship, commitment_per_week, Grade,
           GPA (100 or 4.0)? / GPA (100)?, Telegram user name,
           Where did you hear…, Do you follow us: …linkedin…
Output   : secure_core.secure_id_map  (PII – learner_id ↔ email/name)
           silver_trainings.registrations  (no PII – learner_id only)
           silver_trainings.registrations_rejects  (bad rows)
           silver_trainings.pipeline_run_log        (audit)
"""

import hashlib
import io
import json
import os
import re
import time
from datetime import datetime, timezone

import functions_framework
import pandas as pd
from cloudevents.http import CloudEvent
from google.api_core import exceptions as gapi_exceptions
from google.cloud import bigquery, storage

PROJECT_ID   = os.environ.get("GCP_PROJECT", "ethioware-etl")
# Set FORMS_PREFIX="" in the function env to accept files from any bucket path.
# Default "forms/" scopes the function to the registrations subfolder only.
FORMS_PREFIX = os.environ.get("FORMS_PREFIX", "forms/")

# Lazy client – avoids credential errors during cold-start module load.
_BQ: bigquery.Client | None = None


def _get_bq() -> bigquery.Client:
    global _BQ
    if _BQ is None:
        _BQ = bigquery.Client(project=PROJECT_ID)
    return _BQ


# ── Where-heard normalisation ──────────────────────────────────────────────
WHERE_HEARD_MAP = {
    "telegram":     "social_media",
    "social":       "social_media",
    "facebook":     "social_media",
    "instagram":    "social_media",
    "linkedin":     "social_media",
    "twitter":      "social_media",
    "youtube":      "social_media",
    "friend":       "word_of_mouth",
    "word of mouth": "word_of_mouth",
    "colleague":    "word_of_mouth",
    "school":       "word_of_mouth",
    "teacher":      "word_of_mouth",
    "referred":     "word_of_mouth",
    "family":       "word_of_mouth",
}


# ── Pure helpers ───────────────────────────────────────────────────────────

def _learner_id(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _where_heard_category(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        return "other"
    lower = raw.strip().lower()
    for phrase, cat in WHERE_HEARD_MAP.items():
        if phrase in lower:
            return cat
    return "other"


def _program_from_filename(name: str) -> str:
    """Derive canonical program code from GCS object path."""
    base = os.path.basename(name)
    for ext in (".xlsx", ".xls", ".csv"):
        base = base.replace(ext, "")
    norm = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")

    if "engineering" in norm and "basics" in norm:
        return "Engineering_Basics"
    if "medicine" in norm and "basics" in norm:
        return "Medicine_Basics"
    # "se_basics" OR "software engineering/basics"
    if ("se" in norm.split("_") and "basics" in norm) or \
       ("software" in norm and ("engineering" in norm or "basics" in norm)):
        return "SE_Basics"
    if "law" in norm and "basics" in norm:
        return "Law_Basics"
    return "Other"


def _cohort_from_start_times(series) -> str | None:
    """Return YYYY-MM of the earliest Start time in the dataset."""
    if series is None:
        return None
    try:
        ts = pd.to_datetime(series, errors="coerce")
        min_ts = ts.min()
        if pd.isna(min_ts):
            return None
        return f"{min_ts.year}-{min_ts.month:02d}"
    except Exception:
        return None


def _parse_gpa(val) -> float | None:
    """Normalize GPA to 4.0 scale.
    Accepts 100-scale integers, 4.0-scale floats, ranges like '3.2-3.9'
    (lower bound taken), and percent strings like '80%'.
    Strings like 'Above average' return None.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (int, float)):
        v = float(val)
        return round((v / 100) * 4, 2) if v > 10 else round(v, 2)
    s = str(val).strip().replace(",", ".").replace("%", "")
    # Extract leading numeric token (handles "3.2-3.9", "80%", "3.52")
    m = re.match(r"^(\d+\.?\d*)", s)
    if not m:
        return None
    try:
        f = float(m.group(1))
        return round((f / 100) * 4, 2) if f > 10 else round(f, 2)
    except ValueError:
        return None


def _parse_ts(v) -> str | None:
    """Return UTC ISO-8601 string (YYYY-MM-DDTHH:MM:SSZ) for BigQuery TIMESTAMP."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dt = pd.to_datetime(v)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _str(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s[:10_000] if s else None


def _col(df: pd.DataFrame, *candidates: str) -> str | None:
    """Return the first column name that matches any candidate (case-insensitive)."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        found = lower_map.get(cand.lower())
        if found is not None:
            return found
    return None


# ── Core ingestion logic ───────────────────────────────────────────────────

def _handle_event_dict(obj: dict):
    """
    obj must contain 'bucket' and 'name' (GCS storage event payload).
    Optionally 'local_path' for local test runs.
    """
    bucket = obj.get("bucket") or ""
    name   = (obj.get("name") or "").strip()
    print(f"[registrations] Processing bucket={bucket!r} name={name!r}", flush=True)
    run_id_probe = f"{name or 'no-name'}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    if FORMS_PREFIX and not name.startswith(FORMS_PREFIX):
        print(f"[registrations] Skipping path outside prefix {FORMS_PREFIX!r}: {name!r}", flush=True)
        return
    if not (name.endswith(".xlsx") or name.endswith(".xls") or name.endswith(".csv")):
        print(f"[registrations] Skipping unsupported extension: {name!r}", flush=True)
        return

    source_file = f"gs://{bucket}/{name}"
    run_id      = run_id_probe
    now_utc     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bq          = _get_bq()

    # ── Idempotency check ─────────────────────────────────────────────────
    try:
        rows = list(bq.query(
            f"SELECT COUNT(1) AS n FROM `{PROJECT_ID}.silver_trainings.pipeline_run_log` "
            f"WHERE source = @src AND status = 'SUCCESS'",
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("src", "STRING", source_file)
            ]),
        ).result())
        if rows and rows[0].n > 0:
            print(f"[registrations] Already processed {source_file} – skipping.", flush=True)
            return
    except Exception as e:
        print(f"[registrations] Idempotency check failed (proceeding): {e}", flush=True)

    # ── Download ──────────────────────────────────────────────────────────
    local_path = obj.get("local_path")
    try:
        if local_path and os.path.isfile(local_path):
            with open(local_path, "rb") as fh:
                content = fh.read()
        else:
            gcs     = storage.Client(project=PROJECT_ID)
            content = gcs.bucket(bucket).blob(name).download_as_bytes()
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, f"download_error: {e}")
        raise

    # ── Parse ─────────────────────────────────────────────────────────────
    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        else:
            df = pd.read_csv(io.StringIO(content.decode("utf-8", errors="replace")))
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, f"parse_error: {e}")
        _reject(source_file, "parse_error", json.dumps({"error": str(e)}))
        return

    # Normalise column names (strip whitespace / non-breaking spaces)
    df.columns = [str(c).strip().replace("\xa0", " ") for c in df.columns]

    # ── Resolve flexible columns ──────────────────────────────────────────
    email_col = _col(df, "Email1", "Email2", "Email Address", "Email")
    if not email_col:
        _log_run(run_id, source_file, "FAILED", 0, len(df), "missing_email_column")
        return

    id_col      = _col(df, "Id", "ID", "id")
    gpa_col     = _col(df, "GPA (100 or 4.0)?", "GPA (100)?", "GPA")
    linkedin_col = next((c for c in df.columns if "linkedin" in c.lower()), None)

    program_selection = _program_from_filename(name)
    cohort_name       = _cohort_from_start_times(df.get("Start time")) or "Unknown"

    rows_reg:    list[dict] = []
    rows_secure: list[dict] = []
    rejected = 0

    for idx, row in df.iterrows():
        email_raw = row.get(email_col)
        if email_raw is None or (isinstance(email_raw, float) and pd.isna(email_raw)) \
                or not str(email_raw).strip():
            _reject(source_file, "invalid_email", row.to_json())
            rejected += 1
            continue

        email_clean = str(email_raw).strip().lower()
        lid         = _learner_id(email_clean)
        full_name   = _str(row.get("Full Name")) or ""

        # Stable, cross-file unique registration_id:  Program_Cohort_FormRowId
        form_id         = str(row[id_col]).strip() if id_col else str(idx)
        registration_id = f"{program_selection}_{cohort_name}_{form_id}"

        rows_secure.append({
            "learner_id":     lid,
            "email_canonical": email_clean,
            "full_name_raw":  full_name,
            "source_file":    source_file,
        })

        where_raw    = _str(row.get("Where did you hear about this program?")) or ""
        linkedin_val = None
        if linkedin_col:
            lv = _str(row.get(linkedin_col))
            linkedin_val = lv[:10] if lv else None

        rows_reg.append({
            "registration_id":     registration_id,
            "learner_id":          lid,
            "start_time":          _parse_ts(row.get("Start time")),
            "completion_time":     _parse_ts(row.get("Completion time")),
            "last_modified_time":  _parse_ts(row.get("Last modified time")),
            "highschool_name":     _str(row.get("Highschool Name")),
            "citizenship":         _str(row.get("Citizenship")),
            "commitment_per_week": _str(row.get("How much time do you plan to commit per week?")),
            "grade":               _str(row.get("Grade")),
            "gpa_4_scale":         _parse_gpa(row.get(gpa_col) if gpa_col else None),
            "telegram_username":   _str(row.get("Telegram user name (@your user name)?")),
            "where_heard_category": _where_heard_category(where_raw),
            "linkedin_follow":     linkedin_val,
            "program_selection":   program_selection,
            "cohort_name":         cohort_name,
            "source_file":         source_file,
            "ingestion_time":      now_utc,
            "schema_version":      "v1",
        })

    # ── Upsert PII into secure_id_map (dedup by learner_id) ───────────────
    seen_ids: set[str] = set()
    unique_secure = [r for r in rows_secure if r["learner_id"] not in seen_ids and not seen_ids.add(r["learner_id"])]
    _t0 = time.time()
    _batch_upsert_secure_id_map(unique_secure)
    print(f"[registrations] secure_id_map: {len(unique_secure)} learners merged in {time.time()-_t0:.1f}s", flush=True)

    # ── Stream rows into silver_trainings.registrations ───────────────────
    bq_errors: list[str] = []
    if rows_reg:
        try:
            errs = bq.insert_rows_json(
                f"{PROJECT_ID}.silver_trainings.registrations",
                rows_reg,
            )
            if errs:
                rejected += len(errs)
                bq_errors.extend(str(e) for e in errs)
        except Exception as e:
            bq_errors.append(str(e))

    status = "FAILED" if bq_errors else ("PARTIAL" if rejected else "SUCCESS")
    _log_run(
        run_id, source_file, status,
        len(rows_reg) - len(bq_errors), rejected,
        "; ".join(bq_errors) if bq_errors else None,
    )
    print(f"[registrations] Done: status={status} rows={len(rows_reg)} rejected={rejected}", flush=True)


# ── Cloud Functions entry points ───────────────────────────────────────────

@functions_framework.cloud_event
def cf_main(cloud_event: CloudEvent):
    """Gen2 Eventarc/GCS entry point – deployed with --entry-point=cf_main."""
    data = cloud_event.data or {}
    if isinstance(data, dict):
        _handle_event_dict(data)


def main(event, context=None):
    """Local runner / legacy compatibility entry point."""
    if isinstance(event, dict):
        _handle_event_dict(event)


# ── BigQuery helpers ───────────────────────────────────────────────────────

def _escape_bq(s: str) -> str:
    """Escape single quotes for BigQuery string literals."""
    return s.replace("'", "\\'") if s else ""


def _batch_upsert_secure_id_map(rows: list[dict]):
    """Upsert learners into secure_id_map in batches of BATCH_SIZE using
    a single MERGE per batch with UNNEST(ARRAY<STRUCT<...>>).
    ~258 learners now takes ~15s instead of ~900s.
    """
    if not rows:
        return
    bq = _get_bq()
    BATCH_SIZE = 100

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        values = ", ".join(
            f"('{r['learner_id']}', "
            f"'{_escape_bq(r['email_canonical'])}', "
            f"'{_escape_bq(r['full_name_raw'])}', "
            f"'{_escape_bq(r['source_file'])}')"
            for r in batch
        )
        sql = f"""
        MERGE `{PROJECT_ID}.secure_core.secure_id_map` T
        USING (
          SELECT * FROM UNNEST(
            ARRAY<STRUCT<learner_id STRING, email_canonical STRING,
                         full_name_raw STRING, source_file STRING>>[
              {values}
            ]
          )
        ) S ON T.learner_id = S.learner_id
        WHEN MATCHED THEN UPDATE SET
          full_name_raw = S.full_name_raw,
          updated_at    = CURRENT_TIMESTAMP(),
          source_file   = S.source_file
        WHEN NOT MATCHED THEN INSERT
          (learner_id, email_canonical, full_name_raw, created_at, updated_at, source_file)
        VALUES
          (S.learner_id, S.email_canonical, S.full_name_raw,
           CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), S.source_file)
        """
        delay = 0.5
        for attempt in range(1, 6):
            try:
                bq.query(sql).result()
                break
            except gapi_exceptions.GoogleAPICallError as exc:
                if "Could not serialize access to table" not in str(exc) or attempt == 5:
                    raise
                time.sleep(delay)
                delay *= 2.0


def _reject(source_file: str, reason: str, raw_row: str):
    bq  = _get_bq()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bq.insert_rows_json(
        f"{PROJECT_ID}.silver_trainings.registrations_rejects",
        [{"source_file":    source_file,
          "ingestion_time": now,
          "reject_reason":  reason,
          "raw_row":        raw_row[:100_000]}],
    )


def _log_run(run_id: str, source: str, status: str,
             row_count: int, error_count: int, message: str = None):
    bq  = _get_bq()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bq.insert_rows_json(
        f"{PROJECT_ID}.silver_trainings.pipeline_run_log",
        [{"run_id":       run_id,
          "source":       source,
          "status":       status,
          "row_count":    row_count,
          "error_count":  error_count,
          "message":      message,
          "timestamp":    now}],
    )
