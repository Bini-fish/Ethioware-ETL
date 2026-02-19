## Ethioware EdTech – GCP Medallion Pipeline

This project implements a secure, scalable **GCP Medallion data pipeline** (Bronze → Silver → Gold) for the **Ethioware EdTech Initiative**.

The pipeline ingests training and marketing data from Google Forms/Sheets, CSV exports, and (later) APIs into **Google Cloud Storage**, transforms and standardizes it using **Cloud Functions / Cloud Run** and **BigQuery**, and exposes analytical star schemas and dashboards via **Looker Studio**.

For the detailed architecture, data model, and implementation roadmap, see:

- `Ethioware-ETL-Plan.md`

### Project Structure

Planned high-level layout of this repository:

- `Datasets/`  
  Raw and cleaned reference CSVs used for backfills, schema design, and testing.

- `functions/`  
  Python Cloud Functions / Cloud Run services that ingest data from GCS into BigQuery Silver tables.
  - `functions/registrations/`
  - `functions/scores/`
  - `functions/feedback/`
  - `functions/marketing_youtube/`
  - `functions/marketing_linkedin/`

- `bq/`  
  BigQuery SQL for schemas, transformations, and views.
  - `bq/sql/silver/` – DDL + DML for Silver-layer tables and cleanup jobs.
  - `bq/sql/gold/` – DDL + DML for Gold-layer dim/fact tables and scoring/engagement views.

- `docs/`  
  Additional documentation (architecture diagrams, runbooks, data dictionary, etc.).

- `.cursor/`  
  Cursor configuration, rules, and skills (e.g. `ethioware-etl` skill).

- `Ethioware-ETL-Plan.md`  
  Master blueprint for architecture, data model, ingestion, security, and the 12-week implementation plan.

### Git / GitHub Notes

- This folder currently lives inside a larger git repository rooted at `C:/Users/Administrator/Documents`.
- When pushing to GitHub, you have two main options:
  1. **Use the parent repo** and selectively commit this folder.
  2. **Create a dedicated repo** rooted at `Ethioware GCP Pipeline` (recommended if you want this project isolated).

If you choose a dedicated repo, initialize git from this folder and connect it to a new GitHub repository, making sure you do **not** add the sibling `Household-Data-Analysis-Real-Time-GCP-Pipeline/` directory to that repo.

