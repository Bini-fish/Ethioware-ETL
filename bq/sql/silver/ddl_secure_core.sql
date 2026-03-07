-- Ethioware – secure_core.secure_id_map
-- PII only; links learner_id (hash) to email/name. Analytical tables store only learner_id.
-- Run in project: ethioware-etl (or set via --project_id)
-- Region: me-central1 (document fallbacks if dataset created elsewhere)

CREATE TABLE IF NOT EXISTS `ethioware-etl.secure_core.secure_id_map` (
  learner_id     STRING NOT NULL OPTIONS(description = 'SHA-256(lower(trim(email_canonical))); stable algorithm'),
  email_canonical STRING NOT NULL OPTIONS(description = 'Canonical email from form (Email2); trim, lowercase before hash'),
  full_name_raw  STRING OPTIONS(description = 'Full name from form; PII'),
  created_at     TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader on insert'),
  updated_at     TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader on insert/update'),
  source_file    STRING OPTIONS(description = 'Last source file that updated this row (audit)')
)
OPTIONS(
  description = 'Maps learner_id to PII. Only Education Admins should have read access. Do not expose in dashboards.'
);
