#!/usr/bin/env python3
"""
Run Ethioware ingestion functions locally for testing before deploying to Cloud Functions.
Use --local <file> to read from disk (no GCS) or --gcs gs://bucket/key to use real GCS.
BigQuery writes are always real (set GOOGLE_APPLICATION_CREDENTIALS or gcloud auth).
"""
import argparse
import importlib.util
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("GCP_PROJECT"):
    os.environ["GCP_PROJECT"] = "ethioware-etl"


def _prefix_for(function: str) -> str:
    if function == "registrations":
        return "forms/"
    if function in ("scores", "ka_activity"):
        return "scores/"
    if function == "feedback":
        return "feedback/"
    return ""


def _load_main(function: str):
    """Load main() from functions/<function>/main.py."""
    path = os.path.join(REPO_ROOT, "functions", function, "main.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No main.py at {path}")
    spec = importlib.util.spec_from_file_location(f"ethioware_{function}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.main


def main():
    parser = argparse.ArgumentParser(
        description="Run Ethioware ingestion locally. Use --local to read from file, --gcs to read from GCS."
    )
    parser.add_argument(
        "function",
        choices=["registrations", "scores", "ka_activity", "feedback"],
        help="Which Cloud Function logic to run",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--local", metavar="PATH", help="Path to local file (Excel or CSV). Replaces GCS read.")
    group.add_argument("--gcs", metavar="URI", help="GCS URI, e.g. gs://ethioware-bronze-trainings/forms/file.xlsx")
    parser.add_argument(
        "--bucket",
        default="ethioware-bronze-trainings",
        help="Bucket name when using --local (default: ethioware-bronze-trainings)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip BigQuery writes; only parse and print summary (no GCP credentials needed)")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "1"

    if args.local:
        path = os.path.abspath(args.local)
        if not os.path.isfile(path):
            print(f"Error: not a file: {path}", file=sys.stderr)
            sys.exit(1)
        prefix = _prefix_for(args.function)
        name = prefix + os.path.basename(path)
        event = {
            "bucket": args.bucket,
            "name": name,
            "local_path": path,
        }
        print(f"Using local file: {path} (event name={name})")
    else:
        uri = args.gcs.strip()
        if not uri.startswith("gs://"):
            print("Error: --gcs must be gs://bucket/key", file=sys.stderr)
            sys.exit(1)
        parts = uri[5:].split("/", 1)
        bucket = parts[0]
        name = parts[1] if len(parts) > 1 else ""
        if not name:
            print("Error: --gcs must include object key", file=sys.stderr)
            sys.exit(1)
        event = {"bucket": bucket, "name": name}
        print(f"Using GCS: gs://{bucket}/{name}")

    run_main = _load_main(args.function)
    run_main(event, None)
    print("Done.")


if __name__ == "__main__":
    main()
