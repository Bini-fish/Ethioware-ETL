"""
Ethioware – Registrations ingestion.
Trigger: GCS finalize on ethioware-bronze-trainings/forms/*.xlsx
Reads Microsoft Form Excel export, normalizes email → learner_id, upserts secure_id_map, inserts silver_trainings.registrations.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery, storage

PROJECT_ID = os.environ.get("GCP_PROJECT", "ethioware-etl")
BQ = bigquery.Client(project=PROJECT_ID)

# Where-heard free text → category (add phrases as needed)
WHERE_HEARD_MAP = {
    "social": "social_media",
    "facebook": "social_media",
    "instagram": "social_media",
    "linkedin": "social_media",
    "twitter": "social_media",
    "friend": "word_of_mouth",
    "word of mouth": "word_of_mouth",
    "colleague": "word_of_mouth",
    "school": "word_of_mouth",
    "teacher": "word_of_mouth",
}


def _learner_id(email: str) -> str:
    if not email or not isinstance(email, str):
        return ""
    normalized = email.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _where_heard_category(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        return "other"
    lower = raw.strip().lower()
    for phrase, category in WHERE_HEARD_MAP.items():
        if phrase in lower:
            return category
    return "other"


def _program_and_cohort_from_filename(name: str) -> tuple:
    """Infer program_selection and cohort_name from GCS object name."""
    base = os.path.basename(name).replace(".xlsx", "").replace(".xls", "")
    program = "Other"
    if "engineering" in base.lower() and "software" not in base.lower():
        program = "Engineering Basics"
    elif "medicine" in base.lower():
        program = "Medicine Basics"
    elif "se_" in base.lower() or "software" in base.lower():
        program = "SE Basics"
    elif "law" in base.lower():
        program = "Law Basics"
    cohort = "Unknown"
    if "april" in base.lower():
        cohort = "April"
    elif "early_registration" in base.lower():
        cohort = "Early registration"
    return program, cohort


def _parse_gpa(val) -> float:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (int, float)):
        if val > 10:  # assume 100-scale
            return round((val / 100) * 4, 2) if val <= 100 else None
        return float(val)
    s = str(val).strip().replace(",", ".").replace("%", "")
    try:
        f = float(s)
        return round((f / 100) * 4, 2) if f > 10 else f
    except ValueError:
        return None


def main(event, context):
    # GCS trigger: event may be dict with bucket, name or wrapped in data (base64)
    bucket = event.get("bucket") if isinstance(event, dict) else None
    name = event.get("name", "") if isinstance(event, dict) else ""
    if not bucket or not name:
        data = event.get("data") if isinstance(event, dict) else None
        if data:
            import base64
            try:
                decoded = json.loads(base64.b64decode(data).decode())
                bucket = decoded.get("bucket")
                name = decoded.get("name", "")
            except Exception:
                pass
    if not name or not name.startswith("forms/"):
        return
    if not (name.endswith(".xlsx") or name.endswith(".xls")):
        return

    source_file = f"gs://{bucket}/{name}"
    run_id = f"{bucket}/{name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    inserted = 0
    rejected = 0
    errors = []

    local_path = event.get("local_path") if isinstance(event, dict) else None
    try:
        if local_path and os.path.isfile(local_path):
            with open(local_path, "rb") as f:
                content = f.read()
        else:
            client = storage.Client(project=PROJECT_ID)
            blob = client.bucket(bucket).blob(name)
            content = blob.download_as_bytes()
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, str(e))
        raise

    try:
        df = pd.read_excel(content, engine="openpyxl")
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, f"parse_error: {e}")
        _reject(source_file, "parse_error", json.dumps({"error": str(e)}))
        return

    # Normalize column names (strip whitespace and \xa0)
    df.columns = [str(c).strip().replace("\xa0", " ") for c in df.columns]

    email_col = "Email2"
    if email_col not in df.columns:
        _log_run(run_id, source_file, "FAILED", 0, len(df), "missing_Email2_column")
        for _, row in df.iterrows():
            _reject(source_file, "schema_mismatch", row.to_json())
        return

    program_selection, cohort_name = _program_and_cohort_from_filename(name)
    now = datetime.now(timezone.utc).isoformat()

    rows_reg = []
    rows_secure = []
    for idx, row in df.iterrows():
        email_raw = row.get(email_col)
        if pd.isna(email_raw) or not str(email_raw).strip():
            _reject(source_file, "invalid_email", row.to_json())
            rejected += 1
            continue
        learner_id = _learner_id(str(email_raw))
        full_name = row.get("Full Name")
        if pd.isna(full_name):
            full_name = ""
        full_name = str(full_name).strip()

        rows_secure.append({
            "learner_id": learner_id,
            "email_canonical": str(email_raw).strip().lower(),
            "full_name_raw": full_name,
            "source_file": source_file,
        })

        linkedin_col = [c for c in df.columns if "linkedin" in c.lower()]
        linkedin_val = row.get(linkedin_col[0], "No") if linkedin_col else "No"
        if isinstance(linkedin_val, str):
            linkedin_val = linkedin_val.strip().replace("\xa0", "")[:10]

        where_raw = row.get("Where did you hear about this program?", "")
        where_cat = _where_heard_category(str(where_raw) if not pd.isna(where_raw) else "")

        start_ts = _parse_ts(row.get("Start time"))
        compl_ts = _parse_ts(row.get("Completion time"))
        mod_ts = _parse_ts(row.get("Last modified time"))

        reg_id = str(row.get("ID", idx))
        rows_reg.append({
            "registration_id": reg_id,
            "learner_id": learner_id,
            "start_time": start_ts,
            "completion_time": compl_ts,
            "last_modified_time": mod_ts,
            "highschool_name": _str(row.get("Highschool Name")),
            "citizenship": _str(row.get("Citizenship")),
            "commitment_per_week": _str(row.get("How much time do you plan to commit per week?")),
            "grade": _str(row.get("Grade")),
            "gpa_4_scale": _parse_gpa(row.get("GPA (100 or 4.0)?", row.get("GPA (100)?", None))),
            "telegram_username": _str(row.get("Telegram user name (@your user name)?")),
            "where_heard_category": where_cat,
            "linkedin_follow": linkedin_val,
            "program_selection": program_selection,
            "cohort_name": cohort_name,
            "source_file": source_file,
            "ingestion_time": now,
            "schema_version": "v1",
        })
        inserted += 1

    # Upsert secure_id_map (one per learner in this file)
    seen_learner = set()
    for r in rows_secure:
        if r["learner_id"] in seen_learner:
            continue
        seen_learner.add(r["learner_id"])
        _upsert_secure_id_map(r)

    # Insert registrations
    if rows_reg:
        table_ref = f"{PROJECT_ID}.silver_trainings.registrations"
        errors_bq = BQ.insert_rows_json(table_ref, rows_reg)
        if errors_bq:
            rejected += len(errors_bq)
            for err in errors_bq:
                errors.append(str(err))

    status = "FAILED" if errors else ("PARTIAL" if rejected else "SUCCESS")
    _log_run(run_id, source_file, status, inserted, rejected, "; ".join(errors) if errors else None)


def _str(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v).strip()[:10000]


def _parse_ts(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    try:
        return pd.to_datetime(v).isoformat()
    except Exception:
        return None


def _upsert_secure_id_map(row):
    q = f"""
    MERGE `{PROJECT_ID}.secure_core.secure_id_map` T
    USING (
      SELECT @learner_id AS learner_id, @email AS email_canonical, @full_name AS full_name_raw, @src AS source_file
    ) S ON T.learner_id = S.learner_id
    WHEN MATCHED THEN UPDATE SET
      full_name_raw = S.full_name_raw,
      updated_at = CURRENT_TIMESTAMP(),
      source_file = S.source_file
    WHEN NOT MATCHED THEN INSERT (learner_id, email_canonical, full_name_raw, created_at, updated_at, source_file)
    VALUES (S.learner_id, S.email_canonical, S.full_name_raw, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), S.source_file)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("learner_id", "STRING", row["learner_id"]),
            bigquery.ScalarQueryParameter("email", "STRING", row["email_canonical"]),
            bigquery.ScalarQueryParameter("full_name", "STRING", row["full_name_raw"]),
            bigquery.ScalarQueryParameter("src", "STRING", row["source_file"]),
        ]
    )
    BQ.query(q, job_config=job_config).result()


def _reject(source_file: str, reason: str, raw_row: str):
    table = f"{PROJECT_ID}.silver_trainings.registrations_rejects"
    now = datetime.now(timezone.utc).isoformat()
    BQ.insert_rows_json(table, [{
        "source_file": source_file,
        "ingestion_time": now,
        "reject_reason": reason,
        "raw_row": raw_row[:100000],
    }])


def _log_run(run_id: str, source: str, status: str, row_count: int, error_count: int, message: str = None):
    table = f"{PROJECT_ID}.silver_trainings.pipeline_run_log"
    now = datetime.now(timezone.utc).isoformat()
    BQ.insert_rows_json(table, [{
        "run_id": run_id,
        "source": source,
        "status": status,
        "row_count": row_count,
        "error_count": error_count,
        "message": message,
        "timestamp": now,
    }])
