# Ethioware – IAM (custom roles, project- and dataset-level)

**Project:** `ethioware-etl`  
**Principle:** No public access. Custom roles by title; project-level for Data Engineer, dataset-level for Education Admin and BI/Marketing so they only see their data.

---

## 0. Canonical role-to-dataset mapping (reference)

| Role ID | Title | Who (placeholder) | Datasets / scope |
|---------|-------|-------------------|------------------|
| `projects/ethioware-etl/roles/ethiowareDataEngineer` | Ethioware Data Engineer | Data Engineer (1+ principals) | **Project** – full BigQuery, GCS, Cloud Functions, Logging |
| `projects/ethioware-etl/roles/ethiowareEducationAdmin` | Ethioware Education Admin | Education Admin (1+ principals) | `secure_core`, `silver_trainings`, `gold_trainings`, `dash_admin` only |
| `projects/ethioware-etl/roles/ethiowareBIMarketing` | Ethioware BI Marketing | BI/Marketing (1+ principals) | `silver_marketing`, `gold_marketing`, `dash_marketing`, `dash_board` only |

Use this table when implementing dashboards, authorized views, or access controls. Principals are configured locally (see §3); do not commit emails to the repo.

---

## 1. Role summary

| Role | Who | Access | Binding |
|------|-----|--------|---------|
| **Ethioware Data Engineer** | Pipeline operators | Full admin: BigQuery, GCS (Bronze), Cloud Functions, Logging | **Project** |
| **Ethioware Education Admin** | Staff who need individual student / PII view | BigQuery read + run queries on: `secure_core`, `silver_trainings`, `gold_trainings`, `dash_admin` | **Dataset** (only those 4) |
| **Ethioware BI Marketing** | Marketing / social media users | BigQuery read + run queries on: `silver_marketing`, `gold_marketing`, `dash_marketing`, `dash_board` | **Dataset** (only those 4) |

No role grants public or allUsers access.

---

## 2. Custom role definitions

### 2.1 Ethioware Data Engineer (project-level)

Full pipeline admin: create/manage datasets and tables, run jobs, read/write GCS Bronze buckets, deploy/invoke Cloud Functions, view logs.

**Permissions (custom role):**

```
bigquery.datasets.create
bigquery.datasets.get
bigquery.datasets.update
bigquery.tables.create
bigquery.tables.get
bigquery.tables.getData
bigquery.tables.updateData
bigquery.tables.delete
bigquery.jobs.create
bigquery.jobs.get
bigquery.jobs.list
storage.buckets.get
storage.buckets.list
storage.objects.create
storage.objects.delete
storage.objects.get
storage.objects.list
storage.objects.update
cloudfunctions.functions.create
cloudfunctions.functions.delete
cloudfunctions.functions.get
cloudfunctions.functions.invoke
cloudfunctions.functions.list
cloudfunctions.functions.update
logging.logEntries.list
resourcemanager.projects.get
```

### 2.2 Ethioware Education Admin (dataset-level)

Read tables and run queries (e.g. join `secure_core.secure_id_map` for PII). No write, no other datasets.

**Permissions (custom role):**

```
bigquery.datasets.get
bigquery.tables.get
bigquery.tables.getData
bigquery.jobs.create
bigquery.jobs.get
```

**Datasets this role is bound to:** `secure_core`, `silver_trainings`, `gold_trainings`, `dash_admin`.

### 2.3 Ethioware BI Marketing (dataset-level)

Read marketing/social media data and run queries. No trainings, no PII.

**Permissions (custom role):** Same as Education Admin:

```
bigquery.datasets.get
bigquery.tables.get
bigquery.tables.getData
bigquery.jobs.create
bigquery.jobs.get
```

**Datasets this role is bound to:** `silver_marketing`, `gold_marketing`, `dash_marketing`, `dash_board`.

---

## 3. Commands you run

**Important:** Run these locally or in Cloud Shell. Use your real principal emails only when executing; **do not commit** them or put them in the repo (the repo may be public). Docs keep placeholders only.

Replace:

- `PROJECT_ID` → `ethioware-etl`
- `DATA_ENGINEER_EMAIL` → e.g. `engineer@yourdomain.com`
- `EDUCATION_ADMIN_EMAIL` → e.g. `admin@yourdomain.com` (or a group: `group:ed-admins@yourdomain.com`)
- `BI_MARKETING_EMAIL` → e.g. `marketing@yourdomain.com`

