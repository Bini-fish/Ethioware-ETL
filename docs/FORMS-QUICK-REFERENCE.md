# Forms – quick reference (column names)

One-page view of **every form** and the **exact column names** as they appear in the export. **Registration: Microsoft Form only** (programs: Software Engineering, Medicine, Engineering, Law). **Law** uses the same schema when its export is added. Feedback forms are still Google Forms.

---

## Registration – Microsoft Form (current)

**Purpose:** Register for Engineering Basics, Medicine Basics, or SE (Software Engineering) Basics. **Law** uses the same 16 columns when added (no Law export yet).  
**Source:** Microsoft Form only; one Excel per program in **`Datasets/trainings/registration/`**. Program and cohort from **filename**.

| # | Column name (exact in export) |
|---|-------------------------------|
| 1 | ID |
| 2 | Start time |
| 3 | Completion time |
| 4 | Email |
| 5 | Name |
| 6 | Last modified time |
| 7 | Full Name |
| 8 | Email2 |
| 9 | Highschool Name |
| 10 | Citizenship |
| 11 | How much time do you plan to commit per week? |
| 12 | Grade |
| 13 | GPA (100 or 4.0)? *(Engineering, SE)* or GPA (100)? *(Medicine)* |
| 14 | Telegram user name (@your user name)? |
| 15 | Where did you hear about this program? |
| 16 | Do you follow us: https://www.linkedin.com/company/ethioware/ *(trailing space)* |

---

## Form 1: Engineering Basics – Learner Registration *(historical)*

**Purpose:** Register for Engineering Basics cohort *(historical; see Microsoft Form above for current)*.  
**Export example:** `Engineering_Basics_Learner_Registration_raw.csv`

| # | Column name (exact in export) |
|---|-------------------------------|
| 1 | Id |
| 2 | Start time |
| 3 | Completion time |
| 4 | Email |
| 5 | Name |
| 6 | Full Name |
| 7 | Email1 |
| 8 | Highschool Name |
| 9 | Citizenship |
| 10 | How much time do you plan to commit per week? |
| 11 | Grade |
| 12 | GPA (100 or 4.0)? |
| 13 | Telegram user name (@your user name)? |
| 14 | Do you follow us: https://www.linkedin.com/company/ethioware/  *(trailing space)* |

---

## Form 2: Medicine Basics – Learner Registration *(historical)*

**Purpose:** Register for Medicine Basics cohort *(historical; see Microsoft Form above for current)*.  
**Export example:** `Medicine_Basics_Learner_Registration_raw.csv`

| # | Column name (exact in export) |
|---|-------------------------------|
| 1 | Id |
| 2 | Start time |
| 3 | Completion time |
| 4 | Email |
| 5 | Name |
| 6 | Full Name |
| 7 | Email1 |
| 8 | Highschool Name |
| 9 | Citizenship |
| 10 | How much time do you plan to commit per week? |
| 11 | Grade |
| 12 | **GPA (100)?**  *(different from Engineering)* |
| 13 | Telegram user name (@your user name)? |
| 14 | Do you follow us: https://www.linkedin.com/company/ethioware/  *(trailing space)* |

**Difference from Form 1:** Column 12 is “GPA (100)?” instead of “GPA (100 or 4.0)?.”

---

## Session Feedback Form – expert rating (current)

**Purpose:** Experts/mentors rate the session. **Less frequent**; **expert rating (Rating, Rating2) is useful on the dashboard.**  
**Source:** Microsoft Form/Excel. **Path:** `Datasets/trainings/feedback/Session Feedback Form.xlsx`

| # | Column name (exact in export) |
|---|-------------------------------|
| 1 | ID |
| 2 | Start time |
| 3 | Completion time |
| 4 | Email |
| 5 | Name |
| 6 | Last modified time |
| 7 | Rating |
| 8 | In a single sentence, what did you like most when sharing your experience? *(may have \\xa0 in header)* |
| 9 | In a single sentence, what did you least liked about the session? |
| 10 | What things you wish were added/ removed from the sessions? |
| 11 | Was the training time convenient for you (the duration and the starting time)? |
| 12 | Rating2 |

