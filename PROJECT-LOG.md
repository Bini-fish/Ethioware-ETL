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

- [x] **.gitignore** – Ignore reference/reusable repo (e.g. `Household-Data-Analysis-Real-Time-GCP-Pipeline/`) so it isn’t committed.
- [x] **Cursor rules** – `.cursor/rules/` with Medallion, identity, PII, scoring rules.
- [x] **Cursor skill** – `.cursor/skills/SKILL.md` for Ethioware ETL context so the agent follows the same patterns.
- [ ] **GCP project and region** – Set project (e.g. Ethioware-ETL), region (e.g. me-central1), document fallbacks.
- [ ] **IAM** – Roles for Education Admin, Data Engineer, BI/Marketing, Public.

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

1. Answer follow-up questions in `GOOGLE-FORMS-FORMATS.md`.
2. Standardize forms (or ETL) per checklist in that doc.
3. Sprint 1: GCS buckets, BigQuery datasets, IAM, `secure_core`, audit tables, `bq/sql` and `docs` skeleton.
4. Sprint 2+: Silver DDL and Cloud Functions (registrations, scores, KA, feedback); then Gold and dashboards.

---

*Use this log at the start of a new project: copy the checklist structure, rename the project, and tick or adapt each item.*
