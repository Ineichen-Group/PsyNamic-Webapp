import os
import sys
import json
import re
import argparse
from typing import Optional
from datetime import datetime, timezone, timedelta

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from data.models import Paper, BatchRetrieval, Prediction, NerTag, DosageNormalization
from data.dosage_norm import extract_dosages
from ast import literal_eval

load_dotenv()

parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")


def check_if_pred_exist(pred_dir: str, retrieval_date: str, str_contain: str='') -> str:
    """Check if prediction file for the given retrieval date already exists."""
    pred_files = [f for f in os.listdir(pred_dir) if f.endswith('.csv')]
    for f in pred_files:
        if retrieval_date in f and str_contain in f:
            return os.path.join(pred_dir, f)
    return ""


def create_batch_retrieval(studies_file: str, nr_new_studies: int) -> BatchRetrieval:
    # studies_file format: studies_20260203_00-00-14.csv
    batch_date = studies_file[:-4].split('_')[-2]  # yyyymmdd
    batch_date = datetime.strptime(batch_date, '%Y%m%d')
    retrieval_duration = studies_file[:-4].split('_')[-1]  # hh-mm-ss
    hours, minutes, seconds = map(int, retrieval_duration.split('-'))
    retrieval_duration = timedelta(
        hours=hours, minutes=minutes, seconds=seconds)

    return BatchRetrieval(
        date=datetime.now(timezone.utc),
        number_new_papers=nr_new_studies,
        retrieval_time_needed=retrieval_duration
    )

def normalize_for_db(s: str) -> str:
    if s is None:
        return s
 
    if '\\x' in s or '\\u' in s:
        s2 = s.replace('\\xa0', '\\u00A0')
        try:
            s = bytes(s2, 'utf-8').decode('unicode_escape')
        except Exception:
            pass
    # turn NBSP / thin-space into a regular space and collapse whitespace
    s = s.replace('\u00A0', ' ').replace('\u2009', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

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
    prediction_input = normalize_for_db(prediction_input)
    title = normalize_for_db(title)
    abstract = normalize_for_db(abstract)
    
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


def create_ner_tag(session: Session, tag: str, start_id: int, end_id: int, text: str, probability: float, model: str, paper_id: int, pred_text: str) -> NerTag:
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


def populate_db(prediction_file: str, studies_file: str, studies_id_column: Optional[str] = 'id'):
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://{0}:{1}@{2}:{3}/{4}".format(
            DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME)
    )
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    nr_papers = session.query(Paper).count()
    print(f"Number of papers in the database: {nr_papers}")


    if studies_file:
        populate_studies(session, studies_file, studies_id_column)
        nr_papers = session.query(Paper).count()
        print(f"Number of papers: {nr_papers}")

    if prediction_file:
        if 'ner' in prediction_file:
            populate_ner_predictions(session, prediction_file)
        else:
            populate_class_predictions(session, prediction_file)

    session.commit()
    session.close()


def populate_studies(session: Session, file: str, studies_id_column: str):

    studies_data = pd.read_csv(file)
    if studies_id_column not in studies_data.columns:
        raise ValueError(f"Studies file does not contain column '{studies_id_column}'. Please specify the correct column name with the --studies_id_column argument.")

    nr_studies = len(studies_data)
    batch = create_batch_retrieval(file, nr_studies)
    session.add(batch)
    session.commit()

    # replace the NaN values with empty strings
    studies_data = studies_data.fillna('')

    for _, row in studies_data.iterrows():
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
        # TODO: check if this is actually needed
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
            retrieval_id=batch.id
        )
        session.add(paper)
    session.commit()


def populate_class_predictions(session: Session, file: str):
    pred_data = pd.read_csv(file, encoding='utf-8')
    for i, row in pred_data.iterrows():
        paper_id = int(row['id'])
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            print(f"No paper found with paper_id: {paper_id}")
            continue

        # Check for duplicate prediction (same paper_id, task, label, model)
        existing_pred = session.query(Prediction).filter(
            Prediction.paper_id == paper_id,
            Prediction.task == row['task'],
            Prediction.label == row['label'],
            Prediction.model == row['model']
        ).first()
        if existing_pred:
            print(f"Prediction already exists for paper_id {paper_id}, task {row['task']}, label {row['label']}, model {row['model']}")
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


