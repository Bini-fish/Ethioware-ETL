# Ethioware – CSV schema reference

Single reference for every CSV used in the pipeline. **Registration:** **Microsoft Form only**; exports in **`Datasets/trainings/registration/`** (Excel, one per program). **Law** uses the same schema when added (no Law file yet). **Where heard:** in Silver map to standard categories: **`social_media`**, **`word_of_mouth`**, **`other`**. **LinkedIn:** **`Datasets/marketing/linkedin/`** (followers, visitors, competitor analytics); competitor analytics → Silver with **competitor dimension** for future competitors. See **GOOGLE-FORMS-FORMATS.md** for form-specific cleaning.

Paths are relative to `Datasets/`. Layout: **trainings/** (registration, feedback, scores, ka_activity, cohort, legacy), **marketing/** (linkedin, youtube, web_analytics), **reference/** (Data_dictionary), **archive/** (old structure).

---

## 1. Trainings – Registrations (Microsoft Form only)

**Source:** Microsoft Form only. Google Form registration is not used for new ingestion.

| File | Path | Source |
|------|------|--------|
| Microsoft Form – Engineering | `trainings/registration/Enginerring_Basics_Registration Early_registration_for_April_cohort1.xlsx` | Microsoft Form |
| Microsoft Form – Medicine | `trainings/registration/Medicine_Basics_Registration_Early_registration_for_April_cohort1.xlsx` | Microsoft Form |
| Microsoft Form – SE | `trainings/registration/SE_Basics_Registration Early_registration_for_April_cohort1_171.xlsx` | Microsoft Form |
| Law (when added) | Same 16-column schema; add to `trainings/registration/` | Microsoft Form |

### Schema (cleaned registration – target for Silver)

**Microsoft Form export columns** (from `trainings/registration/` Excel files – one per program):

| Column | Type | Notes |
|--------|------|--------|
| ID | INT64/STRING | Submission ID (capital ID) |
| Start time | STRING (→ TIMESTAMP) | |
| Completion time | STRING (→ TIMESTAMP) | |
| Email | STRING | System; often "anonymous" |
| Name | STRING | System; often empty |
| Last modified time | STRING (→ TIMESTAMP) | New in Microsoft Form |
| Full Name | STRING | PII |
| Email2 | STRING | **PII; canonical for learner_id** (not Email1) |
| Highschool Name | STRING | Free text |
| Citizenship | STRING | |
| How much time do you plan to commit per week? | STRING | "8-10", "11-15", "16-20", "20-22" |
| Grade | STRING | |
| GPA (100 or 4.0)? or GPA (100)? | FLOAT64 | Engineering/SE vs Medicine header |
| Telegram user name (@your user name)? | STRING | |
| Where did you hear about this program? | STRING | Map in Silver to **where_heard_category**: `social_media`, `word_of_mouth`, `other` |
| Do you follow us: https://www.linkedin.com/company/ethioware/ | STRING | Yes/No; strip trailing \\xa0 |

Program and cohort from **filename**. Law uses same schema when added.

---

## 2. Trainings – Score sheets (Sheets/CSV)

| File | Path | Source |
|------|------|--------|
| November score sheet | `trainings/scores/November score sheet - Score sheet.csv` | Sheets/export |
| May cohort scores (raw) | `archive/Trainings_old/Trainings/raw_data/May_Cohort_Scores_raw.csv` | Sheets/export |
| May cohort scores (cleaned) | `trainings/scores/May_Cohort_Scores_clean_data.csv` | Cleaned |

### Schema A – November score sheet

| Column | Type | Notes |
|--------|------|--------|
| Name | STRING | Trailing spaces possible |
| Email Address | STRING | May have trailing space; some rows empty |
| User name | STRING | May have leading space (e.g. " Lidu@30") |
| Cohort | STRING | "Medicine Basics ", "Engineering Basics ", "Both " |
| Quiz score | FLOAT64 | e.g. 6.6 |
| Quiz percentage | STRING | e.g. "94.29%" – strip % for numeric |
| Khan Acadmy score | FLOAT64 | Typo in header |
| Learning Minutes | STRING | **Comma-separated decimals** e.g. "2,561.00", "256.00" |
| KA Score | FLOAT64 | e.g. 155.5 |
| %KA | STRING | e.g. "100.0%" |
| Total points | STRING | e.g. "97.1%" |
| Rank | INT64 | 1, 2, … |

**Parsing:** Strip commas from `Learning Minutes` before casting; blank/incomplete rows (e.g. duplicate name with empty scores) → rejects. Dedupe by (learner, cohort, field).

### Schema B – May cohort scores

| Column | Type | Notes |
|--------|------|--------|
| Name | STRING | Trailing space |
| User-name | STRING | No "Email" column in export |
| Cohort | STRING | "Medicine Basics", "Engineering Basics" |
| Quiz score | FLOAT64 | e.g. 6.644 |
| Quiz percentage | STRING | e.g. "94.91%" |
| Khan Academy score | INT64/FLOAT64 | e.g. 2200, 1600 |
| Relative % to the top scorer | INT64/FLOAT64 | e.g. 100, 93.18 |
| Average | FLOAT64 | e.g. 97.46 |
| Rank | INT64 | 1, 2, … |

Silver should support **both** schemas (column mapping or separate ingest paths) and output a unified `scores_raw` schema.

---

## 3. Trainings – Khan Academy activity (CSV export)

| File | Path | Source |
|------|------|--------|
| KA activity (cleaned) | `trainings/ka_activity/learner_activity_khan_academy_clean_data.csv` | KA/Sheets export |

### Schema

| Column | Type | Notes |
|--------|------|--------|
| student | STRING | Username or display name (map to learner_id where possible) |
| Total Learning minutes | INT64 | |
| skills worked on | INT64 | |
| skills leveled up | INT64 | |
| skills to improve | INT64 | |
| Attempted | INT64 | |
| Familiar | INT64 | |
| Proficient | INT64 | |
| Mastered | INT64 | |

Grain: one row per learner (per provider/period). No cohort in file; assign from context if needed.

---

## 4. Trainings – Feedback (Google Forms + Session Feedback Form Excel)

| File | Path | Source |
|------|------|--------|
| **Session Feedback Form (expert rating)** | `trainings/feedback/Session Feedback Form.xlsx` | Microsoft Form/Excel – **less frequent**; **expert rating for dashboard** |
| Mentor feedback (raw) | `archive/Trainings_old/Trainings/raw_data/SessionFeedbackFromTheMentors_raw.csv` | Google Forms |
| Mentor feedback (cleaned + sentiment) | `trainings/feedback/SessionFeedbackFromTheMentors_clean_data_sentiment.csv` | Cleaned + sentiment |
| Trainee feedback (raw) | `archive/Trainings_old/Trainings/raw_data/Anonymous_rating_Engineering_basics_raw.csv` | Google Forms |
| Trainee feedback (cleaned + sentiment) | `trainings/feedback/Anonymous_rating_Engineering_basics_clean_data_sentiment.csv` | Cleaned + sentiment |

### Schema – Session Feedback Form (expert rating) – `trainings/feedback/Session Feedback Form.xlsx`

| Column | Type | Notes |
|--------|------|--------|
| ID | INT64 | |
| Start time, Completion time | TIMESTAMP | |
| Email | STRING | "anonymous" |
| Name | STRING | Often empty |
| Last modified time | TIMESTAMP | May be null |
| **Rating** | STRING | **Expert rating – general experience** (Excellent, Good) – **for dashboard** |
| In a single sentence, what did you like most when sharing your experience? | STRING | May contain `\xa0` in header |
| In a single sentence, what did you least liked about the session? | STRING | |
| What things you wish were added/ removed from the sessions? | STRING | |
| Was the training time convenient for you (the duration and the starting time)? | STRING | Yes/No |
| **Rating2** | STRING | **Recommendation** (Very likely, Somewhat likely, Very unlikely) – **for dashboard** |

**Silver:** `silver_trainings.feedback` with **feedback_type** = `expert` or `session_feedback`. Expose **Rating** and **Rating2** (expert rating) in **dash_*** views for dashboard widgets. Less frequently updated.

### Schema – Mentor feedback (raw)

| Column | Type | Notes |
|--------|------|--------|
| Id | INT64 | |
| Start time, Completion time | STRING | |
| Email | STRING | "anonymous" |
| How do you rate your general experience?.Rating | STRING | "Excellent", "Good" |
| In a single sentence, what did you like most when sharing your experience? | STRING | Long text |
| In a single sentence, what did you least liked about the session? | STRING | Long text |
| What things you wish were added/ removed from the sessions? | STRING | Long text |
| Was the training time convenient for you (the duration and the starting time)? | STRING | "Yes", "No" |
| How likely are you to recommend other trainers to volunteer and share their journey?.Rating | STRING | "Very likely", "Somewhat likely" |

### Schema – Mentor feedback (cleaned + sentiment)

| Column | Type | Notes |
|--------|------|--------|
| How do you rate your general experience?.Rating | INT64 | 3, 4, 5 |
| How likely are you to recommend other trainers to volunteer and share their journey?.Rating | INT64 | 5, 4 |
| In a single sentence, what did you like most when sharing your experience? | STRING | |
| In a single sentence, what did you least liked about the session? | STRING | |
| What things you wish were added/ removed from the sessions? | STRING | |
| Attribute | STRING | e.g. "How do you rate your general experience Sentiment" |
| Value | STRING | "Neutral", "Positive", "Negative" |

Id/timestamps dropped in this cleaned version; sentiment is one row per question (Attribute/Value).

### Schema – Trainee feedback (raw)

| Column | Type | Notes |
|--------|------|--------|
| How do you rate your general experience?.Rating1 | STRING | "Excellent", "Good" |
| What things you wish were added/ removed from the training?1 | STRING | |
| Was the training time convenient for you (the duration and the starting time)?1 | STRING | "Yes", "No" |
| How much relevant information did you get?.Rating | STRING | "Very Relevant", "Somewhat Relevant" |
| In a single sentence, what did you like most about the training? | STRING | |
| In a single sentence, what did you least like about the training? | STRING | |
| How likely are you to recommend other trainees to join?.Rating | STRING | "Very likely", "Somewhat likely" |

No Id or timestamps in raw export.

### Schema – Trainee feedback (cleaned + sentiment)

| Column | Type | Notes |
|--------|------|--------|
| How do you rate your general experience?.Rating1 | INT64 | 5, 3 |
| How much relevant information did you get?.Rating | INT64 | 5, 4 |
| How likely are you to recommend other trainees to join?.Rating | INT64 | 5, 4 |
| In a single sentence, what did you like most about the training? | STRING | |
| In a single sentence, what did you least like about the training? | STRING | |
| What things you wish were added/ removed from the training?1 | STRING | |
| Attribute | STRING | e.g. "General experience Sentiment" |
| Value | STRING | "Positive", "Neutral" |

Multiple rows per submission (one per Attribute for sentiment). Unify with mentor schema in Silver using `feedback_type` and optional cohort/field.

---

## 5. Trainings – Cohort / aggregate and slides

| File | Path | Source |
|------|------|--------|
| Cohort registration | `trainings/cohort/Cohort registration.csv` | Aggregated (not raw form) |
| Feb cohort slides | `trainings/legacy/Feb_Cohort_Slides.csv` | Qualitative export |
| May cohort slides | `trainings/legacy/May_Cohort_Slides.csv` | Qualitative export |

### Schema – Cohort registration (aggregate)

| Column | Type | Notes |
|--------|------|--------|
| Cohort | STRING | "Nov", "May", "Jul" |
| Training Type | STRING | "EB", "MB" (Engineering/Medicine Basics) |
| Total Registrations | INT64 | |
| Total Enrolled | INT64 | |
| Conversion rate | FLOAT64 | |
| Conversion rate per cohort | FLOAT64 | |

Use for Gold aggregation or reporting; not a raw form schema.

### Schema – Feb / May cohort slides (qualitative)

Columns vary slightly between files. Typical: `Presenter Name`, `Presenter Background`, `Field Explored`, `Key Concepts`, `Challenges Encountered`, `How Challenges were Overcome`, `Future Aspirations`, `General Experience`, `Key Takeaway`, `Inspiration/Interest` (and May: `How They Learned about the Program`). Free text. Optional for pipeline; not in current ETL plan as a Silver table.

---

## 6. Social media – YouTube (platform export)

| File | Path | Source |
|------|------|--------|
| Summary | `marketing/youtube/YouTube Analytics - Summary.csv` | YouTube |
| Top Content | `marketing/youtube/YouTube Analytics - Top Content.csv` | YouTube |
| Top Content (48h) | `marketing/youtube/YouTube Analytics - Top Content (Last 48 Hours).csv` | YouTube |

### Schema – YouTube Summary

| Column | Type | Notes |
|--------|------|--------|
| Metric | STRING | "Total Views", "Watch Time (hours)", "Subscribers" |
| Value | STRING/INT64 | 7873, 514.3, 201 |

Key-value snapshot; store with report date and channel identifier.

### Schema – YouTube Top Content

| Column | Type | Notes |
|--------|------|--------|
| Content | STRING | Video/session title |
| Views | INT64 | |

Grain: one row per content item per report. "Last 48 Hours" variant same schema.

---

## 7. Social media – LinkedIn (platform export)

| File | Path | Source |
|------|------|--------|
| **New – Followers** | `marketing/linkedin/ethioware_followers_*.xls` | LinkedIn |
| **New – Visitors** | `marketing/linkedin/ethioware_visitors_*.xls` | LinkedIn |
| **New – Competitor analytics** | `marketing/linkedin/Ethioware_EdTech_Initiative_competitor_analytics_*.xlsx` | LinkedIn (matrix layout; updated less frequently) |
| LinkedIn (legacy) | `marketing/linkedin/linkedin-cleaned.csv` | LinkedIn |

**Silver:** Ingest competitor analytics into **`silver_marketing.linkedin_competitor_analytics`** with a **competitor dimension** for future competitors.

### Schema – New LinkedIn Followers (ethioware_followers_*.xls)

| Column | Type | Notes |
|--------|------|--------|
| Date | STRING (→ TIMESTAMP) | Store as UTC |
| Sponsored followers | INT64 | |
| Organic followers | INT64 | |
| Auto-invited followers | INT64 | |
| Total followers | INT64 | |

Grain: one row per day.

### Schema – New LinkedIn Visitors (ethioware_visitors_*.xls)

| Column | Type | Notes |
|--------|------|--------|
| Date | STRING (→ TIMESTAMP) | |
| Overview page views (desktop) | INT64 | |
| Overview page views (mobile) | INT64 | |
| Overview page views (total) | INT64 | |
| Overview unique visitors (desktop) | INT64 | |
| Overview unique visitors (mobile) | INT64 | |
| Overview unique visitors (total) | INT64 | |
| Life page views (desktop), (mobile), (total) | INT64 | |
| Life unique visitors (desktop), (mobile), (total) | INT64 | |
| Jobs page views (desktop), (mobile), (total) | INT64 | |
| Jobs unique visitors (desktop), (mobile), (total) | INT64 | |
| Total page views (desktop), (mobile), (total) | INT64 | |
| Total unique visitors (desktop), (mobile), (total) | INT64 | |

Grain: one row per day; 25 columns total.

### Schema – LinkedIn (legacy linkedin-cleaned.csv)

| Column | Type | Notes |
|--------|------|--------|
| Date | STRING (→ TIMESTAMP) | e.g. `2024-07-30 00:00:00` – store as UTC |
| Impressions (organic) | INT64 | |
| Impressions (sponsored) | INT64 | |
| Impressions (total) | INT64 | |
| Unique impressions (organic) | INT64 | |
| Clicks (organic), (sponsored), (total) | INT64 | |
| Reactions (organic), (sponsored), (total) | INT64 | |
| Comments (organic), (sponsored), (total) | INT64 | |
| Reposts (organic), (sponsored), (total) | INT64 | |
| Engagement rate (organic), (sponsored), (total) | FLOAT64 | |

Grain: one row per day. Standardize column names (e.g. snake_case) in Silver.

---

## 8. Social media – YouTube search & device (platform export)

| File | Path | Source |
|------|------|--------|
| Search Term Breakdown | `marketing/youtube/Search Term Breakdown.csv` | YouTube |
| Platform & Device | `marketing/youtube/Platform & Device.csv` | YouTube |

### Schema – Search Term Breakdown

| Column | Type | Notes |
|--------|------|--------|
| Search Term | STRING | e.g. "ethioware" |
| Views | STRING | e.g. "23", "< 15" – normalize or keep as string |

### Schema – Platform & Device

| Column | Type | Notes |
|--------|------|--------|
| Platform & Device | STRING | e.g. "Google Search - mobile" |
| Views (%) | STRING | e.g. "561 (67%)" – parse count and % if needed |

---

## 9. Web analytics (platform export)

| File | Path | Source |
|------|------|--------|
| Website by country | `marketing/web_analytics/website-cleaned.csv` | Web analytics |

### Schema

| Column | Type | Notes |
|--------|------|--------|
| name | STRING | Country name (e.g. "Ireland", "Ethiopia") |
| requests | INT64 | Request count |

Grain: one row per country per report period. Add report date in Silver if not in file.

---

## 10. Silver target summary (for pipeline)

| Domain | Silver table(s) | Primary source schemas |
|--------|------------------|------------------------|
| Trainings | registrations | §1 Microsoft Form; where_heard_category (social_media, word_of_mouth, other) |
| Trainings | scores_raw | §2A (November), §2B (May) – unified |
| Trainings | ka_activity | §3 |
| Trainings | feedback | §4 (Session Feedback Form **expert rating** for dashboard; mentor + trainee normalized) |
| Marketing | youtube_metrics_* | §6, §8 |
| Marketing | linkedin_metrics_*, linkedin_competitor_analytics | §7 (followers, visitors; competitor analytics with competitor dimension) |
| Web | analytics | §9 |

Use this document together with **GOOGLE-FORMS-FORMATS.md** for form cleaning and **Ethioware-ETL-Plan.md** for identity, PII, and Gold modeling.
