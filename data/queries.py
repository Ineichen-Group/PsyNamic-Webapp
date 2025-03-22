from datetime import datetime
import sys
import os
import logging
import pandas as pd
from dash import html
from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import and_, tuple_

from style.colors import rgb_to_hex, get_color_mapping, SECONDARY_COLOR
from settings import *
from .models import Paper, Prediction

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
    tags: dict[str, list] = None
):
    session = Session()
    try:
        query = session.query(Paper)

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

        # Pagination with offset and limit
        query = query.offset(start_row).limit(end_row - start_row)

        # Specify which fields to retrieve
        query = query.with_entities(
            Paper.id, Paper.title, Paper.abstract,
            Paper.key_terms, Paper.doi, Paper.year,
            Paper.link_to_pubmed
        )

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
                'key_terms': study.key_terms,
                'doi': study.doi,
                'year': study.year,
                'link_to_pubmed': study.link_to_pubmed,
                'tags': study_tags.get(study.id, []) if tags else []
            }
            for study in studies
        ]

        return results
    finally:
        session.close()


def get_study_tags(ids: list[int], tags: dict[str, list]) -> dict[int, list[dict]]:
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
                tuple_(Prediction.task, Prediction.label).in_(valid_task_label_pairs),
                Prediction.paper_id.in_(ids)
            )
        )

        results = query.all()

        study_tags = {}
        # TODO: cache color mappings
        color_mappings = {task: get_color_mapping(task, get_all_labels(task)) for task in tags.keys()}

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


@log_time
def get_filtered_freq(task: str, filter_task: str, filter_task_label: str = None) -> pd.DataFrame:
    """Get the prediction data for a given task and filter the data based on the filter task and label."""
    session = Session()
    try:
        subquery = session.query(Prediction.paper_id).filter(
            Prediction.task == filter_task,
            Prediction.label == filter_task_label,
        ).subquery()
        query = session.query(Prediction.label, func.count(Prediction.id).label('Frequency')).filter(
            Prediction.task == task,
        )

        query = query.filter(Prediction.paper_id.in_(subquery))

        query = query.group_by(Prediction.label).order_by('Frequency')
        result = pd.read_sql(query.statement, session.bind)
        result.rename(
            columns={'label': task, 'Frequency': 'Frequency'}, inplace=True)
        return result
    finally:
        session.close()


@log_time
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


@log_time
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


@log_time
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


@log_time
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


@log_time
def get_ids(task: str = None, label: str = None) -> set[int]:
    """Get the ids of the papers that have a specific label for a given task."""
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


@log_time
def get_all_tasks() -> list[str]:
    """Get all unique tasks from the predictions."""
    session = Session()
    try:
        query = session.query(Prediction.task).distinct()
        tasks = [item.task for item in query.all()]
        return tasks
    finally:
        session.close()


@log_time
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


@log_time
def get_time_data(end_year: int = None, start_year: int = None) -> tuple[pd.DataFrame, list[int]]:
    """Get the frequency of IDs per year. Optionally filter by start and end year."""
    session = Session()
    try:
        query = session.query(Paper.id, Paper.year)
        df = pd.read_sql(query.statement, session.bind)
    finally:
        session.close()

    # use year and id columns
    df = df[['id', 'year']]
    if end_year:
        df = df[df['year'] <= end_year]
    if start_year:
        df = df[df['year'] >= start_year]

    ids = df['id'].to_list()
    # count IDs per year, rename columns to Year and Frequency
    frequency_df = df.groupby('year').count().reset_index().rename(
        columns={'id': 'Frequency', 'year': 'Year'})
    return frequency_df, ids


@log_time
def nr_studies():
    """Get the number of studies in the database."""
    session = Session()
    try:
        query = session.query(func.count(Paper.id))
        result = query.first()
        return result[0]
    finally:
        session.close()
