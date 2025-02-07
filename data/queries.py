from datetime import datetime
import sys
import os
import pandas as pd
from dash import html
from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func


from settings import *
from .models import Paper, Prediction

# Add the parent folder to the Python search path
parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)

# Set up the database connection
DATABASE_URL = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{
    DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)


def get_studies_details(study_tags: dict[str, list[html.Div]] = None, ids: list[int] = None) -> list[dict]:
    """
    Retrieves studies from the database based on the provided filters.

    Parameters:
    filters (list of dict): List of filters to apply to the study data.

    Returns:
    list of dict: A list of dictionaries containing the studies that match the filters.
    """
    session = Session()
    try:
        query = session.query(Paper)
        if study_tags:
            ids = study_tags.keys()
        elif not ids:
            ids = []
        studies = query.filter(Paper.id.in_(ids)).all()
        results = []
        for study in studies:
            result = {
                'id': study.id,
                'title': study.title,
                'abstract': study.abstract,
                'key_terms': study.key_terms,
                'doi': study.doi,
                'year': study.year,
                'authors': study.authors,
                'link_to_fulltext': study.link_to_fulltext,
                'link_to_pubmed': study.link_to_pubmed,
                'tags': study_tags[study.id] if study_tags else []
            }
            results.append(result)
        return results
    finally:
        session.close()


def get_filtered_freq(task: str, filter_task: str, filter_task_label: str = None, threshold: float = 0.1) -> pd.DataFrame:
    """Get the prediction data for a given task and filter the data based on the filter task and label."""
    session = Session()
    try:
        subquery = session.query(Prediction.paper_id).filter(
            Prediction.task == filter_task,
            Prediction.label == filter_task_label,
            Prediction.probability >= threshold
        ).subquery()
        query = session.query(Prediction.label, func.count(Prediction.id).label('Frequency')).filter(
            Prediction.task == task,
            Prediction.probability >= threshold
        )

        query = query.filter(Prediction.paper_id.in_(subquery))

        query = query.group_by(Prediction.label).order_by('Frequency')
        result = pd.read_sql(query.statement, session.bind)
        result.rename(
            columns={'label': task, 'Frequency': 'Frequency'}, inplace=True)
        return result
    finally:
        session.close()


def get_freq(task: str, labels: list[str] = None, threshold: float = 0.1) -> pd.DataFrame:
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
            Prediction.probability >= threshold
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


def get_pred(task: str, threshold: float = 0.1) -> pd.DataFrame:
    """Get the prediction data for a given task."""
    session = Session()
    try:
        query = session.query(Prediction).filter(
            Prediction.task == task,
            Prediction.probability >= threshold
        )
        result = pd.read_sql(query.statement, session.bind)
        return result
    finally:
        session.close()


def get_pred_filtered(task: str, ids: list[int], threshold: float = 0.1) -> pd.DataFrame:
    """Get the prediction data for a given task and filter the data based on the paper IDs."""
    session = Session()
    try:
        query = session.query(Prediction).filter(
            Prediction.task == task,
            Prediction.paper_id.in_(ids),
            Prediction.probability >= threshold
        )
        result = pd.read_sql(query.statement, session.bind)
        return result
    finally:
        session.close()


def get_freq_grouped(task: str, group_task: str, threshold: float = 0.1, labels: list[str] = None, ) -> pd.DataFrame:
    """Get the predictions where task is labels, group by group task and labels, then count the frequency. 
    The output is a dataframe with columns group_task, label, and Frequency."""
    session = Session()

    try:
        use_rest = 'Other' in labels if labels else False
        grouping_query = (
            session.query(
                Prediction.paper_id.label("paper_id"),
                Prediction.label.label(group_task)
            )
            .filter(Prediction.task == group_task, Prediction.probability > threshold)
            .subquery()
        )

        # Main query for task grouping
        if labels:
            label_case = case(
                (Prediction.label.in_(labels), Prediction.label),
                else_="Other" if use_rest else Prediction.label
            )
        else:
            label_case = Prediction.label

        # Main query for task grouping
        query = (
            session.query(
                grouping_query.c[group_task].label(group_task),
                label_case.label("Label"),
                func.count(Prediction.id).label("Frequency")
            )
            .join(grouping_query, grouping_query.c.paper_id == Prediction.paper_id)
            .filter(Prediction.task == task, Prediction.probability > threshold)
            .group_by(grouping_query.c[group_task], label_case)
        )

        # Execute query and fetch results
        result = query.all()

        # Convert results to a Pandas DataFrame
        df = pd.DataFrame(result, columns=[group_task, task, "Frequency"])
        return df

    finally:
        session.close()


def get_ids(task: str = None, label: str = None, threshold: float = 0.1) -> set[int]:
    """Get the ids of the papers that have a specific label for a given task."""
    session = Session()
    if task is None and label is None:
        # Return all paper ids
        try:
            query = session.query(Prediction.paper_id)
            ids = [item.paper_id for item in query.all()]
            return set(ids)
        finally:
            session.close()
    elif task is not None:
        try:
            query = session.query(Prediction.paper_id).filter(
                Prediction.task == task,
                Prediction.probability >= threshold
            )
            if label is not None:
                query = query.filter(Prediction.label == label)
            ids = [item.paper_id for item in query.all()]
            return set(ids)
        finally:
            session.close()
    else:
        try:
            query = session.query(Prediction.paper_id).filter(
                Prediction.task == task,
                Prediction.label == label,
                Prediction.probability >= threshold
            )
            ids = [item.paper_id for item in query.all()]
            return set(ids)
        finally:
            session.close()


def get_all_tasks() -> list[str]:
    """Get all unique tasks from the predictions."""
    session = Session()
    try:
        query = session.query(Prediction.task).distinct()
        tasks = [item.task for item in query.all()]
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
