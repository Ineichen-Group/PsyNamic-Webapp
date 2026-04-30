import marimo

__generated_with = "0.23.3"
app = marimo.App()


@app.cell
def _():
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))

    import os
    import pandas as pd
    from data.queries import engine, Session
    from data.models import Paper
    from typing import Optional
    from sqlalchemy import func


    def get_study_by(attr: str, value: int | str, after_2025: bool=False) -> dict:
        session = Session()
        try:
            if after_2025:
                query = session.query(Paper).filter(
                    Paper.entrez_year > 2025
                )
            else:
                query = session.query(Paper).filter(
                    (Paper.entrez_year.is_(None)) | (Paper.entrez_year <= 2025)
                )
            query = query.filter(getattr(Paper, attr) == value)

            # if there is several papers raise an error
            papers = query.all()
            if len(papers) > 1:
                raise ValueError(f"Multiple papers found for {attr} = {value}")

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


    def get_study_by_title(title: str, include_substring: bool = False, after_2025: bool=False) -> list[dict]:
        title = title.lower()
        session = Session()
        try:
            if include_substring:
                query = session.query(Paper).filter(
                    func.lower(Paper.title).contains(func.lower(title))
                )
            else:
                query = session.query(Paper).filter(
                    func.lower(Paper.title) == func.lower(title)
                )
            if after_2025:
                query = query.filter(
                    Paper.entrez_year > 2025
                )
            else:
                query = query.filter(
                    (Paper.entrez_year.is_(None)) | (Paper.entrez_year <= 2025)
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

        included = df.loc[df['prediction'] == 1].copy()
        excluded = df.loc[df['prediction'] == 0].copy()
        # convert title to lowercase
        included.loc[:, 'title'] = included['title'].str.lower()
        excluded.loc[:, 'title'] = excluded['title'].str.lower()
        return [included, excluded]


    def find_study_in_db(pmid: int, doi: str, title: str, after_2025: bool = False, rel_pmid1: Optional[int] = None, rel_pmid2: Optional[int] = None) -> bool:
        study_data = None
        if pmid:
            study_data = get_study_by('pubmed_id', pmid, after_2025=after_2025)
        if study_data:
            return True
        else:
            if rel_pmid1:
                study_data = get_study_by('pubmed_id', rel_pmid1, after_2025=after_2025)
            if study_data:
                return True
            if rel_pmid2:
                study_data = get_study_by('pubmed_id', rel_pmid2, after_2025=after_2025)
            if study_data:
                return True
            if doi:
                doi = str(doi).replace('https://doi.org/', '')
                study_data = get_study_by('doi', doi, after_2025=after_2025)
            if study_data:
                return True
            else:
                study_data = get_study_by_title(title, after_2025=after_2025)
                if study_data:
                    return True
                else:
                    return False        




    return (
        find_study_in_db,
        pd,
        read_in_all_retrieved_studies,
        read_in_asreview,
    )


@app.cell
def _(pd, read_in_all_retrieved_studies, read_in_asreview):
    articles = "/home/veral/PsyNamic/PsyNamic-Webapp/validation/psynamic_validation_included_articles.csv"
    reviews = "/home/veral/PsyNamic/PsyNamic-Webapp/validation/psynamic_validation_sr_library.csv"

    df_articles = pd.read_csv(articles, delimiter=';')
    df_articles.replace('nA', None, inplace=True)

    df_reviews = pd.read_csv(reviews, delimiter=';')
    df_reviews.replace('nA', None, inplace=True)

    included_man, excluded_man, excluded_after_stopping_man, df = read_in_asreview()
    included_auto, excluded_auto = read_in_all_retrieved_studies()
    return (
        df_articles,
        df_reviews,
        excluded_after_stopping_man,
        excluded_auto,
        excluded_man,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    How many articles are there in the set?
    """)
    return


@app.cell
def _(df_articles):
    len(df_articles)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    How many systematic reviews?
    """)
    return


@app.cell
def _(df_reviews):
    len(df_reviews)
    return


@app.cell
def _(
    df_articles,
    excluded_after_stopping_man,
    excluded_auto,
    excluded_man,
    find_study_in_db,
):
    nr_studie_in_db = 0

    df_articles['in_psynamic'] = False
    df_articles['in_excluded'] = False
    df_articles['in_excluded_after_stopping'] = False
    df_articles['excluded_by_bert'] = False
    df_articles['in_later_retrieved'] = False

    for index, row in df_articles.iterrows():
        title = row['Title'].lower()
        if find_study_in_db(row['PMID'], row['doi'], row['Title'], after_2025=False, rel_pmid1=row['Related Publication PMID 1'], rel_pmid2=row['Related Publication PMID 2']):
            df_articles.at[index, 'in_psynamic'] = True

        elif title in excluded_man['title'].values:
            df_articles.at[index, 'in_excluded'] = True

        elif title in excluded_after_stopping_man['title'].values:
            df_articles.at[index, 'in_excluded_after_stopping'] = True

        if title in excluded_auto['title'].values:
            df_articles.at[index, 'excluded_by_bert'] = True

        if find_study_in_db(row['PMID'], row['doi'], row['Title'], after_2025=True, rel_pmid1=row['Related Publication PMID 1'], rel_pmid2=row['Related Publication PMID 2']):
            df_articles.at[index, 'in_later_retrieved'] = True
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Number of articles excluded by BERT?
    """)
    return


@app.cell
def _(df_articles):
    df_articles['excluded_by_bert'].sum()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Percentage of articles from RS that are included in PsyNamic database (up until 2025)?
    """)
    return


