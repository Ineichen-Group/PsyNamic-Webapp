import os
import pandas as pd
from data.queries import engine, Session
from data.models import Paper

def get_study_by_pmid(pmid: int) -> dict:
    session = Session()
    try:
        query = session.query(Paper).filter(Paper.pubmed_id == pmid)
        paper = query.first()
        if not paper:
            return {}
        else:
            return {
                "id": paper.id,
                "pubmed_id": paper.pubmed_id,
                "doi": paper.doi,
                "title": paper.title,
                "abstract": paper.abstract,
            }
    finally:
        session.close()

def get_study_by_doi(doi: str) -> list[dict]:
    session = Session()
    try:
        query = session.query(Paper).filter(Paper.doi == doi)
        papers = query.all()
        if not papers:
            return []
        else:
            result = []
            for paper in papers:
                paper_dict = {
                    "id": paper.id,
                    "pubmed_id": paper.pubmed_id,
                    "doi": paper.doi,
                    "title": paper.title,
                    "abstract": paper.abstract,
                }
                result.append(paper_dict)
            return result
    finally:
        session.close()
    
def get_study_by_title(title: str) -> list[dict]:
    session = Session()
    try:
        query = session.query(Paper).filter(Paper.title == title)
        papers = query.all()
        if not papers:
            return []
        else:
            result = []
            for paper in papers:
                paper_dict = {
                    "id": paper.id,
                    "pubmed_id": paper.pubmed_id,
                    "doi": paper.doi,
                    "title": paper.title,
                    "abstract": paper.abstract,
                }
                result.append(paper_dict)
            return result
    finally:
        session.close()

if __name__ == "__main__":
    input_file = "validation/psynamic_validation_included_articles.csv"

    df = pd.read_csv(input_file, delimiter=';')
    # replace 'nA' with NaN
    df.replace('nA', None, inplace=True)

    nr_studies = len(df)
    print(f"Number of studies in the input file: {nr_studies}")
    nr_studie_in_db = 0
    for index, row in df.iterrows():
        pmid = row['PMID']
        study_data = get_study_by_pmid(pmid)
        if study_data:
            nr_studie_in_db += 1
        else:
            # check if it is nan
            if pd.isna(row['doi']):
                continue
            doi = row['doi'].replace('https://doi.org/', '')
            study_data = get_study_by_doi(doi)
            if study_data:
                nr_studie_in_db += 1
            else:
                title = row['Title']
                study_data = get_study_by_title(title)
                if study_data:
                    nr_studie_in_db += 1
                else:
                    # print title of the study that is not found in the database
                    print(f"{row['Title']} (PMID: {pmid}, DOI: {doi})")
    print(f"Number of studies found in the database: {nr_studie_in_db}")