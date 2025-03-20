from datetime import datetime, timezone, timedelta
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Paper, BatchRetrieval, Token, Prediction, PredictionToken
import argparse
import pandas as pd
from settings import *
from typing import Optional

parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)

#


def create_batch_retrieval(date: datetime, nr_new_papers: int, retrieval_time_needed: timedelta) -> BatchRetrieval:
    return BatchRetrieval(
        date=datetime.now(timezone.utc),
        number_new_papers=nr_new_papers,
        retrieval_time_needed=retrieval_time_needed
    )


def create_paper(
        ID: int,
        title: str,
        abstract: str,
        prediction_input: str,
        key_terms: str,
        doi: str, year: int,
        authors: str,
        link_to_fulltext: str,
        link_to_pubmed: str,
        pubmed_id: str,
        retrieval_id: int
):
    return Paper(
        id=ID,
        pubmed_id=pubmed_id if pubmed_id else None,
        title=title,
        abstract=abstract,
        prediction_input=prediction_input,
        key_terms=key_terms if key_terms else None,
        doi=doi if doi else None,
        year=year,
        authors=authors,
        link_to_fulltext=link_to_fulltext if link_to_fulltext else None,
        link_to_pubmed=link_to_pubmed if link_to_pubmed else None,
        retrieval_id=retrieval_id
    )


def create_tokens(token_list: list[str], ner_list: list[str], paper_id) -> list[Token]:
    if len(token_list) != len(ner_list):
        raise ValueError("Token and NER lists must have the same length")
    tokens = []
    for i, (t, ner) in enumerate(zip(token_list, ner_list)):
        tokens.append(Token(
            paper_id=paper_id,
            text=t,
            ner_tag=ner,
            position_id=i
        ))
    return tokens


def create_predictions(paper_id: int, task: str, label: str, probability: float, model: str, is_multilabel: bool) -> list[Prediction]:
    prediction = Prediction(
        paper_id=paper_id,
        task=task,
        label=label,
        probability=probability,
        model=model,
        is_multilabel=is_multilabel)
    return prediction


def create_prediction_tokens(token_id, prediction_id, weight):
    return PredictionToken(
        token_id=token_id,
        prediction_id=prediction_id,
        weight=weight
    )


def populate_db(prediction_file: str, studies_file: str, studies_id_column: Optional[str] = 'id'):

    # Using the settings.py file, create a connection to the database

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://{0}:{1}@{2}:{3}/{4}".format(
            DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME)
    )
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # check how many papers are already in the database
    nr_papers = session.query(Paper).count()
    print(f"Number of papers in the database: {nr_papers}")

    batch_date = studies_file[:-4].split('_')[-2]  # yyyymmdd
    batch_date = datetime.strptime(batch_date, '%Y%m%d')
    retrieval_duration = studies_file[:-4].split('_')[-1]  # hh:mm:ss
    hours, minutes, seconds = map(int, retrieval_duration.split(':'))
    retrieval_duration = timedelta(
        hours=hours, minutes=minutes, seconds=seconds)

    pred_data = pd.read_csv(prediction_file)
    studies_data = pd.read_csv(studies_file)

    # Check if studies_id_column is in the studies_data
    if studies_id_column not in studies_data.columns:
        raise ValueError(f"Studies file does not contain column '{studies_id_column
                                                                  }'. Please specify the correct column name with the --studies_id_column argument.")

    nr_studies = len(studies_data)

    # datetime duration
    batch = create_batch_retrieval(batch_date, nr_studies, retrieval_duration)
    session.add(batch)
    session.commit()
    batch_id = batch.id

    # replace the NaN values with empty strings
    studies_data = studies_data.fillna('')

    # iterate through the studies data
    for i, row in studies_data.iterrows():
        nr_papers = session.query(Paper).count()
        if check_if_paper_exists(session, row):
            print(f"Paper already exists: {row[studies_id_column]}")
            continue
        abstract = row['abstract']
        # For now, we skip papers without abstracts #TODO: might need to change this
        if not abstract:
            print(f"Paper without abstract: {row[studies_id_column]}")
            continue
        title = row['title']
        prediction_input = title + '.^\n' + abstract
        paper_id = row[studies_id_column]
        if pd.isna(paper_id):
            paper_id = get_unused_id(session)

        paper = create_paper(
            ID=int(paper_id),
            pubmed_id=row['pubmed_id'],
            title=title,
            abstract=abstract,
            prediction_input=prediction_input,
            key_terms=row['keywords'],
            doi=row['doi'],
            year=row['year'],
            authors='',
            link_to_fulltext='',
            link_to_pubmed=row['pubmed_url'],
            retrieval_id=batch_id
        )
        session.add(paper)
    session.commit()

    for i, row in pred_data.iterrows():
        paper_id = row['id']
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            # raise ValueError(f"No paper found with paper_id: {paper_id}")
            print(f"No paper found with paper_id: {paper_id}")
            continue

        pred = create_predictions(
            paper_id=paper_id,
            task=row['task'],
            label=row['label'],
            probability=row['probability'],
            model=row['model'],
            is_multilabel=row['is_multilabel']
        )
        session.add(pred)
    session.commit()

    session.close()


def check_if_paper_exists(session: Session, row: pd.Series) -> bool:
    pubmed_id = row['pubmed_id']
    title = row['title']
    doi = row['doi']
    year = row['year']

    if pubmed_id:
        paper = session.query(Paper).filter(
            Paper.pubmed_id == pubmed_id).first()
        if paper:
            print(f"Paper with pubmed_id {pubmed_id} already exists")
            return True

    # if doi:
    #     paper = session.query(Paper).filter(Paper.doi == doi).first()
    #     if paper:
    #         print(f"Paper with doi {doi} already exists")
    #         return True

    paper = session.query(Paper).filter(
        Paper.title == title, Paper.year == year).first()
    if paper:
        print(f"Paper with title {title} and year {year} already exists")
        return True

    return False


def get_unused_id(session: Session):
    # get all ids from papers, sort from lowest to highest
    ids = session.query(Paper.id).all()
    ids = sorted(ids)
    session.close()

    for i in range(ids[-1]):
        if i not in ids:
            return i
    return ids[-1] + 1


# args parser with the two files
def init_args_parser():
    """Initialize and return the argument parser for the script."""
    arg_parser = argparse.ArgumentParser(
        description='Populate the database with data')
    # add short and long arguments
    arg_parser.add_argument('-p', '--predictions_file', type=str,
                            help='Path to the predictions file', required=True)
    arg_parser.add_argument('-s', '--studies_file', type=str,
                            help='Path to the studies file', required=True)
    arg_parser.add_argument('--studies_id_column', type=str, default='id',)
    return arg_parser


if __name__ == '__main__':
    parser = init_args_parser()
    args = parser.parse_args()
    populate_db(args.predictions_file, args.studies_file,
                args.studies_id_column)
