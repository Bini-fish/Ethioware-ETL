# Registration and form formats – Ethioware trainings (pre-implementation)

Use this document to **standardize and clean** form/survey exports before pipeline implementation. **Registration is collected via Microsoft Form only** (no Google Form registration for new ingestion). **Session Feedback Form** (expert rating) is also Microsoft Form/Excel – less frequent; **expert rating is used on the dashboard.** Other feedback in the dataset may still be Google Forms. Social media data is from the platforms (YouTube, LinkedIn, web).

**Programs (four):** Software Engineering, Medicine, Engineering, Law. **Law** does not have a registration export yet; when added, it will use the **same schema** as Engineering/Medicine/SE (same 16 columns).

---

## Current Microsoft Form – Registration (from `Datasets/trainings/registration/`)

The **current** registration exports are in **`Datasets/trainings/registration/`**. There are **separate Excel exports per program** (Engineering Basics, Medicine Basics, SE [Software Engineering] Basics). **Law** is not yet live; when a Law registration export is added, use the **same 16-column schema** as the others. Program is inferred from the **filename**, not from a column.

**Files (examples):**
- `Enginerring_Basics_Registration Early_registration_for_April_cohort1.xlsx` *(note: typo "Enginerring")*
- `Medicine_Basics_Registration_Early_registration_for_April_cohort1.xlsx`
- `SE_Basics_Registration Early_registration_for_April_cohort1_171.xlsx`

| # | Column name (exact in Microsoft Form export) | Notes |
|---|---------------------------------------------|--------|
| 1 | ID | Submission ID (capital ID) |
| 2 | Start time | |
| 3 | Completion time | |
| 4 | Email | System; often "anonymous" |
| 5 | Name | System; often empty |
| 6 | Last modified time | **New** system column (not in old Google Form) |
| 7 | Full Name | Form question – canonical name |
| 8 | Email2 | **Form question – canonical email** (use for `learner_id`). Note: named Email2, not Email1. |
| 9 | Highschool Name | |
| 10 | Citizenship | |
| 11 | How much time do you plan to commit per week? | e.g. "8-10", "11-15", "16-20", "20-22" |
| 12 | Grade | |
| 13 | GPA (100 or 4.0)? | **Engineering & SE** – numeric or % |
| 13 | GPA (100)? | **Medicine only** – different header |
| 14 | Telegram user name (@your user name)? | |
| 15 | Where did you hear about this program? | **New** – not in old Google Form |
| 16 | Do you follow us: https://www.linkedin.com/company/ethioware/ | Trailing non‑breaking space (`\xa0`) in export |

**Where did you hear about this program?** → In Silver, map free-text responses to a **standard category**. Store both the raw response (optional) and the category. Standard categories: **`social_media`**, **`word_of_mouth`**, **`other`**. Add more categories (e.g. `website`, `school`, `telegram`) as needed; ETL maps known phrases to these values and defaults unmapped to `other`.

**Target pipeline schema:** registration_id, start_time, completion_time, last_modified_time, full_name_raw, email_canonical (from Email2), highschool_name, citizenship, commitment_per_week, grade, gpa_4_scale, telegram_username, **where_heard_category** (standard: social_media, word_of_mouth, other), linkedin_follow, **program_selection** (from filename: Engineering Basics, Medicine Basics, SE Basics, Law Basics when added), cohort_name (from filename), source_file, ingestion_time.

---

## Updated LinkedIn format (from `Datasets/marketing/linkedin/`)

The **updated** LinkedIn exports are in **`Datasets/marketing/linkedin/`**. There are **three Excel files** with different schemas (followers, visitors, competitor analytics). The older `linkedin-cleaned.csv` (Impressions, Clicks, Reactions, Comments, Reposts, Engagement rate) is also in **`marketing/linkedin/linkedin-cleaned.csv`**; the new files add **followers** and **visitors** (page views by device).

**Files:**

1. **ethioware_followers_*.xls** – follower counts by source  
2. **ethioware_visitors_*.xls** – page views and unique visitors by page and device  
3. **Ethioware_EdTech_Initiative_competitor_analytics_*.xlsx** – competitor analytics (first row may be dates; layout differs)

### LinkedIn – Followers (ethioware_followers_*.xls)

| # | Column name (exact) | Notes |
|---|---------------------|--------|
| 1 | Date | |
| 2 | Sponsored followers | |
| 3 | Organic followers | |
| 4 | Auto-invited followers | |
| 5 | Total followers | |

