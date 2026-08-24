"""
This module contains database query functions for the PsyNamic-Webapp.
"""

import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import and_, case, create_engine, extract, func, or_, tuple_
from sqlalchemy.orm import load_only, sessionmaker
from sqlalchemy.sql import select

from data.helper import format_author_citation
from style.colors import get_color_mapping

from .dosage_norm import normalize_relative_weight_dosages, to_mg
from .models import (BatchRetrieval, DosageNormalization, NerTag, Paper,
                     Prediction)

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
DISPLAY_LABELS = {
    'Party setting': 'Recreational setting'
}
MODEL_PATHS = Path(__file__).parent.parent / "pipeline" / "model_paths.json"
with open(MODEL_PATHS) as f:
    MODEL_CONFIG = json.load(f)

LABEL_ORDER = {
    entry["task"]: [
        label
        for _, label in sorted(
            entry["id2label"].items(),
            key=lambda x: int(x[0])
        )
    ]
    for entry in MODEL_CONFIG
}


def get_studies_details(
    ids: list[int] = None,
    start_row: int = 0,
    end_row: int = 20,
    sort_model: list[dict] = None,
    filter_model: dict = None,
    tags: dict[str, list] = None,
    map_all_labels: bool = False
) -> list[dict]:
    """Fetches study details from the database, optionally filtered by IDs, sorted, and paginated to be fed into the study grid."""

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
            Paper.key_terms, Paper.doi, Paper.authors,
            Paper.pubmed_id, Paper.link_to_pubmed, Paper.other_url,
            Paper.date
        ))

        studies = query.all()

        papers = [row[0] for row in studies]
        years = {row[0].id: row[1] for row in studies}

        # Tags
        if tags:
            study_tags = get_study_tags(
                [p.id for p in papers], tags, map_all_labels=map_all_labels)

        results = [
            {
                'id': paper.id,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': format_author_citation(paper.authors),
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
) -> list[dict]:
    """Fetches study details specifically for studies that have a 'Dosage' NER tag, optionally filtered by IDs, sorted, and paginated."""

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
            Paper.id, Paper.title, Paper.abstract, Paper.authors,
            Paper.key_terms, Paper.doi, Paper.date,
            Paper.pubmed_id, Paper.link_to_pubmed, Paper.other_url
        ))

        # Execute the query
        studies = query.all()

        # Fetch tags if provided
        if tags:
            study_tags = get_study_tags([study.id for study in studies], tags)
        paper_ids = [study.id for study in studies]
        dosages_by_id = get_dosages_for_papers(paper_ids)

        # Prepare the results
        results = [
            {
                'id': study.id,
                'title': study.title,
                'abstract': study.abstract,
                'authors': format_author_citation(study.authors),
                'prediction_input': study.prediction_input,
                'key_terms': study.key_terms,
                'doi': study.doi,
                'year': study.date.year if study.date else None,
                'url': study.url,
                'tags': study_tags.get(study.id, []) if tags else [],
                'dosage': dosages_by_id.get(study.id, {}).get('dosage', ''),
                'dosage_display': dosages_by_id.get(study.id, {}).get('dosage_display', '')
            }
            for study in studies
        ]

        return results

    finally:
        session.close()


