CREATE INDEX idx_paper_id ON paper (id);
CREATE INDEX idx_prediction_task_paper_id ON prediction (task, paper_id);
CREATE INDEX idx_prediction_task_label_paper_id ON prediction (task, label, paper_id);
CREATE INDEX idx_prediction_task ON prediction (task);
CREATE INDEX idx_prediction_label ON prediction (label);
CREATE INDEX idx_prediction_task_label ON prediction (task, label);
CREATE INDEX idx_paper_year ON paper (year);