### LinkedIn – Visitors (ethioware_visitors_*.xls)

| # | Column name (exact) | Notes |
|---|---------------------|--------|
| 1 | Date | |
| 2 | Overview page views (desktop) | |
| 3 | Overview page views (mobile) | |
| 4 | Overview page views (total) | |
| 5 | Overview unique visitors (desktop) | |
| 6 | Overview unique visitors (mobile) | |
| 7 | Overview unique visitors (total) | |
| 8 | Life page views (desktop) | |
| 9 | Life page views (mobile) | |
| 10 | Life page views (total) | |
| 11 | Life unique visitors (desktop) | |
| 12 | Life unique visitors (mobile) | |
| 13 | Life unique visitors (total) | |
| 14 | Jobs page views (desktop) | |
| 15 | Jobs page views (mobile) | |
| 16 | Jobs page views (total) | |
| 17 | Jobs unique visitors (desktop) | |
| 18 | Jobs unique visitors (mobile) | |
| 19 | Jobs unique visitors (total) | |
| 20 | Total page views (desktop) | |
| 21 | Total page views (mobile) | |
| 22 | Total page views (total) | |
| 23 | Total unique visitors (desktop) | |
| 24 | Total unique visitors (mobile) | |
| 25 | Total unique visitors (total) | |

### LinkedIn – Competitor analytics (Ethioware_EdTech_Initiative_competitor_analytics_*.xlsx)

First row in the export appears to be dates; layout is matrix-style. **Silver:** Ingest into **`silver_marketing.linkedin_competitor_analytics`** (or similar). Design with **competitor as a dimension** so more competitors can be added in the future (e.g. `competitor_id` / `competitor_name`). Updated **less frequently** than followers/visitors; same Bronze → Silver pattern, with optional `report_date` and one row per competitor per metric per date when the exact layout is fixed.

---

## Session Feedback Form – expert rating (from `Datasets/trainings/feedback/Session Feedback Form.xlsx`)

**Purpose:** Experts/mentors rate the session after sharing their experience. **Less frequent** than other feedback; **expert rating is useful on the dashboard.**

**Source:** Microsoft Form/Excel. File: **`Datasets/trainings/feedback/Session Feedback Form.xlsx`** (single sheet).

| # | Column name (exact in export) | Notes |
|---|-------------------------------|--------|
| 1 | ID | Submission ID |
| 2 | Start time | TIMESTAMP |
| 3 | Completion time | TIMESTAMP |
| 4 | Email | System; often "anonymous" |
| 5 | Name | System; often empty (NaN) |
| 6 | Last modified time | May be NaN |
| 7 | **Rating** | **Expert rating – general experience** (e.g. Excellent, Good) |
| 8 | In a single sentence, what did you like most when sharing your experience? | Long text (header may contain `\xa0` between "most" and "when") |
| 9 | In a single sentence, what did you least liked about the session? | Long text |
| 10 | What things you wish were added/ removed from the sessions? | Long text |
| 11 | Was the training time convenient for you (the duration and the starting time)? | Yes/No |
| 12 | **Rating2** | **Recommendation likelihood** (e.g. Very likely, Somewhat likely, Very unlikely) |

**Silver:** Load into `silver_trainings.feedback` with **feedback_type** = `expert` or `session_feedback`. Store **Rating** and **Rating2** for dashboard (expert rating widgets). Optional: add sentiment via NLP for text fields; less frequent updates.

---

### Assumptions

