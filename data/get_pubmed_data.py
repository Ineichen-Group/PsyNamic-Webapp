import requests
from datetime import timedelta, datetime
from lxml import etree as ET
from lxml import html
from html import unescape
import pandas as pd
import time
import os
import logging
import argparse
import pytz
from data.helper import cleanup_old_logs, format_timedelta_hms

PUBMED_API_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
PUBMED_ABSTRACTS_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
SEARCH_STRING = '((Randomized Controlled Trial[Publication Type] OR Controlled Clinical Trial[Publication Type] OR Pragmatic Clinical Trial[Publication Type] OR Clinical Study[Publication Type] OR Adaptive Clinical Trial[Publication Type] OR Equivalence Trial[Publication Type] OR Clinical Trial[Publication Type] OR Clinical Trial, Phase I[Publication Type] OR Clinical Trial, Phase II[Publication Type] OR Clinical Trial, Phase III[Publication Type] OR Clinical Trial, Phase IV[Publication Type] OR Clinical Trial Protocol[Publication Type] OR multicenter study[Publication Type] OR "Clinical Studies as Topic"[Mesh] OR "Clinical Trials as Topic"[Mesh] OR "Clinical Trial Protocols as Topic"[Mesh] OR "Multicenter Studies as Topic"[Mesh] OR "Random Allocation"[Mesh] OR "Double-Blind Method"[Mesh] OR "Single-Blind Method"[Mesh] OR "Placebos"[Mesh:NoExp] OR "Control Groups"[Mesh] OR "Cross-Over Studies"[Mesh] OR random*[Title/Abstract] OR sham[Title/Abstract] OR placebo*[Title/Abstract] OR ((singl*[Title/Abstract] OR doubl*[Title/Abstract]) AND (blind*[Title/Abstract] OR dumm*[Title/Abstract] OR mask*[Title/Abstract])) OR ((tripl*[Title/Abstract] OR trebl*[Title/Abstract]) AND (blind*[Title/Abstract] OR dumm*[Title/Abstract] OR mask*[Title/Abstract])) OR "control study"[tiab:~3] OR "control studies"[tiab:~3] OR "control group"[tiab:~3] OR "control groups"[tiab:~3] OR "healthy volunteers"[tiab:~3] OR "control trial"[tiab:~3] OR "control trials"[tiab:~3] OR "controlled study"[tiab:~3] OR "controlled trial"[tiab:~3] OR "controlled studies"[tiab:~3] OR "controlled trials"[tiab:~3] OR "clinical study"[tiab:~3] OR "clinical studies"[tiab:~3] OR "clinical trial"[tiab:~3] OR "clinical trials"[tiab:~3] OR Nonrandom*[Title/Abstract] OR non random*[Title/Abstract] OR non-random*[Title/Abstract] OR quasi-random*[Title/Abstract] OR quasirandom*[Title/Abstract] OR "phase study"[tiab:~3] OR "phase studies"[tiab:~3] OR "phase trial"[tiab:~3] OR "phase trials"[tiab:~3] OR "crossover study"[tiab:~3] OR "crossover studies"[tiab:~3] OR "crossover trial"[tiab:~3] OR "crossover trials"[tiab:~3] OR "cross-over study"[tiab:~3] OR "cross-over studies"[tiab:~3] OR "cross-over trial"[tiab:~3] OR "cross-over trials"[tiab:~3] OR ((multicent*[tiab] OR multi-cent*[tiab] OR open label[tiab] OR open-label[tiab] OR equivalence[tiab] OR superiority[tiab] OR non-inferiority[tiab] OR noninferiority[tiab] OR quasiexperimental[tiab] OR quasi-experimental[tiab]) AND (study[tiab] OR studies[tiab] OR trial*[tiab])) OR allocated[tiab] OR pragmatic study[tiab] OR pragmatic studies[tiab] OR pragmatic trial*[tiab] OR practical trial*[tiab]) AND ("Hallucinogens"[Majr] OR "Lysergic Acid Diethylamide"[Majr] OR "Psilocybin"[Majr] OR "psilocin" [Supplementary Concept] OR "Mescaline"[Majr] OR "N,N-Dimethyltryptamine"[Majr] OR "Banisteriopsis"[Majr] OR "N-Methyl-3,4-methylenedioxyamphetamine"[Majr] OR "3,4-Methylenedioxyamphetamine"[Majr] OR ("Ketamine"[Majr] AND ("Behavioral Symptoms"[MeSH] OR "Mental Disorders"[Mesh])) OR "Ibogaine"[Majr] OR "salvinorin a"[Supplementary Concept] OR ((hallucinogen*[tiab] OR psychedel*[tiab] OR psychomimet*[tiab] OR entheo*[tiab] OR entactogen*[tiab]) AND (agent*[tiab] OR drug*[tiab] OR compound*[tiab] OR substance*[tiab] OR therap*[tiab] OR psychotherap*[tiab] OR medic*[tiab])) OR (LSD[tiab] AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR LSD-25[tiab] OR "lysergic acid diethylamide"[tiab] OR delysid*[tiab] OR lysergide[tiab] OR lysergamide[tiab] OR Psilocybin*[tiab] OR Psilocibin*[tiab] OR comp360[tiab] OR Psilocin*[tiab] OR 4-HO-DMT[tiab] OR psilocyn*[tiab] OR mescalin*[tiab] OR 3,4,5-trimethoxyphenethylamine[tiab] OR TMPEA[tiab] OR Peyot*[tiab] OR (DMT[tiab] AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR N,N-Dimethyltryptamine[tiab] OR dimethyltryptamine*[tiab] OR "dimethyl tryptamine"[tiab] OR N,N-DMT[tiab] OR ayahuasca[tiab] OR banisteriopsis[tiab] OR 5-methoxy-N,N-dimethyltryptamine[tiab] OR methylbufotenin[tiab] OR 5-MeO-DMT[tiab] OR "5 methoxy dmt"[tiab] OR "5 methoxy n, n dimethyl tryptamine"[tiab] OR "5 methoxydimethyltryptamine"[tiab] OR "n, n dimethyl 5 methoxytryptamine"[tiab] OR Methylenedioxymethamphetamine[tiab] OR "3,4-Methylenedioxy methamphetamine"[tiab] OR "n methyl 3, 4 methylenedioxyamphetamine"[tiab] OR midomafetamine[tiab] OR MDMA[tiab] OR (ecstasy[tiab] AND drug*[tiab]) OR ((Ketamin*[tiab] OR esketamine[tiab]) AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR Ibogaine[tiab] OR iboga[tiab] OR salvinorin[tiab] OR "salvia divinorum"[tiab])) NOT (("Animals"[Mesh] OR "Animal Experimentation"[Mesh] OR "Models, Animal"[Mesh] OR "Vertebrates"[Mesh]) NOT ("Humans"[Mesh] OR "Human Experimentation"[Mesh]))'