**Response examples:** Rating = Excellent, Good; Rating2 = Very likely, Somewhat likely, Very unlikely; Convenient = Yes, No.

---

## Form 3: Session feedback from the mentors *(historical – Google Form)*

**Purpose:** Mentors/trainers rate the session after sharing their experience.  
**Export example:** `SessionFeedbackFromTheMentors_raw.csv`

| # | Column name (exact in export) |
|---|-------------------------------|
| 1 | Id |
| 2 | Start time |
| 3 | Completion time |
| 4 | Email |
| 5 | How do you rate your general experience?.Rating |
| 6 | In a single sentence, what did you like most when sharing your experience? |
| 7 | In a single sentence, what did you least liked about the session? |
| 8 | What things you wish were added/ removed from the sessions? |
| 9 | Was the training time convenient for you (the duration and the starting time)? |
| 10 | How likely are you to recommend other trainers to volunteer and share their journey?.Rating |

**Response examples:** Rating = Excellent, Good; Convenient = Yes, No; Recommend = Very likely, Somewhat likely.

---

## Form 4: Anonymous rating – Engineering basics (trainee feedback)

**Purpose:** Trainees rate the Engineering Basics training (anonymous).  
**Export example:** `Anonymous_rating_Engineering_basics_raw.csv`

| # | Column name (exact in export) |
|---|-------------------------------|
| 1 | How do you rate your general experience?.Rating1 |
| 2 | What things you wish were added/ removed from the training?1 |
| 3 | Was the training time convenient for you (the duration and the starting time)?1 |
| 4 | How much relevant information did you get?.Rating |
| 5 | In a single sentence, what did you like most about the training? |
| 6 | In a single sentence, what did you least like about the training? |
| 7 | How likely are you to recommend other trainees to join?.Rating |

**Note:** No Id, Start time, or Completion time in this export. Response examples: General experience = Excellent, Good; Relevant = Very Relevant, Somewhat Relevant; Recommend = Very likely, Somewhat likely.

---

## Not forms (for context)

- **Score sheets** (November, May): Google Sheets exports; see `schema.md` for column names.
- **Khan Academy activity:** CSV export from KA/Sheets; see `schema.md`.
- **Cohort registration:** Aggregated table; not a form.

---

## LinkedIn – new exports (`Datasets/marketing/linkedin/`)

| File pattern | Columns (exact) |
|--------------|-----------------|
| **ethioware_followers_*.xls** | Date, Sponsored followers, Organic followers, Auto-invited followers, Total followers |
| **ethioware_visitors_*.xls** | Date; Overview/Life/Jobs page views (desktop, mobile, total) and unique visitors; Total page views and Total unique visitors (desktop, mobile, total) – 25 columns total |
| **Ethioware_EdTech_Initiative_competitor_analytics_*.xlsx** | First row dates; layout matrix-style – see schema.md |

---

## Summary

| Form | Short name | Columns in export |
|------|------------|-------------------|
| **Registration – Microsoft Form** | Reg (current) | 16 – trainings/registration/. **where_heard** → Silver category: social_media, word_of_mouth, other. Law = same schema when added. |
| Engineering Basics – Learner Registration | Reg – Engineering (historical) | 14 (incl. Id, timestamps, Email, Name, Full Name, Email1, school, citizenship, commitment, grade, GPA, Telegram, LinkedIn) |
| Medicine Basics – Learner Registration | Reg – Medicine | 14 (same except GPA header: “GPA (100)?”) |
| **Session Feedback Form** | Feedback – Expert | 12 – trainings/feedback/Session Feedback Form.xlsx. **Rating**, **Rating2** for dashboard. Less frequent. |
| Session feedback from the mentors | Feedback – Mentor *(historical)* | 10 (Google Form) |
| Anonymous rating – Engineering basics | Feedback – Trainee | 7 (no Id/timestamps; 3 ratings + 3 text + convenient) |

For cleaning rules and target pipeline schema, see **GOOGLE-FORMS-FORMATS.md**.
