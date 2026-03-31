

import os
import pandas as pd
from sqlalchemy import text
from .queries import engine


def export_classification_data(outfile: str) -> str:
    """Export classification (predictions) data to CSV including study primary key.

    Columns include: Study_ID (paper_id), task, label, probability, model, is_multilabel
    Returns the path to the written CSV file.
    """
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    sql = text(
        "SELECT paper_id AS Study_ID, task, label, probability, model, is_multilabel FROM prediction"
    )
    df = pd.read_sql(sql, engine)
    df.to_csv(outfile, index=False)
    return outfile


def export_ner_data(outfile: str) -> str:
    """Export NER tags (ner_tag) and dosage normalization (if present) to CSV.

    Columns include: Study_ID (paper_id), ner_tag_id, tag, start_id, end_id, text, probability, model,
    norm_text, min, max, unit, per_weight_unit, weight_reference, per_time_unit, dose_type, original_dosage
    Returns the path to the written CSV file.
    """
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    sql = text(
        "SELECT nt.id AS ner_tag_id, nt.paper_id AS Study_ID, nt.tag, nt.start_id, nt.end_id, nt.text, nt.probability, nt.model, "
        "dn.norm_text, dn.min, dn.max, dn.unit, dn.per_weight_unit, dn.weight_reference, dn.per_time_unit, dn.dose_type, dn.original_dosage "
        "FROM ner_tag nt LEFT JOIN dosage_normalization dn ON dn.ner_tag_id = nt.id"
    )
    df = pd.read_sql(sql, engine)
    df.to_csv(outfile, index=False)
    return outfile

def export_study_data(outfile: str) -> str:
    """Export study metadata (id, pubmed_id, title, abstract) and
    publication date to CSV. Publication date is formatted as yyyy-mm-dd
    in the `Publication_Date` column.
    """

    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    sql = text(
        "SELECT id AS Study_ID, pubmed_id, title, abstract, date, retrieval_id AS batch_id FROM paper"
    )
    df = pd.read_sql(sql, engine)

    # Format publication date as yyyy-mm-dd and expose under Publication_Date
    df['Publication_Date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df = df.drop(columns=['date'])


    df.to_csv(outfile, index=False)
    return outfile

if __name__ == "__main__":
    export_classification_data("analysis/export/classification_data.csv")
    export_ner_data("analysis/export/ner_data.csv")
    export_study_data("analysis/export/study_data.csv")