@app.cell
def _(df_articles):
    df_articles_no_duplicates = df_articles.drop_duplicates(subset=['PMID', 'doi', 'Title'], keep='first')
    nr_articles_no_duplicate = df_articles_no_duplicates['in_psynamic'].sum()
    (nr_articles_no_duplicate / len(df_articles_no_duplicates)) * 100
    return (df_articles_no_duplicates,)


@app.cell
def _(df_articles_no_duplicates):
    # get number of articles where either in_psyanamic, in_excluded or in_excluded_after_stopping is True
    df_articles_no_duplicates['in_psynamic_or_excluded'] = df_articles_no_duplicates['in_psynamic'] | df_articles_no_duplicates['in_excluded'] | df_articles_no_duplicates['in_excluded_after_stopping']
    nr_articles_no_duplicate_or_excluded = df_articles_no_duplicates['in_psynamic_or_excluded'].sum()
    (nr_articles_no_duplicate_or_excluded / len(df_articles_no_duplicates)) * 100
    return (nr_articles_no_duplicate_or_excluded,)


@app.cell
def _(nr_articles_no_duplicate_or_excluded):
    nr_articles_no_duplicate_or_excluded
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Number of studies from RS that were manually excluded?
    """)
    return


@app.cell
def _(df_articles_no_duplicates):
    df_articles_no_duplicates['in_excluded'].sum()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Number of studies from RS that were in excluded after stopping criteria?
    """)
    return


@app.cell
def _(df_articles_no_duplicates):
    df_articles_no_duplicates['in_excluded_after_stopping'].sum()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Number of studies from RS that were included after 2025?
    """)
    return


@app.cell
def _(df_articles_no_duplicates):
    df_articles_no_duplicates['in_later_retrieved'].sum()
    return


@app.cell
def _(df_articles, df_reviews):
    percentages = []
    sr_nos = df_articles['SR_No'].unique()
    for sr_no in sr_nos:
        total_studies = df_reviews[df_reviews['SR'] == sr_no]['Total Nr'].iloc[0]
        included = df_articles[(df_articles['SR_No'] == sr_no) & (df_articles['in_psynamic'])].shape[0] 
        percentage = included / total_studies * 100 if total_studies > 0 else 0
        percentages.append(percentage)

    return (percentages,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What is the average percentage of articles from RS that are included in PsyNamic database (up until 2025)?
    """)
    return


@app.cell
def _(percentages):
    sum(percentages) / len(percentages)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What is the median percentage of articles from RS that are included in PsyNamic database (up until 2025)?
    """)
    return


@app.cell
def _(pd, percentages):
    pd.Series(percentages).median()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Number of missing articles that don't have a PMID?
    """)
    return


@app.cell
def _(df_articles_no_duplicates):
    df_filtered = df_articles_no_duplicates[
        df_articles_no_duplicates['in_psynamic_or_excluded'] == False
    ]

    # count where the PMID is None
    nr_no_pmid = df_filtered['PMID'].isna().sum()
    # percentage of articles without PMID
    (nr_no_pmid / len(df_filtered)) * 100
    nr_no_pmid
    return


@app.cell
def _(pd):
    validation_results_annotated = "/home/veral/PsyNamic/PsyNamic-Webapp/validation/validation_result_annotated.csv"
    df_validation_results = pd.read_csv(validation_results_annotated, delimiter=';')

    # remove all rows where Questionable == true
    df_validation_results_filtered = df_validation_results[df_validation_results['Questionable'] != True]

    # remove all not in psynamic, excluded or excluded after stopping
    nr_not_included = df_validation_results_filtered[
        (df_validation_results_filtered['in_psynamic'] == False) &
        (df_validation_results_filtered['in_excluded'] == False) &
        (df_validation_results_filtered['in_excluded_after_stopping'] == False)
    ].shape[0]
    ((len(df_validation_results_filtered) -nr_not_included )/ len(df_validation_results_filtered)) * 100
    return df_validation_results_filtered, nr_not_included


@app.cell
def _(nr_not_included):
    nr_not_included
    return


@app.cell
def _(df_validation_results_filtered):
    # check how many of the not included the pmid is none
    nr_not_included_with_pmid = df_validation_results_filtered[
        (df_validation_results_filtered['in_psynamic'] == False) &
        (df_validation_results_filtered['in_excluded'] == False) &
        (df_validation_results_filtered['in_excluded_after_stopping'] == False) &
        (df_validation_results_filtered['PMID'].isna() == True)
    ].shape[0]
    nr_not_included_with_pmid
    return


if __name__ == "__main__":
    app.run()
