"""
Ethioware – Scores ingestion.
Trigger: GCS finalize on ethioware-bronze-trainings/scores/*.csv
Supports November and May score sheet schemas.

Core (raw) columns kept in Silver:
  Name, User-name/User name, Cohort, Quiz score,
  Khan Academy score / Khan Acadmy score, Learning Minutes.

Derived columns (Quiz %, Relative %, Average, Rank, KA Score, %KA,
Total points) are NOT stored — they are recomputed in Gold views.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone

import functions_framework
import pandas as pd
from cloudevents.http import CloudEvent
from google.cloud import bigquery, storage

PROJECT_ID = os.environ.get("GCP_PROJECT", "ethioware-etl")
_BQ = None
KA_FILENAME_HINTS = ("learner_activity", "khan", "ka_activity", "all_assignments")


def _get_bq():
    global _BQ
    if _BQ is None:
        _BQ = bigquery.Client(project=PROJECT_ID)
    return _BQ


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


def _col(df_columns: list[str], *candidates: str):
    """Return the first matching column name (case-insensitive, stripped)."""
    lower_map = {c.strip().lower(): c for c in df_columns}
    for c in candidates:
        if c.strip().lower() in lower_map:
            return lower_map[c.strip().lower()]
    return None


def _has_score_schema(columns: list[str]) -> bool:
    lower = {str(c).strip().lower() for c in columns}
    has_quiz_score = "quiz score" in lower
    has_context = ("cohort" in lower) or ("quiz percentage" in lower)
    return has_quiz_score and has_context


# ── Processing core ───────────────────────────────────────────────────────

def _process(bucket: str, name: str, local_path: str = None):
    source_file = f"gs://{bucket}/{name}"
    run_id = f"{bucket}/{name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    inserted = 0
    rejected = 0
    errors = []
    lower_name = name.lower()

    print(f"[scores] Processing {source_file}", flush=True)

    if not name.startswith("scores/"):
        print(f"[scores] Skipping — not in scores/ prefix: {name!r}", flush=True)
        return
    if not name.endswith(".csv"):
        print(f"[scores] Skipping — not a .csv: {name!r}", flush=True)
        return

    if any(hint in lower_name for hint in KA_FILENAME_HINTS):
        msg = "skipped_non_scores_file_routed_to_ka_activity"
        print(f"[scores] {msg}: {source_file}", flush=True)
        if not os.environ.get("DRY_RUN"):
            _log_run(run_id, source_file, "SKIPPED", 0, 0, msg)
        return

    # ── Download / read ──
    try:
        if local_path and os.path.isfile(local_path):
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        else:
            client = storage.Client(project=PROJECT_ID)
            blob = client.bucket(bucket).blob(name)
            content = blob.download_as_bytes().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[scores] Download failed: {e}", flush=True)
        _log_run(run_id, source_file, "FAILED", 0, 0, str(e))
        raise

    # ── Parse CSV ──
    try:
        df = pd.read_csv(pd.io.common.StringIO(content))
    except Exception as e:
        print(f"[scores] CSV parse error: {e}", flush=True)
        _log_run(run_id, source_file, "FAILED", 0, 0, f"parse_error: {e}")
        _reject(source_file, "parse_error", json.dumps({"error": str(e)}))
        return

    df.columns = [str(c).strip() for c in df.columns]
    print(f"[scores] Columns after strip: {list(df.columns)}", flush=True)

    if not _has_score_schema(df.columns):
        msg = "unsupported_scores_schema"
        print(f"[scores] {msg}: {source_file}", flush=True)
        if not os.environ.get("DRY_RUN"):
            _log_run(run_id, source_file, "SKIPPED", 0, 0, msg)
        return

    # ── Column resolution ──
    col_name = _col(df.columns, "Name")
    col_email = _col(df.columns, "Email Address", "Email")
    col_user = _col(df.columns, "User name", "User-name")
    col_cohort = _col(df.columns, "Cohort")
    col_quiz = _col(df.columns, "Quiz score")
    col_quiz_pct = _col(df.columns, "Quiz percentage")
    # Raw KA columns first, derived last (KA Score is computed in November)
    col_ka = _col(df.columns, "Khan Acadmy score", "Khan Academy score", "KA Score")
    col_lm = _col(df.columns, "Learning Minutes")

    print(f"[scores] Resolved: ka={col_ka!r} lm={col_lm!r} rows={len(df)}", flush=True)

    # ── Row processing ──
    rows = []
    seen_hash = set()

    for idx, row in df.iterrows():
        try:
            name_val = row.get(col_name) if col_name else None
            if name_val is not None and pd.isna(name_val):
                name_val = None

            email_val = row.get(col_email) if col_email else None
            if email_val is not None and pd.isna(email_val):
                email_val = None

            user_val = row.get(col_user) if col_user else None
            if user_val is not None and pd.isna(user_val):
                user_val = None

            learner_id = ""
            if email_val:
                learner_id = str(email_val).strip()
            if not learner_id and user_val:
                learner_id = str(user_val).strip()
            if not learner_id and name_val:
                learner_id = str(name_val).strip()

            if not learner_id:
                _reject(source_file, "incomplete", row.to_json())
                rejected += 1
                continue

            cohort = ""
            if col_cohort:
                raw_cohort = row.get(col_cohort)
                if raw_cohort is not None and not pd.isna(raw_cohort):
                    cohort = str(raw_cohort).strip()
            field = cohort.replace("Basics", "").strip() if cohort else ""
            if "Both" in cohort:
                field = "Both"

            quiz_score = _parse_num(row.get(col_quiz) if col_quiz else None)
            quiz_pct = _parse_num(row.get(col_quiz_pct) if col_quiz_pct else None)
            ka_score = _parse_num(row.get(col_ka) if col_ka else None)
            learning_min = _parse_num(row.get(col_lm) if col_lm else None)

            row_hash = hashlib.sha256(
                f"{learner_id}|{cohort}|{field}|{quiz_score}|{ka_score}|{learning_min}".encode()
            ).hexdigest()
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
                "total_points_pct": None,
                "rank": None,
                "source_file": source_file,
                "ingestion_time": now,
                "row_hash": row_hash,
            })
            inserted += 1

        except Exception as row_err:
            print(f"[scores] Row {idx} error: {row_err}", flush=True)
            try:
                _reject(source_file, f"row_error: {row_err}", row.to_json())
            except Exception:
                pass
            rejected += 1

    # ── Insert into BigQuery ──
    if rows:
        if os.environ.get("DRY_RUN"):
            print(f"[DRY_RUN] Would insert {len(rows)} row(s) into silver_trainings.scores_raw. First row: {rows[0]}", flush=True)
        else:
            BQ = _get_bq()
            errs = BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.scores_raw", rows)
            if errs:
                rejected += len(errs)
                errors.extend([str(e) for e in errs])
                print(f"[scores] BQ insert errors: {errs}", flush=True)

    status = "FAILED" if errors else ("PARTIAL" if rejected else "SUCCESS")
    print(f"[scores] Done: status={status} inserted={inserted} rejected={rejected}", flush=True)

    if os.environ.get("DRY_RUN"):
        print(f"[DRY_RUN] status={status} inserted={inserted} rejected={rejected}", flush=True)
    else:
        _log_run(run_id, source_file, status, inserted, rejected, "; ".join(errors) if errors else None)


# ── Entry points ──────────────────────────────────────────────────────────

@functions_framework.cloud_event
def cf_main(cloud_event: CloudEvent):
    """Gen2 Eventarc/GCS entry point — deployed with --entry-point=cf_main."""
    data = cloud_event.data or {}
    if isinstance(data, dict):
        _process(
            bucket=data.get("bucket", ""),
            name=data.get("name", ""),
        )


def main(event, context=None):
    """Local runner / legacy compatibility entry point."""
    bucket = None
    name = ""
    local_path = None
    if isinstance(event, dict):
        bucket = event.get("bucket")
        name = event.get("name") or ""
        local_path = event.get("local_path")
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
    if bucket and name:
        _process(bucket, name, local_path)


# ── Helpers ───────────────────────────────────────────────────────────────

def _reject(source_file: str, reason: str, raw_row: str):
    if os.environ.get("DRY_RUN"):
        print(f"[DRY_RUN] reject reason={reason}", flush=True)
        return
    _get_bq().insert_rows_json(f"{PROJECT_ID}.silver_trainings.scores_rejects", [{
        "source_file": source_file,
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
        "reject_reason": reason,
        "raw_row": raw_row[:100000],
    }])


def _log_run(run_id: str, source: str, status: str, row_count: int, error_count: int, message: str = None):
    if os.environ.get("DRY_RUN"):
        return
    _get_bq().insert_rows_json(f"{PROJECT_ID}.silver_trainings.pipeline_run_log", [{
        "run_id": run_id,
        "source": source,
        "status": status,
        "row_count": row_count,
        "error_count": error_count,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }])
