-- Minimal, non-redundant indexes for production usage
-- Primary key on `paper(id)` already provides an index; avoid duplicating it.
CREATE INDEX IF NOT EXISTS idx_prediction_task_label_paper_id ON prediction (task, label, paper_id);
CREATE INDEX IF NOT EXISTS idx_prediction_label ON prediction (label);
CREATE INDEX IF NOT EXISTS idx_prediction_paper_id ON prediction (paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_year ON paper (year);

-- Notes:
-- - `idx_prediction_task_label_paper_id` covers queries filtering by `task` and `label`,
--   and supports left-prefix queries by `task` or `task,label`.
-- - `idx_prediction_label` speeds queries filtering only by `label`.
-- - `idx_prediction_paper_id` helps joins to `paper(id)` and single-column lookups.
-- - For very large bulk imports consider creating indexes `CONCURRENTLY` after loading
--   to avoid long table locks.