1. **Registration:** **Microsoft Form only** for new ingestion. Exports in **`Datasets/trainings/registration/`**, one per program (Engineering, Medicine, SE; Law uses same schema when added). Program from **filename**; **Email2**; **Last modified time**; **Where did you hear about this program?** → map to standard category in Silver (social_media, word_of_mouth, other).
2. **Email/identity:** The canonical email field (whatever it is named in the Microsoft Form) is used for `learner_id`; system Email/Name are redundant when sign-in is not required.
3. **GPA:** The intent is a single 4.0-scale value in analytics; 100-scale and percentage are legacy and can be mapped or stored as raw + normalized.
4. **LinkedIn:** The question is a simple Yes/No; the URL in the header is only for respondent convenience and should not appear in the stored column name.
5. **Feedback forms:** “Mentor” = trainers/volunteers giving feedback about their session; “Trainee” = learners giving feedback about the training. There is one trainee feedback form (Engineering basics) in the dataset; Medicine or other fields may have separate forms not yet seen.
6. **Trainee feedback anonymity:** Missing Id/Start/Completion time in the trainee raw export was assumed to be due to anonymous collection or export choice, not a different form type.
7. **Score sheets:** They are Google Sheets (or similar) exports, not the same Forms used for registration; column differences between November and May are due to different sheet designs per cohort.
8. **Sentiment:** All sentiment in the cleaned CSVs was added after export (manual or script), not collected in the form; future runs can use Cloud Natural Language API for new rows.
9. **Timezone:** Form timestamps were assumed to be in a single timezone (e.g. Africa/Addis_Ababa); no timezone field was seen in the export.
10. **Controlled vocabulary:** Citizenship and Grade were assumed to benefit from a fixed set of values; the exact list was inferred from the sample data only.

### Follow-up questions to clarify

- **Registration**
  - Do you want **cohort** and **program** to be **explicit form questions** in the Microsoft Form, or is program already a dropdown (Software Engineering / Medicine / Engineering / Law)?
  - Can a learner select **more than one program** in the same submission (e.g. both Engineering and Software Engineering)? If yes, we store multiple rows in `bridge_learner_field`.
  - For **duplicate submissions** (same email, two responses): keep **first** submission, **latest**, or **both** with a flag?
  - What **timezone** should we store for Start/Completion time (e.g. Africa/Addis_Ababa, UTC)?
  - Should **GPA** be stored only as 4.0 scale, or also keep raw (100 or %) for audit?

- **Feedback**
  - Is there a **Medicine Basics** (or other field) **trainee feedback** form? If yes, is it the same questions as Engineering basics or different?
  - For **mentor** feedback: do you need to know **which cohort/session** each response refers to? If yes, will that be added as a form question or from filename/context?
  - Should **sentiment** be computed only for new rows (NLP API) or also backfilled for historical rows that don’t have it?

- **Score sheets**
  - Are score sheets always **manually** filled/exported from Sheets, or will there be a **form** or **API** for scores in the future?
  - For “**Both**” (multi-field): should we treat that as two rows (one per field) in Silver/Gold, or one row with a special field code?

- **General**
  - Will any form **add or remove questions** soon? If yes, how should the pipeline handle **schema changes** (reject, alert, or new version)?
  - Are there any **other forms** used for trainings (e.g. feedback per program, attendance, drop-out) that we should document?

---

## 1. Learner registration (Microsoft Form only)

**Source:** Microsoft Form only. Exports in **`Datasets/trainings/registration/`** – one Excel per program (Engineering Basics, Medicine Basics, SE Basics). **Law** uses the same schema when added (no Law export yet). Program and cohort from **filename**. Google Form registration is **not used** for new ingestion.

### 1.1 Sources

| Source | Path (example) |
|--------|----------------|
| Microsoft Form – Engineering | `trainings/registration/Enginerring_Basics_Registration Early_registration_for_April_cohort1.xlsx` |
| Microsoft Form – Medicine | `trainings/registration/Medicine_Basics_Registration_Early_registration_for_April_cohort1.xlsx` |
| Microsoft Form – SE | `trainings/registration/SE_Basics_Registration Early_registration_for_April_cohort1_171.xlsx` |
| Law (when added) | Same 16-column schema; add file to `trainings/registration/` |

### 1.2 Cleaning rules (apply before or in Silver ETL)

- **Canonical email:** Use **Email2** (not Email1); trim, lowercase for `learner_id`.
- **Where did you hear about this program?** Map free-text to **standard category** in Silver: **`social_media`**, **`word_of_mouth`**, **`other`**. Add more categories (e.g. `website`, `school`, `telegram`) as needed; unmapped → `other`.
- **GPA:** Unify to 4.0 scale in Silver; map 100-scale if needed.
- **LinkedIn:** Strip URL from header; store Yes/No as 1/0.
- **Timestamps:** Normalize format and timezone.
- **Citizenship / Grade:** Trim; controlled vocabulary optional.
- **Deduplication:** Use Email2 (and optionally Full Name); keep first or latest by business rule.

### 1.3 Target schema for Silver (registrations)