### 3.1 Create the three custom roles

```bash
# Data Engineer
gcloud iam roles create ethiowareDataEngineer \
  --project=ethioware-etl \
  --title="Ethioware Data Engineer" \
  --description="Full pipeline admin: BigQuery, GCS Bronze, Cloud Functions, Logging" \
  --permissions=bigquery.datasets.create,bigquery.datasets.get,bigquery.datasets.update,bigquery.tables.create,bigquery.tables.get,bigquery.tables.getData,bigquery.tables.updateData,bigquery.tables.delete,bigquery.jobs.create,bigquery.jobs.get,bigquery.jobs.list,storage.buckets.get,storage.buckets.list,storage.objects.create,storage.objects.delete,storage.objects.get,storage.objects.list,storage.objects.update,cloudfunctions.functions.create,cloudfunctions.functions.delete,cloudfunctions.functions.get,cloudfunctions.functions.invoke,cloudfunctions.functions.list,cloudfunctions.functions.update,logging.logEntries.list,resourcemanager.projects.get \
  --stage=GA

# Education Admin
gcloud iam roles create ethiowareEducationAdmin \
  --project=ethioware-etl \
  --title="Ethioware Education Admin" \
  --description="Read access to student/PII datasets: secure_core, silver_trainings, gold_trainings, dash_admin" \
  --permissions=bigquery.datasets.get,bigquery.tables.get,bigquery.tables.getData,bigquery.jobs.create,bigquery.jobs.get \
  --stage=GA

# BI/Marketing
gcloud iam roles create ethiowareBIMarketing \
  --project=ethioware-etl \
  --title="Ethioware BI Marketing" \
  --description="Read access to marketing datasets: silver_marketing, gold_marketing, dash_marketing, dash_board" \
  --permissions=bigquery.datasets.get,bigquery.tables.get,bigquery.tables.getData,bigquery.jobs.create,bigquery.jobs.get \
  --stage=GA
```

### 3.2 Grant Data Engineer at project level

```bash
gcloud projects add-iam-policy-binding ethioware-etl \
  --member="user:DATA_ENGINEER_EMAIL" \
  --role="projects/ethioware-etl/roles/ethiowareDataEngineer"
```

### 3.3 Grant Education Admin on their datasets only

BigQuery dataset IAM is set per dataset. For each dataset, add the principal with the custom role. Using `bq`:

```bash
# Get current policy (repeat for each dataset), add the binding, then set it back.
# Option A: BigQuery Console – for each dataset (secure_core, silver_trainings, gold_trainings, dash_admin):
#   Open dataset → Sharing → Add principal → Principal = EDUCATION_ADMIN_EMAIL, Role = "Ethioware Education Admin" (project role).

# Use BigQuery Console (gcloud has no dataset-level IAM command for BigQuery)
```

**BigQuery Console (recommended):** for each of `secure_core`, `silver_trainings`, `gold_trainings`, `dash_admin` → **Share** → **Add principal** → principal = Education Admin user/group, role = **Ethioware Education Admin** (show “Project” roles and pick the custom one).

### 3.4 Grant BI/Marketing on their datasets only

**BigQuery Console:** for each of `silver_marketing`, `gold_marketing`, `dash_marketing`, `dash_board` → **Share** → **Add principal** → principal = BI/Marketing user/group, role = **Ethioware BI Marketing**.

---

## 4. Checklist

- [x] Create the three custom roles (3.1).
- [x] Grant **Ethioware Data Engineer** to the data engineer identity at project level (3.2).
- [x] Grant **Ethioware Education Admin** on `secure_core`, `silver_trainings`, `gold_trainings`, `dash_admin` only (3.3).
- [x] Grant **Ethioware BI Marketing** on `silver_marketing`, `gold_marketing`, `dash_marketing`, `dash_board` only (3.4).
- [ ] Confirm no principal has `allUsers` or `allAuthenticatedUsers` on the project or any dataset.

---

## 5. Adding more people later

- **Data Engineer:** Run 3.2 with the new email (or group).
- **Education Admin:** Add the same principal to the four Education Admin datasets (3.3).
- **BI/Marketing:** Add the same principal to the four BI/Marketing datasets (3.4).

Use **group** principals (e.g. `group:ed-admins@yourdomain.com`) so you add/remove people in one place.
