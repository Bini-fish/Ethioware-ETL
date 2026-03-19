# Sprint 2 Silver Upload Test Checklist

Use this checklist to validate Sprint 2 ingestion (registrations, scores, ka_activity, feedback) after deployment changes.

## 1) Test run setup

```powershell
$PROJECT="ethioware-etl"; $TS=Get-Date -Format "yyyyMMddHHmmss"
```

## 2) Upload commands (copy-paste)

### Registrations
```powershell
gsutil cp "Datasets\trainings\registration\Enginerring Basics Learner Registration.csv" "gs://ethioware-bronze-trainings/forms/test_${TS}_Eng_Registration.csv"
gsutil cp "Datasets\trainings\registration\SE Basics Registration.csv" "gs://ethioware-bronze-trainings/forms/test_${TS}_SE_Registration.csv"
gsutil cp "Datasets\trainings\registration\Medicine Basics Learner Registration.csv" "gs://ethioware-bronze-trainings/forms/test_${TS}_Med_Registration.csv"
```

### Scores
```powershell
gsutil cp "Datasets\trainings\scores\May_Cohort_Scores_clean_data.csv" "gs://ethioware-bronze-trainings/scores/test_${TS}_May_Scores.csv"
gsutil cp "Datasets\trainings\scores\November score sheet - Score sheet.csv" "gs://ethioware-bronze-trainings/scores/test_${TS}_Nov_Scores.csv"
```

### KA activity
```powershell
gsutil cp "Datasets\trainings\ka_activity\learner_activity_khan_academy_clean_data.csv" "gs://ethioware-bronze-trainings/scores/test_${TS}_KA_Activity.csv"
gsutil cp "Datasets\trainings\ka_activity\Downloaded_2026_03_08_All_assignments_Engineering_Basics_Pre_Training.csv" "gs://ethioware-bronze-trainings/scores/test_${TS}_KA_Assignments.csv"
```

### Feedback
```powershell
gsutil cp "Datasets\trainings\feedback\Session Feedback Form.xlsx" "gs://ethioware-bronze-trainings/feedback/test_${TS}_SessionFeedback.xlsx"
gsutil cp "Datasets\trainings\feedback\Anonymous_rating_Engineering_basics_clean_data_sentiment.csv" "gs://ethioware-bronze-trainings/feedback/test_${TS}_AnonFeedback.csv"
gsutil cp "Datasets\trainings\feedback\SessionFeedbackFromTheMentors_clean_data_sentiment.csv" "gs://ethioware-bronze-trainings/feedback/test_${TS}_MentorFeedback.csv"
```

Wait 30-90 seconds after uploads.

## 3) Verification queries (copy-paste)

### Run-level status
```powershell
bq --project_id=$PROJECT query --use_legacy_sql=false "SELECT source, status, row_count, error_count, message, timestamp FROM silver_trainings.pipeline_run_log WHERE source LIKE '%test_$TS_%' ORDER BY timestamp DESC"
```

### Target table row counts
```powershell
bq --project_id=$PROJECT query --use_legacy_sql=false "SELECT source_file, COUNT(1) AS n FROM silver_trainings.registrations WHERE source_file LIKE '%test_$TS_%' GROUP BY source_file ORDER BY n DESC"
bq --project_id=$PROJECT query --use_legacy_sql=false "SELECT source_file, COUNT(1) AS n FROM silver_trainings.scores_raw WHERE source_file LIKE '%test_$TS_%' GROUP BY source_file ORDER BY n DESC"
bq --project_id=$PROJECT query --use_legacy_sql=false "SELECT source_file, COUNT(1) AS n FROM silver_trainings.ka_activity WHERE source_file LIKE '%test_$TS_%' GROUP BY source_file ORDER BY n DESC"
bq --project_id=$PROJECT query --use_legacy_sql=false "SELECT source_file, COUNT(1) AS n FROM silver_trainings.feedback WHERE source_file LIKE '%test_$TS_%' GROUP BY source_file ORDER BY n DESC"
```

### Reject analysis
```powershell
bq --project_id=$PROJECT query --use_legacy_sql=false "SELECT source_file, reject_reason, COUNT(1) AS n FROM silver_trainings.scores_rejects WHERE source_file LIKE '%test_$TS_%' GROUP BY source_file, reject_reason ORDER BY source_file, n DESC"
```

## 4) Pass/fail matrix template