def find_pos(text: str, token_list: list[str], prev_token: str, next_token: str, offset: int = 0) -> tuple[int, int]:
    # Lowercase
    text = text.lower()
    token_list = [token.lower() for token in token_list]
    prev_token = prev_token.lower() if prev_token else None
    next_token = next_token.lower() if next_token else None

    # Remove . and ^ if (newline artefact from Prodigy) they are last two tokens in the token list
    if token_list[-1] == '^' and token_list[-2] == '.':
        token_list = token_list[:-2]

    # Create the regex pattern to match the token list with optional whitespace between tokens
    pattern = r'\s?'.join(re.escape(token) for token in token_list)
    pattern = pattern + r'\s*(\.+\^)?\s*' # Optional match for the .^ artefact (was used as a separator between title and abstract in Prodigy)

    matches = list(re.finditer(pattern, text))

    if not matches:
        breakpoint()
        raise ValueError(
            "No match found for the given token list in the text.")

    if len(matches) == 1:
        return matches[0].start()+offset, matches[0].end()+offset
    # Iterate through the matches to find the correct one using prev_token and next_token, defaults to the first match
    for match in matches:
        # Get the start and end positions of the match
        start_pos = match.start()
        end_pos = match.end()
       
        # Get the surrounding text (prev_token and next_token) for disambiguation
        before_match = text[:start_pos].split()[-1] if start_pos > 0 else ''
        after_match = text[end_pos:].split(
        )[0] if end_pos < len(text) else ''

        # Don't check the prev_token and next_token if they are [UNK] or \n
        if prev_token == "[unk]" or prev_token == "\n":
            prev_token = ''
        if next_token == "[unk]" or next_token == "\n":
            next_token = ''
        
        # TODO: this is very ugly, improve
        if (prev_token is None or before_match == prev_token) and (next_token is None or after_match == next_token):
            return start_pos+offset, end_pos+offset  # Return the start and end positions of the match
        
        elif before_match.endswith(prev_token) and after_match.startswith(next_token):
            return start_pos+offset, end_pos+offset
        
        elif after_match.startswith(next_token) and len(prev_token) < 2:
            return start_pos+offset, end_pos+offset
        
        elif before_match.endswith(prev_token) and len(next_token) < 2:
            return start_pos+offset, end_pos+offset
    
    breakpoint()
    raise ValueError("No match found for the given token list in the text.")

def create_dosage_norm(session: Session, ner_tag: NerTag, entity_text: str):
    # First, check if a DosageNormalization already exists for this NerTag
    existing_norm = session.query(DosageNormalization).filter_by(ner_tag_id=ner_tag.id).first()
    
    if existing_norm:
        # Option 1: replace fields with new normalization data
        norm_data = extract_dosages(entity_text)
        existing_norm.min = norm_data['min']
        existing_norm.max = norm_data['max']
        existing_norm.unit = norm_data['unit']
        existing_norm.per_weight_unit = norm_data['per_weight_unit']
        existing_norm.weight_reference = norm_data['weight_reference']
        existing_norm.per_time_unit = norm_data['per_time_unit']
        existing_norm.dose_type = norm_data['dose_type']
        existing_norm.original_dosage = norm_data['original_dosage']
        return existing_norm
    else:
        norm_data = extract_dosages(entity_text)
        dosage_norm = DosageNormalization(
            min=norm_data['min'],
            max=norm_data['max'],
            unit=norm_data['unit'],
            per_weight_unit=norm_data['per_weight_unit'],
            weight_reference=norm_data['weight_reference'],
            per_time_unit=norm_data['per_time_unit'],
            dose_type=norm_data['dose_type'],
            original_dosage=norm_data['original_dosage'],
            ner_tag=ner_tag
        )
        session.add(dosage_norm)
        return dosage_norm

