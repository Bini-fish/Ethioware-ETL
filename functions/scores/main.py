"""
Ethioware – Scores ingestion.
Trigger: GCS finalize on ethioware-bronze-trainings/scores/*.csv
Supports November and May score sheet schemas; strips commas from Learning Minutes; dedupes by row_hash.
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


def _parse_num(s) -> float:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s).strip().replace(",", "").replace("%", "").replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main(event, context):
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
    if not name or not name.startswith("scores/"):
        return
    if not name.endswith(".csv"):
        return

    source_file = f"gs://{bucket}/{name}"
    run_id = f"{bucket}/{name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    inserted = 0
    rejected = 0
    errors = []

    try:
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
    rows = []
    seen_hash = set()

    # November: Name, Email Address, User name, Cohort, Quiz score, Quiz percentage, Khan Acadmy score, Learning Minutes, KA Score, %KA, Total points, Rank
    # May: Name, User-name, Cohort, Quiz score, Quiz percentage, Khan Academy score, Relative % to the top scorer, Average, Rank
    has_nov = "Learning Minutes" in df.columns or "Khan Acadmy score" in df.columns
    has_may = "User-name" in df.columns or "Khan Academy score" in df.columns

    for idx, row in df.iterrows():
        name_val = row.get("Name", row.get("name", ""))
        if pd.isna(name_val) and not has_may:
            _reject(source_file, "incomplete", row.to_json())
            rejected += 1
            continue
        learner_id = str(name_val).strip() if not pd.isna(name_val) else ""
        email = row.get("Email Address", row.get("Email", ""))
        if not pd.isna(email) and str(email).strip():
            learner_id = str(email).strip() or learner_id
        user = row.get("User name", row.get("User-name", ""))
        if not pd.isna(user) and str(user).strip():
            learner_id = learner_id or str(user).strip()
        if not learner_id:
            _reject(source_file, "incomplete", row.to_json())
            rejected += 1
            continue

        cohort = str(row.get("Cohort", "")).strip() if not pd.isna(row.get("Cohort")) else ""
        field = cohort.replace("Basics", "").strip() if cohort else ""
        if "Both" in cohort:
            field = "Both"

        learning_min = row.get("Learning Minutes", None)
        learning_min = _parse_num(learning_min)
        quiz_score = _parse_num(row.get("Quiz score", None))
        quiz_pct = _parse_num(row.get("Quiz percentage", None))
        ka_score = row.get("KA Score", row.get("Khan Academy score", row.get("Khan Acadmy score", None)))
        ka_score = _parse_num(ka_score)
        total_pct = _parse_num(row.get("Total points", row.get("Average", None)))
        rank = row.get("Rank", None)
        if rank is not None and not pd.isna(rank):
            try:
                rank = int(float(rank))
            except (ValueError, TypeError):
                rank = None

        row_hash = hashlib.sha256(f"{learner_id}|{cohort}|{field}|{quiz_score}|{ka_score}|{learning_min}".encode()).hexdigest()
        if row_hash in seen_hash:
            _reject(source_file, "duplicate", row.to_json())
            rejected += 1
            continue
        seen_hash.add(row_hash)

        now = datetime.now(timezone.utc).isoformat()
        rows.append({
            "learner_identifier": learner_id[:500],
            "cohort": cohort[:200],
            "field": field[:200],
            "quiz_score": quiz_score,
            "quiz_pct": quiz_pct,
            "ka_score": ka_score,
            "learning_minutes": learning_min,
            "total_points_pct": total_pct,
            "rank": rank,
            "source_file": source_file,
            "ingestion_time": now,
            "row_hash": row_hash,
        })
        inserted += 1

    if rows:
        table_ref = f"{PROJECT_ID}.silver_trainings.scores_raw"
        errs = BQ.insert_rows_json(table_ref, rows)
        if errs:
            rejected += len(errs)
            errors.extend([str(e) for e in errs])

    status = "FAILED" if errors else ("PARTIAL" if rejected else "SUCCESS")
    _log_run(run_id, source_file, status, inserted, rejected, "; ".join(errors) if errors else None)


def _reject(source_file: str, reason: str, raw_row: str):
    BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.scores_rejects", [{
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
