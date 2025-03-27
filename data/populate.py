from datetime import datetime, timezone, timedelta
import os
import sys
import json
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Paper, BatchRetrieval, Prediction, NerTag
import argparse
import pandas as pd
from settings import *
from typing import Optional

parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)


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
    prediction_input = prediction_input.replace('\xa0', '').replace('\u2009', '')
    title = title.replace('\xa0', '').replace('\u2009', '')
    abstract = abstract.replace('\xa0', '').replace('\u2009', '')
    
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


def create_ner_tags(session: Session, tag: str, start_id: int, end_id: int, text: str, probability: float, model: str, paper_id: int, pred_text: str) -> NerTag:
    print(text,'\t', pred_text[start_id:end_id])

    ner_tag = session.query(NerTag).filter(
        NerTag.paper_id == paper_id,
        NerTag.start_id == start_id,
        NerTag.end_id == end_id,
        NerTag.tag == tag,
        NerTag.text == text
    ).first()
    if ner_tag:
        print(f"NER tag already exists: {ner_tag}")
        return ner_tag


    return NerTag(
        tag=tag,
        start_id=start_id,
        end_id=end_id,
        text=text,
        probability=probability,
        model=model,
        paper_id=paper_id,
    )


def populate_db(args: argparse.Namespace):
    # prediction_file: str, studies_file: str, studies_id_column: Optional[str] = 'id'
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    if args.studies_file:
        populate_studies(session, args.studies_file, args.studies_id_column)
        nr_papers = session.query(Paper).count()
        print(f"Number of papers: {nr_papers}")

    if args.predictions_file:
        if 'ner' in args.predictions_file:
            populate_ner_manual(session, args.predictions_file)
        else:
            populate_predictions(session, args.predictions_file)

    session.commit()
    session.close()


def populate_studies(session: Session, file: str, studies_id_column: str):
    studies_data = pd.read_csv(file, encoding='utf-8')

    # Check if studies_id_column is in the studies_data
    if studies_id_column not in studies_data.columns:
        raise ValueError(f"Studies file does not contain column '{studies_id_column
                                                                  }'. Please specify the correct column name with the --studies_id_column argument.")

    batch_date = file[:-4].split('_')[-2]  # yyyymmdd
    batch_date = datetime.strptime(batch_date, '%Y%m%d')
    retrieval_duration = file[:-4].split('_')[-1]  # hh:mm:ss
    hours, minutes, seconds = map(int, retrieval_duration.split(':'))
    retrieval_duration = timedelta(
        hours=hours, minutes=minutes, seconds=seconds)

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


def populate_predictions(session: Session, file: str):
    pred_data = pd.read_csv(file, encoding='utf-8')
    for i, row in pred_data.iterrows():
        paper_id = int(row['id'])
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


def find_pos(text: str, token_list: list[str], prev_token: str, next_token: str) -> tuple[int, int]:
    # Create the regex pattern to match the token list with optional whitespace between tokens
    pattern = r'\s?'.join(re.escape(token) for token in token_list)
    pattern = r'\s?' + pattern + r'\s?'

    matches = list(re.finditer(pattern, text))

    if not matches:
        raise ValueError(
            "No match found for the given token list in the text.")

    if len(matches) == 1:
        return matches[0].start(), matches[0].end()
    # Iterate through the matches to find the correct one using prev_token and next_token
    for match in matches:
        # Get the start and end positions of the match
        start_pos = match.start()
        end_pos = match.end()

        # Get the surrounding text (prev_token and next_token) for disambiguation
        before_match = text[:start_pos].split()[-1]
        after_match = text[end_pos:].split(
        )[0] if end_pos < len(text) else None

        
        # If prev_token is None, don't check it. Same for next_token.
        if (prev_token is None or before_match == prev_token) and (next_token is None or after_match == next_token):
            return start_pos, end_pos  # Return the start and end positions of the match
        elif before_match.endswith(prev_token) and after_match.startswith(next_token):
            return start_pos, end_pos
    raise ValueError("No match found for the given token list in the text.")


def populate_ner_manual(session: Session, file: str):
    # Load jsonl file
    with open(file, 'r', encoding='utf-8') as f:
        data = f.readlines()

        for row in data:
            row = json.loads(row)
            paper = session.query(Paper).filter(Paper.id == row['id']).first()
            if not paper:
                raise ValueError(f"No paper found with paper_id: {row['id']}")

            pred_text = paper.prediction_input
            tokens = row['tokens']
            ner_tags = row['ner_tags']

            current_tag = None
            entity_tokens = []
            nr_tags = 0

            for i, (token, tag) in enumerate(zip(tokens, ner_tags)):
                prev_id = len(entity_tokens) + 1
                prev_token = tokens[i-prev_id] if prev_id > 0 else None
                next_token = tokens[i] if i < len(tokens) - 1 else None

                if tag.startswith("B-Dosage"):  # Beginning of a new entity
                    if current_tag:
                        start_id, end_id = find_pos(
                            pred_text, entity_tokens, prev_token, next_token)
                        ner_tag = create_ner_tags(
                            session=session,
                            tag=current_tag,
                            start_id=start_id,
                            end_id=end_id,
                            text=" ".join(entity_tokens),
                            probability=1.0,
                            model="manual",
                            paper_id=row['id'],
                            pred_text=pred_text
                        )
                        nr_tags += 1
                        session.add(ner_tag)

                    current_tag = tag[2:]  # Extract the entity type
                    entity_tokens = [token]  # Start new entity with this token

                # Inside the same entity
                elif tag.startswith("I-Dosage") and current_tag == tag[2:]:
                    entity_tokens.append(token)

                else:  # End of the current entity or no entity
                    if current_tag:
                        start_id, end_id = find_pos(
                            pred_text, entity_tokens, prev_token, next_token)
                        ner_tag = create_ner_tags(
                            session=session,
                            tag=current_tag,
                            start_id=start_id,
                            end_id=end_id,
                            text=" ".join(entity_tokens),
                            probability=1.0,
                            model="manual",
                            paper_id=row['id'],
                            pred_text=pred_text
                        )
                        nr_tags += 1
                        session.add(ner_tag)
                        current_tag = None
                        entity_tokens = []

            # Handle the last entity if needed
            if current_tag:

                prev_id = len(entity_tokens) + 1
                prev_token = tokens[i-prev_id] if prev_id > 0 else None
                next_token = tokens[i] if i < len(tokens) - 1 else None
                start_id, end_id = find_pos(
                    pred_text, entity_tokens, prev_token, next_token)
                ner_tag = create_ner_tags(
                    session=session,
                    tag=current_tag,
                    start_id=start_id,
                    end_id=end_id,
                    text=" ".join(entity_tokens),
                    probability=1.0,
                    model="manual",
                    paper_id=row['id'],
                    pred_text=pred_text
                )
                nr_tags += 1
                session.add(ner_tag)

        session.commit()


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


def init_args_parser():
    """Initialize and return the argument parser for the script."""
    arg_parser = argparse.ArgumentParser(
        description='Populate the database with data')
    # add short and long arguments
    arg_parser.add_argument('-p', '--predictions_file', type=str,
                            help='Path to the predictions file')
    arg_parser.add_argument('-s', '--studies_file', type=str,
                            help='Path to the studies file')
    arg_parser.add_argument('--studies_id_column', type=str, default='id',)
    return arg_parser


if __name__ == '__main__':
    parser = init_args_parser()
    args = parser.parse_args()

    populate_db(args)