| Column | Type | Required | Notes |
|--------|------|----------|--------|
| `registration_id` | STRING | Yes | From Form `ID` |
| `start_time` | TIMESTAMP | Yes | From `Start time`, normalized |
| `completion_time` | TIMESTAMP | Yes | From `Completion time`, normalized |
| `last_modified_time` | TIMESTAMP | No | From `Last modified time` |
| `full_name_raw` | STRING | Yes | From `Full Name` (PII) |
| `email_canonical` | STRING | Yes | From **Email2**, trimmed, lowercased (for `learner_id`) |
| `highschool_name` | STRING | No | From `Highschool Name` |
| `citizenship` | STRING | No | Normalized |
| `commitment_per_week` | STRING | No | e.g. "8-10", "11-15", "16-20", "20-22" |
| `grade` | STRING | No | Normalized (trim, controlled set) |
| `gpa_4_scale` | FLOAT64 | No | 0–4 (reject or map if out of range) |
| `telegram_username` | STRING | No | From Telegram question |
| **`where_heard_category`** | STRING | No | **Standard:** `social_media`, `word_of_mouth`, `other` (map from "Where did you hear about this program?") |
| `linkedin_follow` | INT64 / BOOL | No | 1 = Yes, 0 = No |
| `cohort_name` | STRING | No | From filename (e.g. April cohort) |
| `field_selection` | STRING | No | From filename: Engineering Basics, Medicine Basics, SE Basics, Law Basics (when added) |
| `source_file` | STRING | Yes | Audit |
| `ingestion_time` | TIMESTAMP | Yes | Audit |

---

## 2. Mentor feedback form (Session feedback from the mentors)

### 2.1 Source

- **Raw:** `SessionFeedbackFromTheMentors_raw.csv`
- **Cleaned (with sentiment):** `SessionFeedbackFromTheMentors_clean_data_sentiment.csv`  
  Sentiment is **added in post-processing** (Attribute/Value); not in the original form.

### 2.2 Raw Google Form export columns

| Column (exact) | Type | Response values (examples) |
|----------------|------|----------------------------|
| `Id` | System | Integer |
| `Start time` | System | e.g. `6/30/2025 19:24` |
| `Completion time` | System | Same format |
| `Email` | System | "anonymous" in current data |
| `How do you rate your general experience?.Rating` | Scale | **Excellent**, Good |
| `In a single sentence, what did you like most when sharing your experience?` | Long text | Free text |
| `In a single sentence, what did you least liked about the session?` | Long text | Free text |
| `What things you wish were added/ removed from the sessions?` | Long text | Free text |
| `Was the training time convenient for you (the duration and the starting time)?` | Yes/No | **Yes**, No |
| `How likely are you to recommend other trainers to volunteer and share their journey?.Rating` | Scale | **Very likely**, Somewhat likely |

### 2.3 Cleaning rules

- **Ratings:** Map to numeric if needed (e.g. Excellent=5, Good=4; Very likely=5, Somewhat likely=4). Current cleaned uses 3–5.
- **Timestamps:** Normalize format and timezone.
- **Sentiment:** Not in form; add in ETL (Cloud Natural Language API) or keep in separate sentiment table keyed by feedback_id + question. Cleaned file uses Attribute/Value (e.g. "How do you rate your general experience Sentiment", "Neutral").
- **Encoding:** Fix `_x0092_`-style escapes (e.g. people’s → people_x0092_s) to proper apostrophe/Unicode in text fields.

### 2.4 Target schema (feedback – mentor)

| Column | Type | Notes |
|--------|------|--------|
| `feedback_id` | STRING | From Form `Id` |
| `start_time`, `completion_time` | TIMESTAMP | Normalized |
| `feedback_type` | STRING | e.g. "mentor" |
| `rating_general_experience` | INT64 or STRING | 1–5 or keep scale label |
| `text_like_most` | STRING | |
| `text_least_liked` | STRING | |
| `text_wish_added_removed` | STRING | |
| `training_time_convenient` | BOOL/INT | Yes=1, No=0 |
| `rating_recommend_trainers` | INT64 or STRING | |
| `sentiment_label` | STRING | From post-processing (e.g. Positive, Neutral, Negative) |
| `sentiment_score` | FLOAT64 | Optional |
| `model_version` | STRING | If from NLP API |
| `source_file`, `ingestion_time` | STRING, TIMESTAMP | Audit |

---

## 3. Trainee feedback form (Anonymous rating – e.g. Engineering basics)

