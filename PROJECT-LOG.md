# Project log – Ethioware GCP Pipeline (reusable for next project)

Track what was done in this project so the same approach can be reused elsewhere (e.g. another EdTech pipeline or Medallion ETL).

---

## 1. Before implementation – data and schema

- [x] **Master plan** – One ETL plan document (`Ethioware-ETL-Plan.md`) with architecture, data model, identity/PII, scoring, sprints, and pitfalls.
- [x] **Workspace scan** – Listed all files; mapped Datasets to Silver/Gold; noted missing code (no `functions/`, `bq/` yet).
- [x] **Implementation plan** – Created `docs/IMPLEMENTATION-PLAN.md` with sprint-by-sprint tasks, file checklist, and source-schema notes.
- [x] **Form formats** – Documented Google Form exports (raw column names, differences between forms, cleaning rules) in `docs/GOOGLE-FORMS-FORMATS.md`.
- [x] **Assumptions and questions** – Listed assumptions and follow-up questions in the same doc so stakeholders can clarify before coding.
- [x] **Schema reference** – Single `docs/schema.md` for every CSV (trainings + social media): columns, types, parsing notes, Silver target.
- [x] **Forms quick reference** – `docs/FORMS-QUICK-REFERENCE.md` with form name and exact column names for quick lookup when filling or mapping forms.
- [ ] **Stakeholder answers** – Fill in answers to the follow-up questions in `GOOGLE-FORMS-FORMATS.md` (GPA, dedupe, timezone, extra forms, etc.).
- [ ] **Form standardization** – Unify GPA and LinkedIn questions in Forms (or in ETL); normalize Citizenship/Grade if using controlled vocabulary.

**Reuse in next project:** Start with one ETL/architecture doc, scan datasets, write implementation plan, then **document all form/source schemas and assumptions** before writing ingestion code.

---

## 2. Repo and governance

