import os
import pandas as pd
from data.queries import engine, Session
from data.models import Paper
from sqlalchemy import func


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
        query = session.query(Paper).filter(
            func.lower(Paper.title) == func.lower(title)
        )
        papers = query.all()

        if not papers:
            return []

        result = []
        for paper in papers:
            result.append({
                "id": paper.id,
                "pubmed_id": paper.pubmed_id,
                "doi": paper.doi,
                "title": paper.title,
                "abstract": paper.abstract,
            })

        return result

    finally:
        session.close()

def read_in_asreview() -> list[pd.DataFrame]:
    input_file = "/home/veral/PsyNamic/data/raw_data/asreview_dataset_all_Psychedelic Study.csv"
    df = pd.read_csv(input_file)
    df['title'] = df['title'].str.lower()
    included = df[df['included'] == 1]
    excluded = df[df['included'] == 0]
    #    array([ 1., nan,  0.])
    # lower title
    excluded_after_stopping = df[df['included'].isna()]

    return [included, excluded, excluded_after_stopping, df]

def read_in_all_retrieved_studies() -> list[pd.DataFrame]:
    input_dir = '/home/veral/PsyNamic/PsyNamic-Webapp/data/relevant_studies/studies_20260320_00-09-37.csv'
    df = pd.read_csv(input_dir)
    # remove all papers that have entrez_date > 2025
    df['entrez_date'] = pd.to_datetime(df['entrez_year'], errors='coerce')
    df = df[df['entrez_date'] < '2025-01-01']

    included = df[df['prediction'] == 1]
    excluded = df[df['prediction'] == 0]
    # convert title to lowercase
    included['title'] = included['title'].str.lower()
    excluded['title'] = excluded['title'].str.lower()
    
    return [included, excluded]

def find_study_in_db(pmid: int, doi: str, title: str) -> bool:
    study_data = get_study_by_pmid(pmid)
    if study_data:
        return True
    else:
        if pd.isna(doi):
            return False
        doi = doi.replace('https://doi.org/', '')
        study_data = get_study_by_doi(doi)
        if study_data:
            return True
        else:
            study_data = get_study_by_title(title)
            if study_data:
                return True
            else:
                return False         


    pass


def count_batches():
    session = Session()

    try:
        batch_counts = session.query(Paper.batch_retrieval).group_by(Paper.retrieval_id).count()
        breakpoint()
        return batch_counts
    finally:        
        session.close()
    

if __name__ == "__main__":
    articles = "validation/psynamic_validation_included_articles.csv"
    reviews = "validation/psynamic_validation_sr_library.csv"

    # count_batches()

    df_articles = pd.read_csv(articles, delimiter=';')
    df_articles.replace('nA', None, inplace=True)

    df_reviews = pd.read_csv(reviews, delimiter=';')
    nr_studie_in_db = 0
    included_man, excluded_man, excluded_after_stopping_man, df = read_in_asreview()
    included_auto, excluded_auto = read_in_all_retrieved_studies()

    # add new column in_psynamic
    df_articles['in_psynamic'] = False
    df_articles['in_excluded'] = False
    df_articles['in_excluded_after_stopping'] = False
    df_articles['excluded_by_bert'] = False

    for index, row in df_articles.iterrows():
        title = row['Title'].lower()
        # if 'MDMA-facilitated cognitive-behavioural conjoint therapy for posttraumatic stress disorder: an uncontrolled trial' in row['Title']:
        #     breakpoint()
        #     # get row record_id =5744 in df
        #     if df[df['record_id'] == 5744].shape[0] > 0:
        #         print('found')
        if find_study_in_db(row['PMID'], row['doi'], row['Title']):
            df_articles.at[index, 'in_psynamic'] = True

        elif title in excluded_man['title'].values:
            df_articles.at[index, 'in_excluded'] = True
        
        elif title in excluded_after_stopping_man['title'].values:
            df_articles.at[index, 'in_excluded_after_stopping'] = True

        if title in excluded_auto['title'].values:
            df_articles.at[index, 'excluded_by_bert'] = True

    # print number of excluded by bert
    print('Number of studies excluded by BERT: {}'.format(df_articles['excluded_by_bert'].sum()))
    df_articles_no_duplicates = df_articles.drop_duplicates(subset=['PMID', 'doi', 'Title'], keep='first')
    nr_studie_in_db = df_articles_no_duplicates['in_psynamic'].sum()
    print('Percentage of studies found in the database: {:.2f}%'.format((nr_studie_in_db / len(df_articles_no_duplicates)) * 100))

    print('Number of studies in excluded set: {}'.format(df_articles_no_duplicates['in_excluded'].sum()))
    # print titles of df_articles_no_duplicates where in_excluded is True
    print('Titles of studies in excluded set:')
    print(df_articles_no_duplicates[df_articles_no_duplicates['in_excluded'] == True]['Title'].values)
    print('Number of studies in excluded after stopping set: {}'.format(df_articles_no_duplicates['in_excluded_after_stopping'].sum()))
    print('Titles of studies in excluded after stopping set:')
    print(df_articles_no_duplicates[df_articles_no_duplicates['in_excluded_after_stopping'] == True]['Title'].values)

    percentages = []
    sr_nos = df_articles['SR_No'].unique()
    for sr_no in sr_nos:
        total_studies = df_reviews[df_reviews['SR'] == sr_no]['Total Nr'].iloc[0]
        included = df_articles[(df_articles['SR_No'] == sr_no) & (df_articles['in_psynamic'])].shape[0]
        percentage = included / total_studies * 100 if total_studies > 0 else 0
        percentages.append(percentage)

    print('Average percentage of studies found in the database across all systematic reviews: {:.2f}%'.format(sum(percentages) / len(percentages)))
    # median percentage of studies found in the database across all systematic reviews
    print(percentages)
    print('Median percentage of studies found in the database across all systematic reviews: {:.2f}%'.format(pd.Series(percentages).median()))

    # plot a bar chart of the percentage of studies found in the database across all systematic reviews
    import matplotlib.pyplot as plt
    plt.bar(sr_nos, percentages)
    plt.xlabel('Systematic Review Number')
    plt.ylabel('Percentage of Studies Found in Database')
    plt.title('Percentage of Studies Found in Database Across Systematic Reviews')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('validation/percentage_studies_found_in_database.png')


    # NR of studies not in psynamic
    nr_studies_not_in_psynamic = df_articles_no_duplicates[~df_articles_no_duplicates['in_psynamic']].shape[0]
    print('Number of studies not found in the database: {}'.format(nr_studies_not_in_psynamic))

    # Remove excluded and excluded after stopping from the articles dataframe
    df_articles_final = df_articles_no_duplicates[~df_articles_no_duplicates['in_excluded'] & ~df_articles_no_duplicates['in_excluded_after_stopping']]
    nr_studie_in_db_final = df_articles_final['in_psynamic'].sum()
    print('Percentage of studies found in the database after removing excluded studies: {:.2f}%'.format((nr_studie_in_db_final / len(df_articles_final)) * 100))

    # output all studies where in_psynamic is False to a csv file
    df_articles_final[df_articles_final['in_psynamic'] == False].to_csv('validation/psynamic_validation_not_in_db.csv', index=False, sep=';')