### 3.1 Source

- **Raw:** `Anonymous_rating_Engineering_basics_raw.csv`
- **Cleaned (with sentiment):** `Anonymous_rating_Engineering_basics_clean_data_sentiment.csv`  
  **No Id / Start time / Completion time** in raw – form may be anonymous and not collect timestamps, or they were dropped.

### 3.2 Raw Google Form export columns

| Column (exact) | Type | Response values (examples) |
|----------------|------|----------------------------|
| `How do you rate your general experience?.Rating1` | Scale | **Excellent**, Good |
| `What things you wish were added/ removed from the training?1` | Long text | Free text |
| `Was the training time convenient for you (the duration and the starting time)?1` | Yes/No | **Yes**, No |
| `How much relevant information did you get?.Rating` | Scale | **Very Relevant**, Somewhat Relevant |
| `In a single sentence, what did you like most about the training?` | Long text | Free text |
| `In a single sentence, what did you least like about the training?` | Long text | Free text |
| `How likely are you to recommend other trainees to join?.Rating` | Scale | **Very likely**, Somewhat likely |

Note: Suffix **`.Rating1`** or **`?1`** appears when the form has multiple sections or duplicate question titles; keep one canonical name in schema.

### 3.3 Cleaning rules

- **Unify question names** with mentor form where possible (e.g. same "rating_general_experience", "text_like_most", "text_least_liked") so one Silver `feedback` table can hold both.
- **Generate feedback_id** if missing (e.g. hash of row or UUID per submission).
- **Ratings:** Map to numeric (Excellent=5, Good=4; Very Relevant=5, Somewhat Relevant=4; Very likely=5, Somewhat likely=4).
- **Sentiment:** Same as mentor – post-process; store in Attribute/Value or separate columns with `model_version`.

### 3.4 Target schema (feedback – trainee)

Same logical shape as mentor feedback; use `feedback_type` = "trainee" and optional `cohort_id` / `field_id` from context:

- Same columns as §2.4, with optional `cohort_name`, `field_name` (e.g. "Engineering Basics") from form or filename.

---

## 4. Score sheets (Sheets/CSV – not Forms)

Score data is **not** collected via the same Google Forms; it is exported from **Google Sheets** or similar (manual/CSV upload). Schemas differ by cohort. Document in **schema.md**; for “form formats” we only note:

- **November score sheet:** Columns include Name, Email Address, User name, Cohort, Quiz score, Quiz percentage, Khan Academy score, Learning Minutes (with comma decimals), KA Score, %KA, Total points, Rank. Values like "Both" for Cohort; numeric fields may have commas.
- **May cohort scores:** Name, User-name, Cohort, Quiz score, Quiz percentage, Khan Academy score, Relative % to the top scorer, Average, Rank (no Email in export).

Standardize column names and numeric parsing (strip commas, one scale) in Silver; see **schema.md** and ETL plan.

---

## 5. Checklist before implementation

- [ ] **Registration:** Use Microsoft Form columns from `trainings/registration/` (Email2, Last modified time, Where did you hear…). Unify GPA and LinkedIn in ETL; normalize Citizenship and Grade; timestamps to one format/timezone.
- [ ] **Registration:** Normalize Citizenship and Grade (trim, controlled vocabulary); timestamps to one format/timezone.
- [ ] **Registration:** Decide deduplication rule (first vs latest per email) and document.
- [ ] **Feedback (both):** Decide canonical question names and numeric mapping for scales; fix encoding (e.g. `_x0092_`) in text.
- [ ] **Feedback:** Ensure one Silver `feedback` schema can hold both mentor and trainee with `feedback_type` and optional cohort/field.
- [ ] **Score sheets:** Keep as Sheets/CSV; document both November and May schemas in schema.md and handle in scores ingestion (column mapping, comma stripping, dedupe).

Once the above are applied, form exports will be as clean and consistent as possible for Silver ingestion.

---

## Follow-up questions for clarity

1. For **duplicate submissions** (same email): keep **first**, **latest**, or **both** with a flag?
2. **Timezone** for Start/Completion time (e.g. Africa/Addis_Ababa, UTC)?
3. **GPA:** store only 4.0 scale or also keep raw (100/%) for audit?
4. **Feedback:** which cohort/session for mentor feedback; sentiment for new rows only or backfill?
5. **Score sheets:** "Both" → one row vs two rows per field in Silver?
