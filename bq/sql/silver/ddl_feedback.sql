-- Ethioware – silver_trainings.feedback
-- Session Feedback Form (expert), mentor, trainee. Rating/Rating2 for dashboard; sentiment from CSV or NLP.
-- Run in project: ethioware-etl

CREATE TABLE IF NOT EXISTS `ethioware-etl.silver_trainings.feedback` (
  feedback_id       STRING NOT NULL OPTIONS(description = 'Unique per row; e.g. source_file + row index or UUID'),
  learner_identifier STRING OPTIONS(description = 'Email/name if present; else anonymous'),
  feedback_type     STRING NOT NULL OPTIONS(description = 'expert, mentor, trainee'),
  rating            STRING OPTIONS(description = 'Expert Rating – for dashboard'),
  rating2           STRING OPTIONS(description = 'Expert Rating2 – recommendation – for dashboard'),
  feedback_text     STRING OPTIONS(description = 'Free text; can concatenate multiple columns'),
  sentiment_label   STRING OPTIONS(description = 'Positive, Neutral, Negative; from CSV or Cloud NL API'),
  sentiment_score   FLOAT64 OPTIONS(description = 'From Cloud Natural Language API if used'),
  model_version     STRING OPTIONS(description = 'Sentiment model version if from API'),
  source_file       STRING NOT NULL,
  ingestion_time    TIMESTAMP NOT NULL OPTIONS(description = 'Set by loader')
)
OPTIONS(
  description = 'Feedback from Session Feedback Form (expert), mentor, trainee. Rating/Rating2 for dashboard.'
);