zurich = pytz.timezone('Europe/Zurich')


def get_pubmed_data(query_string: str, retstart: int = 0, retmax: int = 2000):
    """
    Get pubmed ids for a given query string (which includes the query and a time filter)
    """

    params = {
        'db': 'pubmed',
        'retmode': 'xml',
        'retstart': retstart,
        'retmax': retmax,
    }
    data = {
        'term': query_string,
    }

    try:
        response = requests.post(
            PUBMED_API_URL, params=params, data=data, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while querying PubMed: {e}")
        return None


def get_pubmed_abstracts(pmids: list) -> str:
    """
    Get abstracts and other metadata for a list of pubmed ids
    """
    pmids_str = ','.join(map(str, pmids))
    data = {
        'db': 'pubmed',
        'rettype': 'abstract',
        'id': pmids_str,
        'retmode': 'xml',
    }

    try:
        response = requests.post(PUBMED_ABSTRACTS_URL, data=data, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while fetching abstracts: {e}")
        return None


def parse_pubmed_data(xml_data: str) -> list[dict]:
    """
    Parse the XML data and extract the relevant information
    """
    articles = extract_pubmed_articles(xml_data)
    articles_info = []
    for article in articles:
        article_info = {}

        article_info['keywords'] = [
            a.text for a in article.xpath('.//Keyword') if a.text]

        article_info['pubmed_id'] = extract_pubmedid(article)
        article_info['pubmed_url'] = f'https://pubmed.ncbi.nlm.nih.gov/{article_info["pubmed_id"]}/' if article_info['pubmed_id'] else None
        article_info['doi'] = extract_doi(article)

        pub_date = article.find(
            './/History/PubMedPubDate[@PubStatus="pubmed"]/Year')
        article_info['year'] = pub_date.text if pub_date is not None else None

        article_info['abstract'] = extract_abstract_text(article)
        article_info['title'] = extract_title(article)

        # Skip articles without abstracts — do not save them
        if not article_info['abstract'] or not str(article_info['abstract']).strip():
            logging.info(f"Skipping PubMed article without abstract: {article_info.get('pubmed_id')}")
            continue

        authors = []
        for author in article.findall('.//Article/AuthorList/Author'):
            initials = author.find('.//Initials')
            last_name = author.find('.//LastName')
            collective_name = author.find('.//CollectiveName')

            if initials is not None and last_name is not None:
                authors.append(f"{initials.text}. {last_name.text}")
            elif collective_name is not None:
                authors.append(collective_name.text)

        article_info['authors'] = ', '.join(authors) if authors else None
        articles_info.append(article_info)

    return articles_info


def extract_title(article: ET.Element) -> str:
    title_element = article.find('.//ArticleTitle')
    title = "".join(title_element.itertext()).strip()
    if title:
        title = unescape(html.fromstring(title).text_content())

    return title


def extract_pubmedid(article: ET.Element) -> str:
    """
    Extract PubMed ID from a PubmedArticle element
    """
    # <ArticleIdList>
    #    <ArticleId IdType="pubmed">41498818</ArticleId>
    pmid_element = article.find(
        './/PubmedData/ArticleIdList/ArticleId[@IdType="pubmed"]')
    return pmid_element.text if pmid_element is not None else None


def extract_doi(article: ET.Element) -> str:
    #  <ArticleIdList>
    #             <ArticleId IdType="pubmed">41498818</ArticleId>
    #             <ArticleId IdType="doi">10.1021/acschemneuro.5c00892</ArticleId>
    doi_element = article.find(
        './/PubmedData/ArticleIdList/ArticleId[@IdType="doi"]')
    return doi_element.text if doi_element is not None else None


def extract_pubmed_articles(xml_data: str) -> list[ET.Element]:
    """
    Extract PubmedArticle elements from the XML data
    """
    root = ET.fromstring(xml_data.encode('utf-8'))
    articles = root.xpath('//PubmedArticle')
    return articles


def extract_abstract_text(article: ET.Element) -> str:
    abstract_texts = article.findall('.//AbstractText')

    parts = []

    for a in abstract_texts:
        label = a.get("Label")
        text = "".join(a.itertext())
        if label:
            parts.append(f"{label}: {text}")
        else:
            parts.append(text)

    abstract = " ".join(parts).strip()

    if abstract:
        abstract = unescape(html.fromstring(abstract).text_content())

    return abstract


def main():
    # Get dir of this file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    date_file = os.path.join(dir_path, 'last_data_fetch.txt')

    parser = argparse.ArgumentParser(description='Fetch PubMed data')
    parser.add_argument(
        '-l', '--log-file',
        type=str,
        default=None,
        help='Path to logfile. If not provided, logs go to terminal.'
    )
    args = parser.parse_args()

    if args.log_file:
        log_dir = os.path.dirname(args.log_file)
        os.makedirs(log_dir, exist_ok=True)
        cleanup_old_logs(log_dir)
        logging.basicConfig(
            filename=args.log_file,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            force=True
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            force=True
        )

    with open(date_file, "r", encoding="utf-8") as f:
        last_data_fetch = f.readlines()[-1].rstrip("\n")

    search_string_with_date = f'{SEARCH_STRING} AND (("{last_data_fetch}"[Date - Publication] : "3000"[Date - Publication]))'

    start = 0
    total_results = 0
    all_abstracts = []
    count = 0

    start_time = datetime.now(zurich)

    # Paginate through results
    while True:
        xml_data = get_pubmed_data(search_string_with_date, retstart=start)
        if xml_data:
            root = ET.fromstring(xml_data.encode('utf-8'))
            pmids = [
                id_element.text for id_element in root.xpath('//IdList/Id')]
            count = int(root.find('Count').text)

            if pmids:
                abstract_data = get_pubmed_abstracts(pmids)
                if abstract_data:
                    parsed_abstracts = parse_pubmed_data(abstract_data)
                    all_abstracts.extend(parsed_abstracts)
                    total_results += len(parsed_abstracts)

                    if total_results >= count:
                        break

                    start += 2000
                    if start >= count:
                        break

                    time.sleep(1)
                else:
                    break
            else:
                break
        else:
            break

    end_time = datetime.now(zurich)
    # duration in format hh:mm:ss
    duration = format_timedelta_hms(end_time - start_time)
    df = pd.DataFrame(all_abstracts)
    df['text'] = df['title'] + '^\n' + df['abstract']
    today = datetime.now(zurich).strftime("%Y/%m/%d")

    # 2026/01/12 --> 20260112
    from_date = last_data_fetch.replace("/", "")
    to_date = today.replace("/", "")

    outfile = os.path.join(dir_path, 'pubmed_fetch_results',
                           f'pubmed_results_{from_date}_{to_date}_{duration}.csv')
    df.to_csv(outfile, index=False, encoding='utf-8')
    logging.info(f"Wrote {len(df)} abstracts to {outfile}")

    with open(date_file, "a", encoding="utf-8") as f:
        f.write(today + "\n")
    logging.info(f"Updated last_data_fetch to {today}")


if __name__ == "__main__":
    main()