def get_study_tags(
    ids: list[int], 
    tags: dict[str, list] | None = None, 
    map_all_labels: bool = False
) -> dict[int, list[dict]]:
    """Fetches the tags for the given study IDs and returns them in a structured format, 
    required for the Tags column in the study grid."""
    
    session = Session()
    try:
        # 1. Build Query
        if tags:
            db_tags = {
                task: [database_label(label) for label in labels] 
                for task, labels in tags.items()
            }
            display_tags = {
                task: [display_label(label) for label in labels] 
                for task, labels in tags.items()
            }
            valid_task_label_pairs = [
                (task, label) 
                for task, labels in db_tags.items() 
                for label in labels
            ]

            query = session.query(
                Prediction.paper_id,
                Prediction.task,
                Prediction.label
            ).filter(
                and_(
                    Prediction.paper_id.in_(ids),
                    Prediction.task.in_(db_tags.keys()),
                    tuple_(Prediction.task, Prediction.label).in_(valid_task_label_pairs)
                )
            )
        else:
            query = session.query(
                Prediction.paper_id,
                Prediction.task,
                Prediction.label
            ).filter(
                and_(
                    Prediction.paper_id.in_(ids),
                    Prediction.task.notin_(SKIP_TASKS)
                )
            )

        results = query.all()

        # 2. Extract display_tags dynamically if `tags` parameter wasn't provided
        if not tags:
            display_tags = {}
            for _, task, label in results:
                disp_lbl = display_label(label)
                if task not in display_tags:
                    display_tags[task] = []
                if disp_lbl not in display_tags[task]:
                    display_tags[task].append(disp_lbl)

        # 3. Build Color Mappings
        if map_all_labels:
            color_mappings = {
                task: get_color_mapping(task, get_all_labels(task)) 
                for task in display_tags
            }
        else:
            color_mappings = {
                task: get_color_mapping(task, labels) 
                for task, labels in display_tags.items()
            }

        # 4. Group results by paper_id and task-label pair
        # Structure: { paper_id: { (task, label): tag_info } }
        study_tags_map = {}
        for paper_id, task, label in results:
            disp_lbl = display_label(label)
            task_colors = color_mappings.get(task, {})
            
            tag_info = {
                'task': task,
                'label': disp_lbl,
                'color': task_colors.get(disp_lbl, "#6c757d")
            }

            if paper_id not in study_tags_map:
                study_tags_map[paper_id] = {}
            
            study_tags_map[paper_id][(task, disp_lbl)] = tag_info

        # 5. Build ordered output matching display_tags order
        ordered_study_tags = {paper_id: [] for paper_id in ids}
        
        for paper_id, tags_by_pair in study_tags_map.items():
            for task, labels in display_tags.items():
                for label in labels:
                    key = (task, label)
                    if key in tags_by_pair:
                        ordered_study_tags[paper_id].append(tags_by_pair[key])

        return ordered_study_tags

    finally:
        session.close()


def get_filtered_label_frequencies(task: str, filter_task: str, filter_task_label: str = None) -> pd.DataFrame:
    """
    Get the prediction data for a given task and filter the data 
    based on the filter task and label.
    """
    session = Session()
    filter_task_label = database_label(filter_task_label)
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


def get_task_label_frequencies(task: str, labels: list[str] = None) -> pd.DataFrame:
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
            labels = [database_label(l) for l in labels]
            query = query.filter(Prediction.label.in_(labels))
        query = query.group_by(Prediction.label).order_by(
            func.count(Prediction.id).desc())
        result = pd.read_sql(query.statement, session.bind)
        result.rename(
            columns={'label': task, 'Frequency': 'Frequency'}, inplace=True)
        result[task] = result[task].map(display_label)
        return result

    except Exception as e:
        print(f"Error fetching frequencies: {e}")
        return pd.DataFrame(columns=[task, 'Frequency'])

    finally:
        session.close()


def get_predictions(task: str) -> pd.DataFrame:
    """Get the prediction data for a given task."""
    session = Session()
    try:
        query = session.query(Prediction).filter(
            Prediction.task == task,
        )
        result = pd.read_sql(query.statement, session.bind)
        result["label"] = result["label"].map(display_label)
        return result
    finally:
        session.close()


def get_predictions_by_ids(task: str, ids: list[int]) -> pd.DataFrame:
    """Get the prediction data for a given task and filter the data based on the paper IDs."""
    session = Session()
    try:
        query = session.query(Prediction).filter(
            Prediction.task == task,
            Prediction.paper_id.in_(ids),
        )
        result = pd.read_sql(query.statement, session.bind)
        result["label"] = result["label"].map(display_label)
        return result
    finally:
        session.close()


def get_freq_grouped(
    task: str,
    group_task: str,
    labels: list[str] = None,
    aggregate: bool = False,
) -> pd.DataFrame:
    """Get grouped predictions.

    Returns either:
    - raw rows with group_task, task, and Study_ID
    - aggregated rows with frequency and Study_ID lists

    Args:
        task: Prediction task to filter.
        group_task: Task used for grouping.
        labels: Optional labels to include.
        aggregate: If True, aggregate by group_task and task and include
                   frequency plus Study_ID lists.
    """
    session = Session()

    if labels:
        labels = [database_label(label) for label in labels]

    try:
        use_rest = "Other" in labels if labels else False

        grouping_query = (
            session.query(
                Prediction.paper_id.label("paper_id"),
                Prediction.label.label(group_task),
            )
            .filter(Prediction.task == group_task)
            .subquery()
        )

        if labels:
            if "Other" in labels:
                selected = [l for l in labels if l != "Other"]
                label_case = case(
                    (Prediction.label.in_(selected), Prediction.label),
                    else_="Other",
                )
            else:
                label_case = Prediction.label
        else:
            label_case = Prediction.label

        query = (
        session.query(
            grouping_query.c[group_task].label(group_task),
            label_case.label(task),
            Prediction.paper_id.label("Study_ID"),
        )
        .join(
            grouping_query,
            grouping_query.c.paper_id == Prediction.paper_id,
        )
        .filter(Prediction.task == task)
    ) 
        if labels and "Other" not in labels:
            query = query.filter(Prediction.label.in_(labels))

        result = query.all()

        df = pd.DataFrame(
            result,
            columns=[group_task, task, "Study_ID"],
        )

        df[task] = df[task].map(display_label)
        df[group_task] = df[group_task].map(display_label)

        if aggregate:
            df = (
                df.groupby([group_task, task])
                .agg(
                    Frequency=("Study_ID", "size"),
                    Study_ID=("Study_ID", lambda x: list(x.unique())),
                )
                .reset_index()
            )

        return df

    finally:
        session.close()