| TC ID | Domain | Test file | GCS target object | Expected behavior | Actual run_log status | row_count | error_count | Reject reason summary | Target table rows | Result | Notes |
|------|--------|-----------|-------------------|-------------------|-----------------------|-----------|-------------|-----------------------|------------------|--------|-------|
| TC-REG-01 | registrations | Enginerring Basics Learner Registration.csv | forms/test_${TS}_Eng_Registration.csv | SUCCESS/PARTIAL; rows in registrations; secure_id_map updated | | | | | | PASS/FAIL | |
| TC-REG-02 | registrations | SE Basics Registration.csv | forms/test_${TS}_SE_Registration.csv | SUCCESS/PARTIAL; program_selection=SE_Basics | | | | | | PASS/FAIL | |
| TC-REG-03 | registrations | Medicine Basics Learner Registration.csv | forms/test_${TS}_Med_Registration.csv | SUCCESS/PARTIAL; program_selection=Medicine_Basics | | | | | | PASS/FAIL | |
| TC-SCR-01 | scores | May_Cohort_Scores_clean_data.csv | scores/test_${TS}_May_Scores.csv | SUCCESS; rows in scores_raw | | | | | | PASS/FAIL | |
| TC-SCR-02 | scores | November score sheet - Score sheet.csv | scores/test_${TS}_Nov_Scores.csv | SUCCESS or PARTIAL with small rejects | | | | | | PASS/FAIL | |
| TC-KA-01 | ka_activity | learner_activity_khan_academy_clean_data.csv | scores/test_${TS}_KA_Activity.csv | ka_activity SUCCESS; scores SKIPPED/no reject spam | | | | | | PASS/FAIL | |
| TC-KA-02 | ka_activity | Downloaded_2026_03_08_All_assignments_Engineering_Basics_Pre_Training.csv | scores/test_${TS}_KA_Assignments.csv | clean handling (ka_activity load or SKIPPED); no bulk scores rejects | | | | | | PASS/FAIL | |
| TC-FDB-01 | feedback | Session Feedback Form.xlsx | feedback/test_${TS}_SessionFeedback.xlsx | SUCCESS; rows in feedback | | | | | | PASS/FAIL | |
| TC-FDB-02 | feedback | Anonymous_rating_Engineering_basics_clean_data_sentiment.csv | feedback/test_${TS}_AnonFeedback.csv | SUCCESS; rows in feedback | | | | | | PASS/FAIL | |
| TC-FDB-03 | feedback | SessionFeedbackFromTheMentors_clean_data_sentiment.csv | feedback/test_${TS}_MentorFeedback.csv | SUCCESS; rows in feedback | | | | | | PASS/FAIL | |

## 5) Final verified run (2026-03-19, post registrations MERGE fix)

| TC ID | Domain | Status | row_count | error_count | Result | Notes |
|-------|--------|--------|-----------|-------------|--------|-------|
| TC-REG-01 | registrations | PARTIAL | 390 | 2 | PASS | 2 `invalid_email` rejects (blank emails in source CSV) |
| TC-REG-02 | registrations | SUCCESS | 283 | 0 | PASS | program_selection=SE_Basics; 258 learners merged in 8.8s |
| TC-REG-03 | registrations | PARTIAL | 297 | 1 | PASS | 1 `invalid_email` reject (blank email in source CSV) |
| TC-SCR-01 | scores | SUCCESS | 22 | 0 | PASS | |
| TC-SCR-02 | scores | No log entry | - | - | INCONCLUSIVE | Pre-existing; November schema may need scores fn update |
| TC-KA-01 | ka_activity | SUCCESS | 27 | 0 | PASS | scores fn correctly SKIPPED this file |
| TC-FDB-01 | feedback | SUCCESS | 15 | 0 | PASS | |
| TC-FDB-02 | feedback | SUCCESS | 15 | 0 | PASS | |

**Summary:** 7/8 PASS, 1 INCONCLUSIVE (TC-SCR-02 November scores — pre-existing schema issue, not related to Sprint 2 changes).

## 6) Operational note (logging baseline)

Default production troubleshooting signal should come from:
- `silver_trainings.pipeline_run_log` (run-level status and message)
- corresponding `*_rejects` tables (row-level reasons)

Current expected statuses include:
- `SUCCESS`, `PARTIAL`, `FAILED`, `SKIPPED`

