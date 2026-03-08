"""
Ethioware – Feedback ingestion.
Trigger: GCS finalize on ethioware-bronze-trainings/feedback/*
Reads Session Feedback Form (Excel) or mentor/trainee CSV/Excel; sets feedback_type from filename.
Optional Cloud Natural Language API for sentiment when not present in source.
"""
import json
import os
from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery, storage

PROJECT_ID = os.environ.get("GCP_PROJECT", "ethioware-etl")
BQ = bigquery.Client(project=PROJECT_ID)

# Set to "true" to call Cloud Natural Language API for sentiment when missing
USE_NLP_SENTIMENT = os.environ.get("USE_NLP_SENTIMENT", "false").lower() == "true"


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
    if not name or not name.startswith("feedback/"):
        return
    base = os.path.basename(name).lower()
    if not (base.endswith(".xlsx") or base.endswith(".xls") or base.endswith(".csv")):
        return

    source_file = f"gs://{bucket}/{name}"
    run_id = f"{bucket}/{name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    inserted = 0
    rejected = 0
    errors = []

    # Infer feedback_type from filename
    if "session" in base and "feedback" in base:
        feedback_type = "expert"
    elif "mentor" in base:
        feedback_type = "mentor"
    elif "trainee" in base:
        feedback_type = "trainee"
    else:
        feedback_type = "expert"

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
        if name.endswith(".csv"):
            df = pd.read_csv(pd.io.common.BytesIO(content))
        else:
            df = pd.read_excel(content, engine="openpyxl")
    except Exception as e:
        _log_run(run_id, source_file, "FAILED", 0, 0, f"parse_error: {e}")
        _reject(source_file, "parse_error", json.dumps({"error": str(e)}))
        return

    df.columns = [str(c).strip().replace("\xa0", " ") for c in df.columns]

    # Session Feedback Form columns: Rating, Rating2, and text Qs
    rating_col = _find_col(df.columns, "rating", exclude_sub="rating2")
    rating2_col = _find_col(df.columns, "rating2", "recommendation")
    exclude = {"ID", "Start time", "Completion time", "Email", "Name", "Last modified time"}
    if rating_col:
        exclude.add(rating_col)
    if rating2_col:
        exclude.add(rating2_col)
    text_cols = [c for c in df.columns if c and c not in exclude]

    rows = []
    for idx, row in df.iterrows():
        feedback_id = str(row.get("ID", f"{source_file}_{idx}")).strip()[:500]
        learner = _str(row.get("Email", row.get("Name", "anonymous")))
        if not learner or learner == "nan":
            learner = "anonymous"
        rating = _str(row.get(rating_col)) if rating_col else None
        rating2 = _str(row.get(rating2_col)) if rating2_col else None
        parts = []
        for c in text_cols:
            v = row.get(c)
            if v is not None and not pd.isna(v) and str(v).strip():
                parts.append(str(v).strip())
        feedback_text = "\n".join(parts)[:100000] if parts else None

        sentiment_label = _str(row.get("sentiment_label", row.get("Sentiment", row.get("sentiment"))))
        sentiment_score = _float(row.get("sentiment_score", row.get("Sentiment score")))
        model_version = _str(row.get("model_version"))

        if (not sentiment_label or not sentiment_label.strip()) and feedback_text and USE_NLP_SENTIMENT:
            try:
                from google.cloud import language_v1
                client_nl = language_v1.LanguageServiceClient()
                doc = language_v1.Document(content=feedback_text[:5000], type_=language_v1.Document.Type.PLAIN_TEXT)
                resp = client_nl.analyze_sentiment(request={"document": doc})
                if resp.document_sentiment:
                    sentiment_score = resp.document_sentiment.score
                    sentiment_label = "Positive" if sentiment_score > 0.25 else ("Negative" if sentiment_score < -0.25 else "Neutral")
                    model_version = "google_nl_v1"
            except Exception as e:
                errors.append(f"nlp:{e}")

        now = datetime.now(timezone.utc).isoformat()
        rows.append({
            "feedback_id": feedback_id,
            "learner_identifier": learner[:500],
            "feedback_type": feedback_type,
            "rating": rating,
            "rating2": rating2,
            "feedback_text": feedback_text,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "model_version": model_version,
            "source_file": source_file,
            "ingestion_time": now,
        })
        inserted += 1

    if rows:
        errs = BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.feedback", rows)
        if errs:
            rejected += len(errs)
            errors.extend([str(e) for e in errs])

    status = "FAILED" if errors else ("PARTIAL" if rejected else "SUCCESS")
    _log_run(run_id, source_file, status, inserted, rejected, "; ".join(errors) if errors else None)


def _find_col(columns, *substrings, exclude_sub=None):
    for c in columns:
        if not c:
            continue
        lower = c.lower()
        if exclude_sub and exclude_sub.lower() in lower:
            continue
        for s in substrings:
            if s in lower:
                return c
    return None


def _str(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v).strip()[:10000]


def _float(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _reject(source_file: str, reason: str, raw_row: str):
    BQ.insert_rows_json(f"{PROJECT_ID}.silver_trainings.feedback_rejects", [{
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
