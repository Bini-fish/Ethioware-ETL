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
- [ ] **GCP project and region** – Set project (e.g. Ethioware-ETL), region (e.g. me-central1), document fallbacks.
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

## 7. Next steps (implementation)

**Immediate (Sprint 1 – Foundation)**  
1. **GCP** – Create or select project (e.g. `Ethioware-ETL`), set region (e.g. `me-central1`), document in `docs/architecture.md`.  
2. **Bronze** – Create GCS buckets: `ethioware-bronze-trainings` (prefixes: forms/, scores/, feedback/), `ethioware-bronze-marketing` (youtube/, linkedin/), `ethioware-bronze-web` (analytics/).  
3. **BigQuery** – Create datasets: `secure_core`, `silver_trainings`, `silver_marketing`, `silver_web`, `gold_*`, `dash_*` (or single `dash`).  
4. **Identity & audit** – DDL for `secure_core.secure_id_map`, `pipeline_run_log`, and Silver rejects tables; add `dim_date`.  
5. **Repo skeleton** – Add `bq/sql/silver/`, `bq/sql/gold/` with DDL file placeholders; add `docs/architecture.md` and `docs/runbook.md`.  
6. **IAM** – Define roles (Education Admin, Data Engineer, BI/Marketing) and apply least privilege per dataset.

**Then (Sprint 2+)**  
7. Answer follow-up questions in `GOOGLE-FORMS-FORMATS.md` (or document “ETL decides” for GPA, dedupe, timezone).  
8. Silver DDL and Cloud Functions: registrations → scores → ka_activity → feedback (see `docs/IMPLEMENTATION-PLAN.md` §2).  
9. Test with `Datasets/trainings/` and `Datasets/marketing/` files; backfill to Silver.  
10. Gold layer (dim/fact/views) and scoring views; then marketing/web and dashboards.

---

*Use this log at the start of a new project: copy the checklist structure, rename the project, and tick or adapt each item.*