def get_ids(task: str = None, label: str = None) -> list[int]:
    session = Session()
    try:
        query = session.query(Prediction.paper_id)
        if task is not None:
            query = query.filter(Prediction.task == task)
        if label is not None:
            label = database_label(label)
            query = query.filter(Prediction.label == label)
        return [r[0] for r in query.distinct().all()]
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
    """Return labels in the order defined in model_paths.json."""
    if task == "Number of Participants":
        return ["1-20", "21-40", "41-60", "61-80", "81-100", "101-199", "200-499", "500-999", "≥1000", "Unknown", "Not applicable"]
    elif task in LABEL_ORDER:
        return [display_label(l) for l in LABEL_ORDER[task]]

    session = Session()
    try:
        query = session.query(Prediction.label).filter(
            Prediction.task == task
        ).distinct()
        labels = [item.label for item in query.all()]
        return [display_label(label) for label in labels]
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


def get_study_count():
    """Get the number of studies in the database."""
    session = Session()
    try:
        query = session.query(func.count(Paper.id))
        result = query.first()
        return result[0]
    finally:
        session.close()


def display_label(label: str) -> str:
    return DISPLAY_LABELS.get(label, label)


def database_label(label: str) -> str:
    reverse = {v: k for k, v in DISPLAY_LABELS.items()}
    return reverse.get(label, label)


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
            Paper.id, Paper.title, Paper.abstract, Paper.authors,
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
                'authors': format_author_citation(s.authors),
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


def get_filtered_study_ids(filter: OrderedDict[str, list[str]], mode="and") -> list[int]:
    if not filter:
        return []
    filter = {
        task: [database_label(label) for label in labels]
        for task, labels in filter.items()
    }

    valid_pairs = [(task, label)
                   for task, labels in filter.items() for label in labels]
    session = Session()
    try:
        if mode == "or":
            query = (
                session.query(Prediction.paper_id)
                .filter(tuple_(Prediction.task, Prediction.label).in_(valid_pairs))
                .distinct()
            )
            return [r[0] for r in query.all()]

        # Mode == "and": Study must match ALL specified pairs
        query = (
            session.query(Prediction.paper_id)
            .filter(tuple_(Prediction.task, Prediction.label).in_(valid_pairs))
            .group_by(Prediction.paper_id)
            .having(func.count(func.distinct(tuple_(Prediction.task, Prediction.label))) == len(valid_pairs))
        )
        return [r[0] for r in query.all()]
    finally:
        session.close()


# Matches '(', ')', and the whole-word operators used in advanced filter expressions.
_BOOLEAN_QUERY_TOKEN_RE = re.compile(r'(\(|\)|\bAND\b|\bOR\b|\bNOT\b)')


def _tokenize_boolean_query(query_text: str) -> list:
    """Splits an advanced filter expression into '(', ')', 'AND', 'OR', 'NOT' and ('CMP', task, label) tokens."""
    tokens = []
    for part in _BOOLEAN_QUERY_TOKEN_RE.split(query_text):
        part = part.strip()
        if not part:
            continue
        if part in ("(", ")", "AND", "OR", "NOT"):
            tokens.append(part)
            continue
        if "=" not in part:
            raise ValueError(f"Expected 'Task = Label' but got: '{part}'")
        task, label = part.split("=", 1)
        tokens.append(("CMP", task.strip(), label.strip()))
    return tokens


