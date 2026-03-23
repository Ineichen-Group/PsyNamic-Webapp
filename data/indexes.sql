-- Minimal, non-redundant indexes for production usage
-- Primary key on `paper(id)` already provides an index; avoid duplicating it.
CREATE INDEX IF NOT EXISTS idx_prediction_task_label_paper_id ON prediction (task, label, paper_id);
CREATE INDEX IF NOT EXISTS idx_prediction_label ON prediction (label);
CREATE INDEX IF NOT EXISTS idx_prediction_paper_id ON prediction (paper_id);
-- Indexes on `paper` must match the model fields in data/models.py
CREATE INDEX IF NOT EXISTS idx_paper_pubmed_id ON paper (pubmed_id);
CREATE INDEX IF NOT EXISTS idx_paper_date ON paper (date);