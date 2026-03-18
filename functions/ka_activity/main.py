"""
Ethioware – KA activity ingestion.
Trigger: GCS finalize on ethioware-bronze-trainings/scores/*.csv (files with learner_activity or khan in name) or dedicated prefix.
Reads learner_activity_khan_academy CSV, inserts silver_trainings.ka_activity.
"""
import json
import os
from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery, storage

PROJECT_ID = os.environ.get("GCP_PROJECT", "ethioware-etl")
BQ = bigquery.Client(project=PROJECT_ID)


def main(event, context):
    bucket = None
    name = ""
    if isinstance(event, dict):
        bucket = event.get("bucket")
        name = event.get("name") or ""
        if (not bucket or not name) and event.get("data") is not None:
            data = event["data"]
            if isinstance(data, dict):
                bucket = data.get("bucket") or bucket
                name = data.get("name") or name
            else:
                import base64
                try:
                    decoded = json.loads(base64.b64decode(data).decode())
                    bucket = decoded.get("bucket") or bucket
                    name = decoded.get("name") or name
                except Exception:
                    pass
    lower = name.lower() if name else ""
    if not (isinstance(event, dict) and event.get("local_path")):
        if not ("learner_activity" in lower or "khan" in lower or "ka_activity" in lower):
            return
    if not name.endswith(".csv"):
        return

    source_file = f"gs://{bucket}/{name}"
    run_id = f"{bucket}/{name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    inserted = 0
    rejected = 0
    errors = []

    local_path = event.get("local_path") if isinstance(event, dict) else None
    try:
        if local_path and os.path.isfile(local_path):
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        else:
            client = storage.Client(project=PROJECT_ID)
            blob = client.bucket(bucket).blob(name)
            content = blob.download_as_bytes().decode("utf-8", errors="replace")
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, str(e))
        raise

    try:
        df = pd.read_csv(pd.io.common.StringIO(content))
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, f"parse_error: {e}")
        _reject(source_file, "parse_error", json.dumps({"error": str(e)}))
        return

    df.columns = [str(c).strip() for c in df.columns]

    def col(row_dict, *candidates):
        for c in candidates:
            key = c.lower().replace(" ", "_")
            for k in row_dict:
                if k and str(k).lower().replace(" ", "_") == key:
                    return row_dict.get(k)
            if c in row_dict:
                return row_dict.get(c)
        return None

    rows = []
    for idx, row in df.iterrows():
        row_d = row.to_dict()
        learner = col(row_d, "student", "learner", "email", "name")
        if learner is None or pd.isna(learner):
            learner = row_d.get(df.columns[0]) if len(df.columns) else ""
        if pd.isna(learner) or not str(learner).strip():
            _reject(source_file, "incomplete", row.to_json())
            rejected += 1
            continue
        now = datetime.now(timezone.utc).isoformat()
        rows.append({
            "learner_identifier": str(learner).strip()[:500],
            "provider_id": "khan_academy",
            "total_learning_minutes": _int(col(row_d, "Total Learning minutes", "total_learning_minutes")),
            "skills_worked_on": _int(col(row_d, "skills worked on", "skills_worked_on")),
            "skills_leveled_up": _int(col(row_d, "skills leveled up", "skills_leveled_up")),
            "skills_to_improve": _int(col(row_d, "skills to improve", "skills_to_improve")),
            "attempted": _int(col(row_d, "Attempted", "attempted")),
            "familiar": _int(col(row_d, "Familiar", "familiar")),
            "proficient": _int(col(row_d, "Proficient", "proficient")),
            "mastered": _int(col(row_d, "Mastered", "mastered")),
            "source_file": source_file,
            "ingestion_time": now,
        })
        inserted += 1

    if rows:
        errs = BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.ka_activity", rows)
        if errs:
            rejected += len(errs)
            errors.extend([str(e) for e in errs])

    status = "FAILED" if errors else ("PARTIAL" if rejected else "SUCCESS")
    _log_run(run_id, source_file, status, inserted, rejected, "; ".join(errors) if errors else None)


def _int(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return 0


def _reject(source_file: str, reason: str, raw_row: str):
    BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.ka_activity_rejects", [{
        "source_file": source_file,
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
        "reject_reason": reason,
        "raw_row": raw_row[:100000],
    }])


def _log_run(run_id: str, source: str, status: str, row_count: int, error_count: int, message: str = None):
    BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.pipeline_run_log", [{
        "run_id": run_id,
        "source": source,
        "status": status,
        "row_count": row_count,
        "error_count": error_count,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }])