class _BooleanQueryParser:
    """Recursive-descent parser for AND/OR/NOT/parentheses expressions over 'Task = Label' comparisons."""

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        token = self._peek()
        self.pos += 1
        return token

    def parse(self):
        if not self.tokens:
            raise ValueError("Empty filter expression")
        node = self._parse_or()
        if self.pos != len(self.tokens):
            raise ValueError(f"Unexpected token: {self._peek()}")
        return node

    def _parse_or(self):
        node = self._parse_and()
        while self._peek() == "OR":
            self._advance()
            node = ("OR", node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_not()
        while self._peek() == "AND":
            self._advance()
            node = ("AND", node, self._parse_not())
        return node

    def _parse_not(self):
        if self._peek() == "NOT":
            self._advance()
            return ("NOT", self._parse_not())
        return self._parse_atom()

    def _parse_atom(self):
        token = self._peek()
        if token == "(":
            self._advance()
            node = self._parse_or()
            if self._advance() != ")":
                raise ValueError("Missing closing bracket ')'")
            return node
        if isinstance(token, tuple) and token[0] == "CMP":
            self._advance()
            return token
        raise ValueError(f"Unexpected token: {token}")


def _evaluate_boolean_query(node: tuple, universe: set[int]) -> set[int]:
    kind = node[0]
    if kind == "CMP":
        _, task, label = node
        return set(get_ids(task=task, label=label))
    if kind == "AND":
        return _evaluate_boolean_query(node[1], universe) & _evaluate_boolean_query(node[2], universe)
    if kind == "OR":
        return _evaluate_boolean_query(node[1], universe) | _evaluate_boolean_query(node[2], universe)
    if kind == "NOT":
        return universe - _evaluate_boolean_query(node[1], universe)
    raise ValueError(f"Unknown expression node: {node}")


def get_ids_from_boolean_query(query_text: str) -> list[int]:
    """Parses and evaluates an advanced filter expression (AND/OR/NOT/parentheses over 'Task = Label' comparisons)."""
    query_text = (query_text or "").strip()
    if not query_text:
        return get_ids()

    tree = _BooleanQueryParser(_tokenize_boolean_query(query_text)).parse()
    universe = set(get_ids())
    return sorted(_evaluate_boolean_query(tree, universe))


def get_paper_prediction_input(id: int) -> str:
    session = Session()
    try:
        query = session.query(Paper.prediction_input).filter(Paper.id == id)
        result = query.first()
        return result[0]
    finally:
        session.close()


def get_dosages_for_papers(paper_ids: list[int]) -> dict[int, dict[str, str]]:
    """
    Fetches raw and formatted dosages for a batch of paper IDs in a single query.
    Returns: {paper_id: {'dosage': '...', 'dosage_display': '...'}}
    """
    if not paper_ids:
        return {}

    session = Session()
    try:
        # Pre-initialize result dict for all requested paper IDs to handle missing records gracefully
        formatted_dosages = {
            pid: {'dosage': '', 'dosage_display': ''}
            for pid in paper_ids
        }

        # Select only necessary scalar columns to reduce ORM hydration overhead
        query = (
            session.query(
                NerTag.paper_id,
                DosageNormalization.norm_text,
                DosageNormalization.dose_type,
                DosageNormalization.min,
                DosageNormalization.max,
                DosageNormalization.unit,
                DosageNormalization.per_weight_unit,
                DosageNormalization.weight_reference,
            )
            .join(DosageNormalization, DosageNormalization.ner_tag_id == NerTag.id)
            .filter(
                NerTag.paper_id.in_(paper_ids),
                NerTag.tag == 'Dosage'
            )
        )

        results = query.all()
        if not results:
            return formatted_dosages

        # Use dict.fromkeys() to maintain insertion order while giving O(1) deduplication
        dosage_map = {
            pid: {'raw': {}, 'display': {}}
            for pid in paper_ids
        }

        for pid, norm_text, dose_type, min_v, max_v, unit, per_weight_unit, weight_ref in results:
            # 1. Collect raw text
            if norm_text:
                dosage_map[pid]['raw'][norm_text] = None

            # 2. Build display string
            display_text = norm_text
            if dose_type and dose_type.startswith('relative_weight'):
                min_val, max_val = normalize_relative_weight_dosages(
                    min_v, max_v, weight_ref, per_weight_unit
                )
                min_mg = to_mg(min_val, unit)
                max_mg = to_mg(max_val, unit)

                if min_mg is not None and max_mg is not None:
                    if min_mg == max_mg:
                        normalized_value = f"{min_mg:g} mg"
                    else:
                        normalized_value = f"{min_mg:g}-{max_mg:g} mg"
                    display_text = f"{norm_text} -> {normalized_value} (70 kg person)"
                elif norm_text:
                    display_text = f"{norm_text} (70 kg person)"

            if display_text:
                dosage_map[pid]['display'][display_text] = None

        # 3. Format into final pipe-separated strings
        for pid in paper_ids:
            formatted_dosages[pid] = {
                'dosage': ' | '.join(dosage_map[pid]['raw'].keys()),
                'dosage_display': ' | '.join(dosage_map[pid]['display'].keys())
            }

        return formatted_dosages

    finally:
        session.close()


def get_paper_ner_tags(paper_id: int, ner_type: str = None, in_titel=False) -> list[dict]:
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
                'start': tag.start_id,  # if in_titel else tag.start_id - end_id_of_title,
                'end': tag.end_id,  # if in_titel else tag.end_id - end_id_of_title,
                'tag': tag.tag,
            })
        return tags
    finally:
        session.close()