def populate_ner_predictions(session: Session, file: str, manual: bool = True):
    # check if input file is json or csv
    if file.endswith('.csv'):
        data = pd.read_csv(file).to_dict(orient='records')
    elif file.endswith('.jsonl'):
        with open(file, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f.readlines()]
    # Load jsonl file
    for row in data:
        paper = session.query(Paper).filter(Paper.id == row['id']).first()
        if not paper:
            raise ValueError(f"No paper found with paper_id: {row['id']}")

        pred_text = paper.prediction_input
        tokens = literal_eval(row['tokens']) if isinstance(row['tokens'], str) else row['tokens']
        ner_tags = literal_eval(row['ner_tags']) if isinstance(row['ner_tags'], str) else row['ner_tags']

        current_tag = None
        entity_tokens = []
        nr_tags = 0

        model = None
        probability = None

        if manual:
            model = "manual"
            probability = 1.0
            
        else:
            model = row.get('model_name', None)
            probability = row.get('probability', None)

        offset = 0
        for i, (token, tag) in enumerate(zip(tokens, ner_tags)):
            # Determine entity type from B- or I- prefix
            entity_type = tag[2:] if tag != 'O' else None
            
            # Case 1: new entity starts
            if tag.startswith("B-"):
                entity_start_index = i

                # If there was a previous entity, process it first
                if current_tag:
                    cur_entity_start_index = entity_start_index - (len(entity_tokens)+1)
                    prev_token = tokens[cur_entity_start_index] if cur_entity_start_index > 0 else None
                    
                    try:
                        start_id, end_id = find_pos(
                            pred_text[offset:],
                            entity_tokens,
                            prev_token,
                            next_token=token,
                            offset=offset
                        )
                    except:
                        breakpoint()
                    ner_tag = create_ner_tag(
                        session=session, tag=current_tag, start_id=start_id, end_id=end_id,
                        text=pred_text[start_id:end_id], probability=probability, model=model, paper_id=row['id'], pred_text=pred_text
                    )
                    
                    session.add(ner_tag)
                    session.flush() 
                    nr_tags += 1
                    
                    # If it's a Dosage tag, normalize it
                    if current_tag == 'Dosage':
                        try:
                           create_dosage_norm(session, ner_tag, pred_text[start_id:end_id])
                        except (ValueError, IndexError) as e:
                            print(f"Could not normalize dosage '{pred_text[start_id:end_id]}': {e}")

                # Start the new entity
                current_tag = entity_type
                entity_tokens = [token]

            # Case 2: continue entity
            elif tag.startswith("I-") and current_tag == entity_type:
                entity_tokens.append(token)

            # Case 3: End of an entity (current tag is O or a new B- tag)
            else:
                if current_tag:
                    
                    prev_token = tokens[entity_start_index - 1] if entity_start_index > 0 else None
                    next_token = tokens[i] if i < len(tokens) else None
                    try: 
                        start_id, end_id = find_pos(
                            pred_text[offset:],
                            entity_tokens,
                            prev_token,
                            next_token,
                            offset=offset
                        )
                    except Exception as e:
                        print(f"Error occurred: {e}")
                        breakpoint()
                    ner_tag = create_ner_tag(
                        session=session, tag=current_tag, start_id=start_id, end_id=end_id,
                        text=pred_text[start_id:end_id], probability=probability, model=model, paper_id=row['id'], pred_text=pred_text
                    )
                    # Cut off the pred_text after the end_id for the next search, to avoid finding the same entity again
                    offset = end_id

                    session.add(ner_tag)
                    session.flush() 
                    nr_tags += 1

                    # If it's a Dosage tag, normalize it
                    if current_tag == 'Dosage':
                        try:
                            create_dosage_norm(session, ner_tag, pred_text[start_id:end_id])
                        except (ValueError, IndexError) as e:
                            print(f"Could not normalize dosage '{pred_text[start_id:end_id]}': {e}")
                    
                    # Reset for next entity
                    current_tag = None
                    entity_tokens = []

        # Process any remaining entity at the end of the sequence
        if current_tag:
            
            prev_token = tokens[entity_start_index - 1] if entity_start_index > 0 else None
            next_token = None
            try: 

                start_id, end_id = find_pos(
                    pred_text[offset:],
                    entity_tokens,
                    prev_token,
                    next_token,
                    offset=offset
                )
            except:
                breakpoint()
            
            ner_tag = create_ner_tag(
                session=session, tag=current_tag, start_id=start_id, end_id=end_id,
                text=pred_text[start_id:end_id], probability=probability, model=model, paper_id=row['id'], pred_text=pred_text
            )
            offset = end_id
            session.add(ner_tag)
            session.flush()
            nr_tags += 1

            # If it's a Dosage tag, normalize it
            if current_tag == 'Dosage':
                try:
                    # make sure to replace existing normalization if it exists, since this is the last entity and we might have found a better match for the text
                    create_dosage_norm(session, ner_tag, pred_text[start_id:end_id])
                except (ValueError, IndexError) as e:
                    print(f"Could not normalize dosage '{pred_text[start_id:end_id]}': {e}")

        session.commit()


def check_if_paper_exists(session: Session, row: pd.Series) -> bool:
    pubmed_id = row['pubmed_id']
    title = row['title']
    year = row['year']

    if pubmed_id:
        paper = session.query(Paper).filter(
            Paper.pubmed_id == pubmed_id).first()
        if paper:
            print(f"Paper with pubmed_id {pubmed_id} already exists")
            return True

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
                            help='Path to the predictions file', required=False)
    arg_parser.add_argument('-s', '--studies_file', type=str,
                            help='Path to the studies file', required=False)
    arg_parser.add_argument('--studies_id_column', type=str, default='id',)
    arg_parser.add_argument('--all_studies', action='store_true', help='Populate all studies/predictions files from the data folder')
    return arg_parser


if __name__ == '__main__':
    parser = init_args_parser()
    args = parser.parse_args()
    STUDIES_DIR = 'data/relevant_studies'
    PREDICTIONS_DIR = 'data/predictions'


    if not args.predictions_file and not args.studies_file:

        # get the latest file in the directory
        args.studies_file = max([os.path.join(STUDIES_DIR, f) for f in os.listdir(
            STUDIES_DIR) if f.endswith('.csv')], key=os.path.getctime)
        # get prediction file with the same date as studies file
        date_str = args.studies_file[:-4].split('_')[-2]

        # Check if classification predictions file exists
        class_predictions_file = check_if_pred_exist(PREDICTIONS_DIR, date_str, 'class')
        if not args.predictions_file:
        #     print(
        #         f"No predictions file found for date {date_str}. Please provide a predictions file.")
        #     sys.exit(1)        
            populate_db(class_predictions_file, args.studies_file,
                        args.studies_id_column)
            
        
        ner_prediction_file = check_if_pred_exist(PREDICTIONS_DIR, date_str, 'ner')
        if ner_prediction_file:
            populate_db(ner_prediction_file, args.studies_file,
                        args.studies_id_column)

    else:
        populate_db(args.predictions_file, args.studies_file,
                    args.studies_id_column)