- [x] **.gitignore** – Ignore reference/reusable repo (e.g. `Household-Data-Analysis-Real-Time-GCP-Pipeline/`) so it isn’t committed. **Datasets/** added so data assets stay local.
- [x] **Datasets restructure** – Logical layout: **trainings/** (registration, feedback, scores, ka_activity, cohort, legacy), **marketing/** (linkedin, youtube, web_analytics), **reference/**, **archive/**; docs updated to new paths.
- [x] **Repo override** – Local state committed and force-pushed to `origin/master`; remote reflects current files and structure.
- [x] **Cursor rules** – `.cursor/rules/` with Medallion, identity, PII, scoring rules.
- [x] **Cursor skill** – `.cursor/skills/SKILL.md` for Ethioware ETL context so the agent follows the same patterns.
- [x] **GCP project and region** – Project `ethioware-etl`, BigQuery in `us-central1`, GCS in US multi-region. Documented in `docs/architecture.md`.
- [x] **IAM** – Custom roles (Ethioware Data Engineer, Education Admin, BI/Marketing); project-level for Data Engineer, dataset-level for Education Admin and BI/Marketing. No public access. See **docs/iam.md** for role-to-dataset mapping.

**Reuse in next project:** Add rules and a skill for the new domain; keep .gitignore and docs in sync with actual sources.

---

## 3. Documentation layout

| Document | Purpose |
|----------|---------|
| `Ethioware-ETL-Plan.md` | Master blueprint (architecture, model, scoring, sprints). |
| `README.md` | Project overview and planned folder structure. |
| `docs/IMPLEMENTATION-PLAN.md` | Execution checklist by sprint; file list; schema/parsing notes. |
| `docs/GOOGLE-FORMS-FORMATS.md` | Form export columns, cleaning rules, target schema, assumptions, follow-up questions. |
| `docs/FORMS-QUICK-REFERENCE.md` | One-page list of forms and their column names. |
| `docs/schema.md` | Every CSV: columns, types, Silver target. |
| `PROJECT-LOG.md` (this file) | What we did; reusable checklist for the next project. |

**Reuse in next project:** Keep the same doc roles; duplicate and rename (e.g. FORMS → “Survey formats” if different source).

---

## 4. Data sources summarized

- **Trainings – Forms:** **Microsoft Form only** for registration (Engineering, Medicine, SE; **Law** same schema when added). **Where heard** → Silver categories: **social_media**, **word_of_mouth**, **other**. **Session Feedback Form** (expert rating) – less frequent; **Rating/Rating2 for dashboard.** Mentor/Trainee feedback via Google Forms.
- **Trainings – Sheets/CSV:** Score sheets (November, May), KA activity, cohort aggregate; slides optional.
- **Marketing/Web:** YouTube; LinkedIn (followers, visitors, **competitor analytics** → Silver with **competitor dimension** for future competitors; updated less frequently); Web (requests by country).  

**Reuse in next project:** List all sources and mark which are “form-like” (variable schema) vs “platform export” (stable schema).

---

## 5. Decisions made

- **Registration:** Microsoft Form only; no Google Form for new ingestion. Law uses same schema when export is added.
- **Where did you hear?** In Silver, map to standard categories: **social_media**, **word_of_mouth**, **other** (add more as needed).
- **Competitor analytics:** Silver table **`linkedin_competitor_analytics`** with **competitor dimension** (competitor_id/name) so more competitors can be added later; updated less frequently than followers/visitors.

## 6. Decisions still open (to be filled when decided) (to be filled when decided)

- GPA: one scale (4.0) only or keep raw (100/%)?
- Registration dedupe: first vs latest per email?
- Timezone for form timestamps?
- Extra registration/feedback forms for other **programs** (feedback per program: Software Engineering, Law, etc.)?
- Score sheets: always Sheets/CSV or future form/API?
- “Both” (multi-field): one row vs two rows per field in Silver?

---

## 7. Sprint progress

**Sprint 1 – Foundation (DONE)**
1. [x] GCP project `ethioware-etl`, BigQuery `us-central1`, GCS US multi-region.
2. [x] GCS buckets: `ethioware-bronze-trainings` (forms/, scores/, feedback/), `ethioware-bronze-marketing`, `ethioware-bronze-web`.
3. [x] BigQuery datasets: `secure_core`, `silver_trainings`, `silver_marketing`, `silver_web`, `gold_trainings`, `gold_marketing`, `gold_web`, `dash_admin`, `dash_marketing`, `dash_board`, `dash_public`.
4. [x] DDL: `secure_core.secure_id_map`, `pipeline_run_log`, rejects tables, `dim_date`.
5. [x] Repo skeleton: `bq/sql/`, `docs/`, `functions/`, `scripts/`.
6. [x] IAM: custom roles (Data Engineer, Education Admin, BI/Marketing).

**Sprint 2 – Silver Trainings (DONE)**
7. [x] Silver DDL: registrations, scores_raw, ka_activity, feedback.
8. [x] Cloud Functions (Gen2): registrations (cf_main), scores, ka_activity, feedback — all deployed and tested.
9. [x] Test suite: 7/8 PASS, 1 INCONCLUSIVE (November scores). See `docs/SPRINT2-UPLOAD-TEST-CHECKLIST.md`.
10. [x] Key fix: batched secure_id_map MERGE (117x faster); flush=True on all prints.

**Sprint 3 – Gold Trainings (IN PROGRESS)**
11. [ ] Gold dimension DDLs: dim_learner, dim_cohort, dim_field, dim_institution, dim_learning_provider.
12. [ ] bridge_learner_field for multi-field enrollment.
13. [ ] Backfill dimensions from Silver.
14. [ ] Fact tables: fact_scores, fact_engagement, fact_feedback.
15. [ ] Scoring views: v_scores_v1 (relative %, engagement composite).

**Sprint 4 – Marketing, Web, Dashboards (PENDING)**
16. [ ] Marketing Silver/Gold (YouTube, LinkedIn, web).
17. [ ] Dashboard views (dash_admin, dash_marketing, dash_board, dash_public).
18. [ ] Looker Studio dashboards.

---

*Use this log at the start of a new project: copy the checklist structure, rename the project, and tick or adapt each item.*