def get_dosage_samples(
    substances: list[str] = None,
    dosage_types: list[str] = ['absolute', 'relative_weight'],
    initial_dataset: bool = False
) -> pd.DataFrame:
    """Return a DataFrame with dosage samples per substance."""

    EXCLUDED_SUBSTANCES = {'Unknown', 'Analogue', 'Combination Therapy'}
    session = Session()
    if substances:
        substances = [database_label(s) for s in substances]

    try:
        # Base query: place select_from() before distinct() and filter()
        query = (
            session.query(
                Prediction.label,
                Paper.id,
                DosageNormalization.min,
                DosageNormalization.max,
                DosageNormalization.unit,
                DosageNormalization.per_weight_unit,
                DosageNormalization.weight_reference,
                DosageNormalization.dose_type,
                DosageNormalization.norm_text,
            )
            .select_from(Paper)
            .distinct()
            .join(Prediction, Prediction.paper_id == Paper.id)
            .join(NerTag, NerTag.paper_id == Paper.id)
            .join(DosageNormalization, DosageNormalization.ner_tag_id == NerTag.id)
            .filter(
                Prediction.task == "Substances",
                Prediction.label.notin_(EXCLUDED_SUBSTANCES),
            )
        )

        if initial_dataset:
            query = query.filter(
                or_(Paper.entrez_year.is_(None), Paper.entrez_year <= 2025))

        if dosage_types:
            query = query.filter(
                DosageNormalization.dose_type.in_(dosage_types))

        # 2. Optimize substance filtering: handle user inputs + exclude list together
        if substances:
            filtered_substances = [
                s for s in substances if s not in EXCLUDED_SUBSTANCES]
            if not filtered_substances:
                return pd.DataFrame(columns=['Substance', 'Dosage_mg', 'Unit', 'Study_ID', 'Dose_Type', 'Norm_Text'])
            query = query.filter(Prediction.label.in_(filtered_substances))

        # Fetch clean, pre-deduplicated data from DB
        rows = query.all()

        samples = []
        # Python loop now ONLY runs math transformations on valid data
        for label, paper_id, minv, maxv, unit, per_weight_unit, weight_reference, dose_type, norm_text in rows:
            if dose_type and dose_type.startswith('relative'):
                min_val, max_val = normalize_relative_weight_dosages(
                    minv, maxv, weight_reference, per_weight_unit
                )
            else:
                min_val, max_val = minv, maxv

            min_mg = to_mg(min_val, unit)
            max_mg = to_mg(max_val, unit)

            if min_mg is not None and max_mg is not None:
                samples.append({
                    'Substance': label,
                    'Dosage_mg': min_mg,
                    'Unit': 'mg',
                    'Study_ID': paper_id,
                    'Dose_Type': dose_type,
                    'Norm_Text': norm_text
                })

        if not samples:
            return pd.DataFrame(columns=['Substance', 'Dosage_mg', 'Unit', 'Study_ID', 'Dose_Type', 'Norm_Text'])

        df = pd.DataFrame(samples)

        # Secondary Python drop_duplicates just in case to_mg math yielded identical normalized values
        df = df.drop_duplicates(
            subset=['Substance', 'Dosage_mg', 'Unit', 'Study_ID', 'Dose_Type', 'Norm_Text'])
        df["Substance"] = df["Substance"].map(display_label)

        return df

    finally:
        session.close()


def get_latest_retrieval_date():
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
