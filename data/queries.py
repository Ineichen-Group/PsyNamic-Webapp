"""
This module contains database query functions for the PsyNamic-Webapp.
"""

from .models import Paper, Prediction, NerTag, DosageNormalization, BatchRetrieval
from .dosage_norm import to_mg, normalize_relative_weight_dosages
from datetime import datetime

import sys
import os
import logging
from collections import OrderedDict
import pandas as pd
from sqlalchemy import create_engine, func, extract, or_
from sqlalchemy.orm import sessionmaker, load_only
from sqlalchemy.sql import select
from sqlalchemy import and_, tuple_, case

from style.colors import get_color_mapping

from dotenv import load_dotenv
load_dotenv()

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")


# Add the parent folder to the Python search path
parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)

# Set up the database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME)
)
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


SKIP_TASKS = ["Study Conclusion", "Clinical Trial Phase"]


def log_time(func):
    """Decorator to log the execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        duration = (datetime.now() - start_time).total_seconds()
        logging.info(f"{func.__name__} query took {duration:.4f} seconds")
        return result
    return wrapper


def get_studies_details(
    ids: list[int] = None,
    start_row: int = 0,
    end_row: int = 20,
    sort_model: list[dict] = None,
    filter_model: dict = None,
    tags: dict[str, list] = None,
    map_all_labels: bool = False
):

    session = Session()
    try:
        if ids is not None and len(ids) == 0:
            return []

        query = session.query(
            Paper,
            extract('year', Paper.date).label('year')
        )

        # Filtering
        if filter_model:
            for field, condition in filter_model.items():
                if "filter" in condition:
                    query = query.filter(
                        getattr(Paper, field) == condition["filter"]
                    )

        if ids:
            query = query.filter(Paper.id.in_(ids))

        # Default sorting
        if not sort_model or len(sort_model) == 0:
            sort_field = "year"
            sort_order = "desc"
        else:
            sort_field = sort_model[0]["colId"]
            sort_order = sort_model[0]["sort"]

        if sort_field == "year":
            order_column = Paper.date
        else:
            order_column = getattr(Paper, sort_field, None)

        if order_column is not None:
            query = query.order_by(
                order_column.desc() if sort_order == "desc" else order_column.asc()
            )

        # Pagination
        query = query.offset(start_row)
        if end_row is not None:
            limit_value = end_row - start_row
            if limit_value > 0:
                query = query.limit(limit_value)

        query = query.options(load_only(
            Paper.id, Paper.title, Paper.abstract, Paper.prediction_input,
            Paper.key_terms, Paper.doi,
            Paper.pubmed_id, Paper.link_to_pubmed, Paper.other_url,
            Paper.date
        ))

        studies = query.all()

        papers = [row[0] for row in studies]
        years = {row[0].id: row[1] for row in studies}

        # Tags
        if tags:
            study_tags = get_study_tags([p.id for p in papers], tags, map_all_labels=map_all_labels)

        results = [
            {
                'id': paper.id,
                'title': paper.title,
                'abstract': paper.abstract,
                'prediction_input': paper.prediction_input,
                'key_terms': paper.key_terms,
                'doi': paper.doi,
                'year': years.get(paper.id),
                'pubmed_id': paper.pubmed_id,
                'url': paper.url,
                'tags': study_tags.get(paper.id, []) if tags else []
            }
            for paper in papers
        ]

        return results

    finally:
        session.close()


def get_studies_details_ner(
    ids: list[int] = None,
    start_row: int = 0,
    end_row: int = 20,
    sort_model: list[dict] = None,
    filter_model: dict = None,
    tags: dict[str, list] = None
):

    session = Session()
    try:
        # if ids empty list, assume not match
        if ids is not None and len(ids) == 0:
            return []
        tags = {
            'Substances': get_all_labels('Substances'),
        }
        query = session.query(Paper)

        # Only include papers that have a 'Dosage' NER tag
        query = query.join(NerTag, Paper.id == NerTag.paper_id).filter(
            NerTag.tag == 'Dosage').distinct()

        # Apply any filters based on the filter model
        if filter_model:
            for field, condition in filter_model.items():
                if "filter" in condition:
                    query = query.filter(
                        getattr(Paper, field) == condition["filter"])

        # Apply filtering by paper IDs
        if ids:
            query = query.filter(Paper.id.in_(ids))

        # Set default sorting if no sort_model is provided
        if not sort_model or len(sort_model) == 0:
            # Default sorting by 'year' in descending order
            sort_field = "year"
            sort_order = "desc"
        else:
            # Use the sorting provided in the sort_model
            sort_field = sort_model[0]["colId"]
            sort_order = sort_model[0]["sort"]

        # Apply the sorting
        order_column = getattr(Paper, sort_field, None)
        if order_column is not None:
            query = query.order_by(
                order_column.desc() if sort_order == "desc" else order_column.asc())

        # Pagination with offset and optional limit. If `end_row` is None,
        # don't apply a limit (fetch all after offset).
        query = query.offset(start_row)
        if end_row is not None:
            limit_value = end_row - start_row
            if limit_value > 0:
                query = query.limit(limit_value)

        # Specify which fields to load into the Paper instances
        query = query.options(load_only(
            Paper.id, Paper.title, Paper.abstract,
            Paper.key_terms, Paper.doi, Paper.date,
            Paper.pubmed_id, Paper.link_to_pubmed, Paper.other_url
        ))

        # Execute the query
        studies = query.all()

        # Fetch tags if provided
        if tags:
            study_tags = get_study_tags([study.id for study in studies], tags)

        # Prepare the results
        results = [
            {
                'id': study.id,
                'title': study.title,
                'abstract': study.abstract,
                'prediction_input': study.prediction_input,
                'key_terms': study.key_terms,
                'doi': study.doi,
                'year': study.date.year,
                'url': study.url,
                'tags': study_tags.get(study.id, []) if tags else [],
                'dosage': get_dosage_string(study.id),
                'dosage_display': get_dosage_display_string(study.id)
            }
            for study in studies
        ]

        return results

    finally:
        session.close()


def get_study_tags(ids: list[int], tags: dict[str, list], map_all_labels: bool = False) -> dict[int, list[dict]]:
    study_tags = {}
    session = Session()

    try:

        valid_task_label_pairs = [
            (task, label) for task, labels in tags.items() for label in labels
        ]

        query = session.query(
            Prediction.paper_id,
            Prediction.task,
            Prediction.label
        ).filter(
            and_(
                Prediction.task.in_(tags.keys()),
                tuple_(Prediction.task, Prediction.label).in_(
                    valid_task_label_pairs),
                Prediction.paper_id.in_(ids)
            )
        )

        results = query.all()

        study_tags = {}
        # TODO: cache color mappings
        if map_all_labels:
            color_mappings = {task: get_color_mapping(
                task, get_all_labels(task)) for task, labels in tags.items()}
        else:
            color_mappings = {task: get_color_mapping(
                task, labels) for task, labels in tags.items()}

        for paper_id, task, label in results:
            tag_info = {
                'task': task,
                'label': label,
                'color': color_mappings[task][label],
            }

            if paper_id not in study_tags:
                study_tags[paper_id] = {}

            if task not in study_tags[paper_id]:
                study_tags[paper_id][task] = []

            study_tags[paper_id][task].append(tag_info)

        ordered_study_tags = {}
        for paper_id, task_dict in study_tags.items():
            ordered_tags = []
            for task, labels in tags.items():
                if task in task_dict:  # Ensure the task is present
                    for label in labels:
                        for tag_info in task_dict[task]:
                            if tag_info['label'] == label:
                                ordered_tags.append(tag_info)
            ordered_study_tags[paper_id] = ordered_tags

        return ordered_study_tags
    finally:
        session.close()


def get_filtered_freq(task: str, filter_task: str, filter_task_label: str = None) -> pd.DataFrame:
    """
    Get the prediction data for a given task and filter the data 
    based on the filter task and label.
    """
    session = Session()
    try:
        # Explicitly use select() for the subquery
        subquery = (
            select(Prediction.paper_id)
            .where(
                Prediction.task == filter_task,
                Prediction.label == filter_task_label
            )
        ).subquery()

        query = (
            select(Prediction.label, func.count(
                Prediction.id).label("Frequency"))
            .where(Prediction.task == task, Prediction.paper_id.in_(select(subquery)))
            .group_by(Prediction.label)
            .order_by("Frequency")
        )

        result = pd.read_sql(query, session.bind)
        result.rename(
            columns={"label": task, "Frequency": "Frequency"}, inplace=True)
        return result
    finally:
        session.close()


def get_freq(task: str, labels: list[str] = None) -> pd.DataFrame:
    """
    Get the frequency of the labels for a given task. If no labels are provided, return the frequency of all labels."""
    session = Session()
    try:
        # Build query
        query = session.query(
            Prediction.label,
            func.count(Prediction.id).label('Frequency')
        ).filter(
            Prediction.task == task,
        )
        if labels:
            query = query.filter(Prediction.label.in_(labels))
        query = query.group_by(Prediction.label).order_by(
            func.count(Prediction.id).desc())
        result = pd.read_sql(query.statement, session.bind)
        result.rename(
            columns={'label': task, 'Frequency': 'Frequency'}, inplace=True)
        return result

    except Exception as e:
        print(f"Error fetching frequencies: {e}")
        return pd.DataFrame(columns=[task, 'Frequency'])

    finally:
        session.close()


def get_pred(task: str) -> pd.DataFrame:
    """Get the prediction data for a given task."""
    session = Session()
    try:
        query = session.query(Prediction).filter(
            Prediction.task == task,
        )
        result = pd.read_sql(query.statement, session.bind)
        return result
    finally:
        session.close()


def get_pred_filtered(task: str, ids: list[int]) -> pd.DataFrame:
    """Get the prediction data for a given task and filter the data based on the paper IDs."""
    session = Session()
    try:
        query = session.query(Prediction).filter(
            Prediction.task == task,
            Prediction.paper_id.in_(ids),
        )
        result = pd.read_sql(query.statement, session.bind)
        return result
    finally:
        session.close()


def get_freq_grouped(task: str, group_task: str, labels: list[str] = None) -> pd.DataFrame:
    """Get the predictions where task is labels, group by group task and labels. 
    The output is a dataframe with columns group_task, label, and Study_ID (without frequency)."""
    session = Session()

    try:
        use_rest = 'Other' in labels if labels else False

        # Subquery to group by the group_task
        grouping_query = (
            session.query(
                Prediction.paper_id.label("paper_id"),
                Prediction.label.label(group_task)
            )
            .filter(Prediction.task == group_task)
            .subquery()
        )

        # Handle the case where specific labels are provided
        if labels:
            label_case = case(
                (Prediction.label.in_(labels), Prediction.label),
                else_="Other" if use_rest else Prediction.label
            )
        else:
            label_case = Prediction.label

        # Main query (without frequency counting, including Study_ID)
        query = (
            session.query(
                grouping_query.c[group_task].label(group_task),
                label_case.label("Label"),
                Prediction.paper_id.label("Study_ID")  # Include Study_ID
            )
            .join(grouping_query, grouping_query.c.paper_id == Prediction.paper_id)
            .filter(Prediction.task == task)
        )

        # Execute query and fetch results
        result = query.all()

        # Convert results to a Pandas DataFrame, now including Study_ID
        df = pd.DataFrame(result, columns=[group_task, task, "Study_ID"])
        return df

    finally:
        session.close()


def get_ids(task: str = None, label: str = None) -> set[int]:
    """Get the ids of the papers that have a specific label for a given task.
    If no task and label are provided, return all paper ids."""

    session = Session()
    if task is None and label is None:
        # Return all paper ids
        try:
            query = session.query(Prediction.paper_id)
            ids = [item.paper_id for item in query.all()]
            return list(set(ids))
        finally:
            session.close()
    elif task is not None:
        try:
            query = session.query(Prediction.paper_id).filter(
                Prediction.task == task
            )
            if label is not None:
                query = query.filter(Prediction.label == label)
            ids = [item.paper_id for item in query.all()]
            return list(set(ids))
        finally:
            session.close()
    else:
        try:
            query = session.query(Prediction.paper_id).filter(
                Prediction.task == task,
                Prediction.label == label)
            ids = [item.paper_id for item in query.all()]
            return list(set(ids))
        finally:
            session.close()


def get_all_tasks() -> list[str]:
    """Get all unique tasks from the predictions."""
    session = Session()
    try:
        query = session.query(Prediction.task).distinct()
        tasks = [item.task for item in query.all() if item.task not in SKIP_TASKS]
        tasks.sort()
        return tasks
    finally:
        session.close()


def get_all_labels(task: str) -> list[str]:
    """Get all unique labels for a given task."""
    session = Session()
    try:
        query = session.query(Prediction.label).filter(
            Prediction.task == task).distinct()
        labels = [item.label for item in query.all()]
        return labels
    finally:
        session.close()


def get_time_data(end_year: int = None, start_year: int = None) -> tuple[pd.DataFrame, list[int]]:
    """Get the frequency of IDs per year. Optionally filter by start and end year."""
    session = Session()
    try:
        query = session.query(
            Paper.id,
            extract('year', Paper.date).label('year')
        )

        df = pd.read_sql(query.statement, session.bind)
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    finally:
        session.close()

    # filter
    if end_year:
        df = df[df['year'] <= end_year]
    if start_year:
        df = df[df['year'] >= start_year]

    ids = df['id'].to_list()

    # count IDs per year
    frequency_df = (
        df.groupby('year')
        .count()
        .reset_index()
        .rename(columns={'id': 'Frequency', 'year': 'Year'})
    )

    return frequency_df, ids


def nr_studies():
    """Get the number of studies in the database."""
    session = Session()
    try:
        query = session.query(func.count(Paper.id))
        result = query.first()
        return result[0]
    finally:
        session.close()


def search_papers(query: str, start_row: int = 0, end_row: int = 50):
    """Search papers by pubmed id, study id, doi or title (partial match for title/doi).
    Returns a list of dicts with similar shape to `get_studies_details`.
    """
    session = Session()
    try:
        q = query.strip()

        query_stmt = session.query(Paper)

        # numeric -> could be pubmed_id or internal id
        if q.isdigit():
            # match either id or pubmed_id
            query_stmt = query_stmt.filter(
                (Paper.id == int(q)) | (Paper.pubmed_id == q)
            )
        else:
            # treat as doi if contains a slash and a dot (simple heuristic)
            if '/' in q and '.' in q:
                query_stmt = query_stmt.filter(Paper.doi.ilike(f"%{q}%"))
            else:
                # fallback to title partial match
                query_stmt = query_stmt.filter(Paper.title.ilike(f"%{q}%"))

        # pagination
        query_stmt = query_stmt.offset(start_row)
        if end_row is not None:
            limit_value = end_row - start_row
            if limit_value > 0:
                query_stmt = query_stmt.limit(limit_value)

        query_stmt = query_stmt.options(load_only(
            Paper.id, Paper.title, Paper.abstract,
            Paper.key_terms, Paper.doi, Paper.date,
            Paper.pubmed_id, Paper.link_to_pubmed, Paper.other_url
        ))

        studies = query_stmt.all()

        # no tags by default
        results = [
            {
                'id': s.id,
                'title': s.title,
                'abstract': s.abstract,
                'key_terms': s.key_terms,
                'doi': s.doi,
                'year': s.date.year if s.date else None,
                'pubmed_id': s.pubmed_id,
                'url': s.url,
                'tags': [],
            }
            for s in studies
        ]

        return results
    finally:
        session.close()


def get_filtered_study_ids(filter: OrderedDict[str, list[str]], mode = "and") -> list[int]:
    """Get study IDs matching the given filter.

    Args:
        filter: Mapping from task names to lists of labels.
        mode:
            - "and": studies must match every task/label pair.
            - "or": studies must match at least one task/label pair.
    """
    if mode not in {"and", "or"}:
        raise ValueError("mode must be 'and' or 'or'")

    valid_task_label_pairs = [
        (task, label)
        for task, labels in filter.items()
        for label in labels
    ]

    if mode == "and":
        matching_ids = set(get_ids())
        for task, label in valid_task_label_pairs:
            matching_ids &= set(get_ids(task, label))
    else:
        matching_ids = set()
        for task, label in valid_task_label_pairs:
            matching_ids |= set(get_ids(task, label))

    return list(matching_ids)


def get_pred_text(id: int) -> str:
    session = Session()
    try:
        query = session.query(Paper.prediction_input).filter(Paper.id == id)
        result = query.first()
        return result[0]
    finally:
        session.close()


def get_dosage_string(paper_id: int) -> str:
    """Get all dosage tags for a given paper ID."""
    session = Session()
    try:
        query = session.query(NerTag).filter(
            NerTag.paper_id == paper_id, NerTag.tag == 'Dosage')
        results = query.all()

        norm_texts = set()
        # get connected dosage normalization for each tag
        for tag in results:
            query = session.query(DosageNormalization).filter(
                DosageNormalization.ner_tag_id == tag.id)
            norm = query.first()
            if norm:
                tag.norm_text = norm.norm_text
                norm_texts.add(tag.norm_text)

        dosages = ''
        for t in norm_texts:
            dosages += t + ' | '

        dosages = dosages[:-3]  # Remove last ' | '
        return dosages
    finally:
        session.close()


def get_dosage_display_string(paper_id: int) -> str:
    """Get dosage tags with 70 kg normalization shown for relative weight dosages."""
    session = Session()
    try:
        query = (
            session.query(NerTag, DosageNormalization)
            .join(DosageNormalization, DosageNormalization.ner_tag_id == NerTag.id)
            .filter(NerTag.paper_id == paper_id, NerTag.tag == 'Dosage')
        )
        results = query.all()

        display_texts = []
        seen_texts = set()

        for tag, norm in results:
            display_text = norm.norm_text

            if norm.dose_type and norm.dose_type.startswith('relative_weight'):
                min_val, max_val = normalize_relative_weight_dosages(
                    norm.min, norm.max, norm.weight_reference, norm.per_weight_unit
                )
                min_mg = to_mg(min_val, norm.unit)
                max_mg = to_mg(max_val, norm.unit)

                if min_mg is not None and max_mg is not None:
                    if min_mg == max_mg:
                        normalized_value = f"{min_mg:g} mg"
                    else:
                        normalized_value = f"{min_mg:g}-{max_mg:g} mg"
                    display_text = f"{norm.norm_text} -> {normalized_value} (70 kg person)"
                else:
                    display_text = f"{norm.norm_text} (70 kg person)"

            if display_text not in seen_texts:
                seen_texts.add(display_text)
                display_texts.append(display_text)

        return ' | '.join(display_texts)
    finally:
        session.close()


def ner_tags_type(paper_id: int, ner_type: str = None, in_titel=False) -> list[dict]:
    """Get all tags of a specific type for a given paper ID."""
    session = Session()
    try:
        if ner_type is None:
            query = session.query(NerTag).filter(
                NerTag.paper_id == paper_id)
        else:
            query = session.query(NerTag).filter(
                NerTag.paper_id == paper_id, NerTag.tag == ner_type)
        results = query.all()

        # get title, abstract and text
        query = session.query(Paper).filter(Paper.id == paper_id)
        paper = query.first()
        title = paper.title
        end_id_of_title = len(title + '.^\n')
        tags = []
        for tag in results:
            if not in_titel and tag.start_id < end_id_of_title:
                continue

            tags.append({
                'start': tag.start_id, # if in_titel else tag.start_id - end_id_of_title,
                'end': tag.end_id, # if in_titel else tag.end_id - end_id_of_title,
                'tag': tag.tag,
            })
        return tags
    finally:
        session.close()


def get_dosage_samples(substances: list[str] = None, dosage_types: list[str] = ['absolute', 'relative_weight'], initial_dataset: bool = False) -> pd.DataFrame:
    """Return a DataFrame with dosage samples per substance.

    The following preprocessing steps are applied:
    * normalize relative weight dosages to absolute dosages using a reference weight of 70kg 
    * convert all dosages to mg using the provided unit information
    * remove duplicates (same substance, dosage, unit, study id, and dose type)
    * remove entries with substance "Unknown", "Analogue", or "Combination Therapy"
    """
    session = Session()

    # Select necessary fields including per-weight metadata and dose_type
    query = session.query(
        Prediction.label,
        Paper.id,
        DosageNormalization.min,
        DosageNormalization.max,
        DosageNormalization.unit,
        DosageNormalization.per_weight_unit,
        DosageNormalization.weight_reference,
        DosageNormalization.dose_type, DosageNormalization.norm_text
    ).join(Paper, Prediction.paper_id == Paper.id)
    query = query.join(NerTag, NerTag.paper_id == Paper.id)
    query = query.join(DosageNormalization,
                       DosageNormalization.ner_tag_id == NerTag.id)
    query = query.filter(Prediction.task == 'Substances')

    if initial_dataset:
        # filter for papers that have entrez_year <= 2025 or no entrez_year
        query = query.filter(or_(Paper.entrez_year.is_(None), Paper.entrez_year <= 2025))

    if dosage_types:
        query = query.filter(DosageNormalization.dose_type.in_(dosage_types))

    if substances:
        query = query.filter(Prediction.label.in_(substances))

    rows = query.all()

    samples = []

    # Normalize relative weight dosages & convert all dosages to mg
    for label, paper_id, minv, maxv, unit, per_weight_unit, weight_reference, dose_type, norm_text in rows:
        if dose_type and dose_type.startswith('relative'):
            min_val, max_val = normalize_relative_weight_dosages(
                minv, maxv, weight_reference, per_weight_unit)
        else:
            min_val = minv
            max_val = maxv

        min_mg = to_mg(min_val, unit)
        max_mg = to_mg(max_val, unit)

        if min_mg is not None and max_mg is not None:
            samples.append({'Substance': label, 'Dosage_mg': min_mg,
                           'Unit': 'mg', 'Study_ID': paper_id, 'Dose_Type': dose_type, 'Norm_Text': norm_text})

    df = pd.DataFrame(samples)
    # Remove duplicates same paper, dosage and substance
    df = df.drop_duplicates(
        subset=['Substance', 'Dosage_mg', 'Unit', 'Study_ID', 'Dose_Type', 'Norm_Text'])

    # Remove "Unknown", "Analogue", "Combination Therapy"
    df = df[~df['Substance'].isin(
        ['Unknown', 'Analogue', 'Combination Therapy'])]

    return df



def latest_update():
    """Get the the retrieval date, formated like 20.01.2026, of the latest batch retrieval."""
    session = Session()
    try:
        # The model uses `date` as the timestamp column on BatchRetrieval
        query = session.query(BatchRetrieval).order_by(
            BatchRetrieval.date.desc()).first()
        if query and query.date:
            return query.date.strftime("%d.%m.%Y")
        return "Unknown"
    finally:
        session.close()
