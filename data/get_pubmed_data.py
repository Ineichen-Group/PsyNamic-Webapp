from random import random
import re
import requests
from datetime import timedelta, datetime, date
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
from typing import Optional, List, Sequence

PUBMED_API_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
PUBMED_ABSTRACTS_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
SEARCH_STRING = '((Randomized Controlled Trial[Publication Type] OR Controlled Clinical Trial[Publication Type] OR Pragmatic Clinical Trial[Publication Type] OR Clinical Study[Publication Type] OR Adaptive Clinical Trial[Publication Type] OR Equivalence Trial[Publication Type] OR Clinical Trial[Publication Type] OR Clinical Trial, Phase I[Publication Type] OR Clinical Trial, Phase II[Publication Type] OR Clinical Trial, Phase III[Publication Type] OR Clinical Trial, Phase IV[Publication Type] OR Clinical Trial Protocol[Publication Type] OR multicenter study[Publication Type] OR "Clinical Studies as Topic"[Mesh] OR "Clinical Trials as Topic"[Mesh] OR "Clinical Trial Protocols as Topic"[Mesh] OR "Multicenter Studies as Topic"[Mesh] OR "Random Allocation"[Mesh] OR "Double-Blind Method"[Mesh] OR "Single-Blind Method"[Mesh] OR "Placebos"[Mesh:NoExp] OR "Control Groups"[Mesh] OR "Cross-Over Studies"[Mesh] OR random*[Title/Abstract] OR sham[Title/Abstract] OR placebo*[Title/Abstract] OR ((singl*[Title/Abstract] OR doubl*[Title/Abstract]) AND (blind*[Title/Abstract] OR dumm*[Title/Abstract] OR mask*[Title/Abstract])) OR ((tripl*[Title/Abstract] OR trebl*[Title/Abstract]) AND (blind*[Title/Abstract] OR dumm*[Title/Abstract] OR mask*[Title/Abstract])) OR "control study"[tiab:~3] OR "control studies"[tiab:~3] OR "control group"[tiab:~3] OR "control groups"[tiab:~3] OR "healthy volunteers"[tiab:~3] OR "control trial"[tiab:~3] OR "control trials"[tiab:~3] OR "controlled study"[tiab:~3] OR "controlled trial"[tiab:~3] OR "controlled studies"[tiab:~3] OR "controlled trials"[tiab:~3] OR "clinical study"[tiab:~3] OR "clinical studies"[tiab:~3] OR "clinical trial"[tiab:~3] OR "clinical trials"[tiab:~3] OR Nonrandom*[Title/Abstract] OR non random*[Title/Abstract] OR non-random*[Title/Abstract] OR quasi-random*[Title/Abstract] OR quasirandom*[Title/Abstract] OR "phase study"[tiab:~3] OR "phase studies"[tiab:~3] OR "phase trial"[tiab:~3] OR "phase trials"[tiab:~3] OR "crossover study"[tiab:~3] OR "crossover studies"[tiab:~3] OR "crossover trial"[tiab:~3] OR "crossover trials"[tiab:~3] OR "cross-over study"[tiab:~3] OR "cross-over studies"[tiab:~3] OR "cross-over trial"[tiab:~3] OR "cross-over trials"[tiab:~3] OR ((multicent*[tiab] OR multi-cent*[tiab] OR open label[tiab] OR open-label[tiab] OR equivalence[tiab] OR superiority[tiab] OR non-inferiority[tiab] OR noninferiority[tiab] OR quasiexperimental[tiab] OR quasi-experimental[tiab]) AND (study[tiab] OR studies[tiab] OR trial*[tiab])) OR allocated[tiab] OR pragmatic study[tiab] OR pragmatic studies[tiab] OR pragmatic trial*[tiab] OR practical trial*[tiab]) AND ("Hallucinogens"[Majr] OR "Lysergic Acid Diethylamide"[Majr] OR "Psilocybin"[Majr] OR "psilocin" [Supplementary Concept] OR "Mescaline"[Majr] OR "N,N-Dimethyltryptamine"[Majr] OR "Banisteriopsis"[Majr] OR "N-Methyl-3,4-methylenedioxyamphetamine"[Majr] OR "3,4-Methylenedioxyamphetamine"[Majr] OR ("Ketamine"[Majr] AND ("Behavioral Symptoms"[MeSH] OR "Mental Disorders"[Mesh])) OR "Ibogaine"[Majr] OR "salvinorin a"[Supplementary Concept] OR ((hallucinogen*[tiab] OR psychedel*[tiab] OR psychomimet*[tiab] OR entheo*[tiab] OR entactogen*[tiab]) AND (agent*[tiab] OR drug*[tiab] OR compound*[tiab] OR substance*[tiab] OR therap*[tiab] OR psychotherap*[tiab] OR medic*[tiab])) OR (LSD[tiab] AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR LSD-25[tiab] OR "lysergic acid diethylamide"[tiab] OR delysid*[tiab] OR lysergide[tiab] OR lysergamide[tiab] OR Psilocybin*[tiab] OR Psilocibin*[tiab] OR comp360[tiab] OR Psilocin*[tiab] OR 4-HO-DMT[tiab] OR psilocyn*[tiab] OR mescalin*[tiab] OR 3,4,5-trimethoxyphenethylamine[tiab] OR TMPEA[tiab] OR Peyot*[tiab] OR (DMT[tiab] AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR N,N-Dimethyltryptamine[tiab] OR dimethyltryptamine*[tiab] OR "dimethyl tryptamine"[tiab] OR N,N-DMT[tiab] OR ayahuasca[tiab] OR banisteriopsis[tiab] OR 5-methoxy-N,N-dimethyltryptamine[tiab] OR methylbufotenin[tiab] OR 5-MeO-DMT[tiab] OR "5 methoxy dmt"[tiab] OR "5 methoxy n, n dimethyl tryptamine"[tiab] OR "5 methoxydimethyltryptamine"[tiab] OR "n, n dimethyl 5 methoxytryptamine"[tiab] OR Methylenedioxymethamphetamine[tiab] OR "3,4-Methylenedioxy methamphetamine"[tiab] OR "n methyl 3, 4 methylenedioxyamphetamine"[tiab] OR midomafetamine[tiab] OR MDMA[tiab] OR (ecstasy[tiab] AND drug*[tiab]) OR ((Ketamin*[tiab] OR esketamine[tiab]) AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR Ibogaine[tiab] OR iboga[tiab] OR salvinorin[tiab] OR "salvia divinorum"[tiab])) NOT (("Animals"[Mesh] OR "Animal Experimentation"[Mesh] OR "Models, Animal"[Mesh] OR "Vertebrates"[Mesh]) NOT ("Humans"[Mesh] OR "Human Experimentation"[Mesh]))'

SEARCH_STRING_WITHOUT_STUDY_TYPE = '("Hallucinogens"[Majr] OR "Lysergic Acid Diethylamide"[Majr] OR "Psilocybin"[Majr] OR "psilocin" [Supplementary Concept] OR "Mescaline"[Majr] OR "N,N-Dimethyltryptamine"[Majr] OR "Banisteriopsis"[Majr] OR "N-Methyl-3,4-methylenedioxyamphetamine"[Majr] OR "3,4-Methylenedioxyamphetamine"[Majr] OR ("Ketamine"[Majr] AND ("Behavioral Symptoms"[MeSH] OR "Mental Disorders"[Mesh])) OR "Ibogaine"[Majr] OR "salvinorin a"[Supplementary Concept] OR ((hallucinogen*[tiab] OR psychedel*[tiab] OR psychomimet*[tiab] OR entheo*[tiab] OR entactogen*[tiab]) AND (agent*[tiab] OR drug*[tiab] OR compound*[tiab] OR substance*[tiab] OR therap*[tiab] OR psychotherap*[tiab] OR medic*[tiab])) OR (LSD[tiab] AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR LSD-25[tiab] OR "lysergic acid diethylamide"[tiab] OR delysid*[tiab] OR lysergide[tiab] OR lysergamide[tiab] OR Psilocybin*[tiab] OR Psilocibin*[tiab] OR comp360[tiab] OR Psilocin*[tiab] OR 4-HO-DMT[tiab] OR psilocyn*[tiab] OR mescalin*[tiab] OR 3,4,5-trimethoxyphenethylamine[tiab] OR TMPEA[tiab] OR Peyot*[tiab] OR (DMT[tiab] AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR N,N-Dimethyltryptamine[tiab] OR dimethyltryptamine*[tiab] OR "dimethyl tryptamine"[tiab] OR N,N-DMT[tiab] OR ayahuasca[tiab] OR banisteriopsis[tiab] OR 5-methoxy-N,N-dimethyltryptamine[tiab] OR methylbufotenin[tiab] OR 5-MeO-DMT[tiab] OR "5 methoxy dmt"[tiab] OR "5 methoxy n, n dimethyl tryptamine"[tiab] OR "5 methoxydimethyltryptamine"[tiab] OR "n, n dimethyl 5 methoxytryptamine"[tiab] OR Methylenedioxymethamphetamine[tiab] OR "3,4-Methylenedioxy methamphetamine"[tiab] OR "n methyl 3, 4 methylenedioxyamphetamine"[tiab] OR midomafetamine[tiab] OR MDMA[tiab] OR (ecstasy[tiab] AND drug*[tiab]) OR ((Ketamin*[tiab] OR esketamine[tiab]) AND (psychedel*[tiab] OR hallucinogen*[tiab] OR entheo*[tiab] OR trip*[tiab] OR psychiat*[tiab])) OR Ibogaine[tiab] OR iboga[tiab] OR salvinorin[tiab] OR "salvia divinorum"[tiab]) NOT (("Animals"[Mesh] OR "Animal Experimentation"[Mesh] OR "Models, Animal"[Mesh] OR "Vertebrates"[Mesh]) NOT ("Humans"[Mesh] OR "Human Experimentation"[Mesh])) NOT (preprint[Filter])'

zurich = pytz.timezone('Europe/Zurich')
session = requests.Session()
session.headers.update({
    "User-Agent": "PubMedPipeline/1.0 (research script)"
})


def split_into_5y_window(start_date: date, end_date: date):
    """
    Split date range into 5-year chunks safely. Works across leap years and long historical ranges.
    This is necessary because the fetch results are limited to 9,999 records
    """
    chunks = []
    current = start_date

    while current < end_date:
        try:
            candidate_end = current.replace(year=current.year + 5)
        except ValueError:
            candidate_end = current.replace(year=current.year + 5, day=28)

        chunk_end = min(candidate_end, end_date)

        chunks.append((current, chunk_end))

        if chunk_end >= end_date:
            break

        current = chunk_end + timedelta(days=1)
        if chunk_end >= end_date:
            break

        current = chunk_end + timedelta(days=1)

    return chunks



def fmt(d: date):
    """Format a `date` as YYYY/MM/DD for PubMed queries."""

    return d.strftime("%Y/%m/%d")


def request_with_retry(url, params=None, data=None, method="post", max_retries=5) -> Optional[str]:
    """Perform HTTP request with exponential backoff and simple HTML validation.

    Returns response text on success or `None` after exhausting retries.
    """

    for attempt in range(max_retries):
        try:
            if method == "post":
                response = session.post(
                    url, params=params, data=data, timeout=20)
            else:
                response = session.get(url, params=params, timeout=20)

            response.raise_for_status()
            text = response.text

            if not text or "<html" in text.lower():
                raise ValueError("Invalid HTML response from PubMed")

            return text

        except Exception as e:
            wait = (2 ** attempt) + random()
            logging.warning(f"Request failed ({attempt+1}/{max_retries}): {e}")
            logging.warning(f"Retrying in {wait:.2f}s")
            time.sleep(wait)

    logging.error("Max retries reached")
    return None


def get_pubmed_data(query_string: str, retstart: int = 0, retmax: int = 1000) -> Optional[str]:
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

    response_text = request_with_retry(
        PUBMED_API_URL,
        params=params,
        data=data
    )

    if response_text is None:
        logging.error("esearch failed permanently")
        return None

    time.sleep(0.34)
    return response_text


def get_pubmed_abstracts(pmids: Sequence) -> Optional[str]:
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

    response_text = request_with_retry(
        PUBMED_ABSTRACTS_URL,
        data=data
    )

    if not response_text:
        return None

    time.sleep(0.34)
    return response_text


def parse_pubmed_data(xml_data: object):
    """
    Parse PubMed XML into structured article dictionaries.

    Behavior:
    - If passed an `lxml` Element (a single `<PubmedArticle>`), returns a single dict.
    - If passed an XML string, returns a list of dicts (one per article).
    """

    def _parse_article(article: ET._Element) -> dict:
        pmid = extract_pubmedid(article)

        article_info = {
            "pubmed_id": pmid,
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            "doi": extract_doi(article),
            "title": extract_title(article),
            "pub_date": extract_date(article),
        }

        abstract = extract_abstract_text(article)
        abstract = abstract.strip() if abstract else ""

        article_info["abstract"] = abstract

        article_info["keywords"] = [
            a.text for a in article.xpath(".//Keyword") if a.text
        ]

        authors = []
        for author in article.findall(".//Article/AuthorList/Author"):
            initials = author.find(".//Initials")
            last_name = author.find(".//LastName")
            collective_name = author.find(".//CollectiveName")

            if initials is not None and last_name is not None:
                authors.append(f"{initials.text}. {last_name.text}")
            elif collective_name is not None:
                authors.append(collective_name.text)

        article_info["authors"] = ", ".join(authors) if authors else None

        entrez_year = article.find(
            ".//History/PubMedPubDate[@PubStatus='entrez']/Year"
        )
        article_info["entrez_year"] = entrez_year.text if entrez_year is not None else None

        return article_info

    # If caller passed a parsed Element for a single article, return a single dict
    if isinstance(xml_data, ET._Element):
        return _parse_article(xml_data)

    # Otherwise assume xml_data is a string (or bytes) containing XML and parse all articles
    articles = extract_pubmed_articles(xml_data)
    return [_parse_article(article) for article in articles]


def extract_date(article: ET.Element) -> Optional[str]:
    """
    Extracts a single publication date from a PubMed article XML element.
    Raises an error if multiple <PubDate> elements are found.
    Returns a string in 'YYYY-MM-DD' format.
    If Month or Day is missing, sets them to '01'.
    Handles <MedlineDate> formats like: '2026 Mar-Apr 01'
    """

    pub_date_elems = article.findall('.//PubDate')

    if not pub_date_elems:
        return None

    if len(pub_date_elems) > 1:
        logging.warning(
            f"Multiple <PubDate> elements found for article {extract_pubmedid(article)}. Using the first one.")

    pub_date_elem = pub_date_elems[0]

    year = pub_date_elem.findtext('Year')
    month = pub_date_elem.findtext('Month')
    day = pub_date_elem.findtext('Day')

    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    if year is None:
        medline = pub_date_elem.findtext('MedlineDate')

        if medline:
            year_match = re.search(r'\b(\d{4})\b', medline)
            if year_match:
                year = year_match.group(1)

            month_match = re.search(
                r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                medline
            )
            if month_match:
                month = month_match.group(1)  # keep raw for now

            day_match = re.search(r'\b(\d{1,2})\b', medline)
            if day_match:
                day = day_match.group(1)

    if not year:
        logging.warning(
            f"No year found for article {extract_pubmedid(article)}. Cannot extract publication date.")
        return None

    if month:
        month = month_map.get(month, month)
    else:
        month = '01'

    if day:
        day = day.zfill(2)
    else:
        day = '01'

    return f"{year}-{month}-{day}"


def extract_title(article: ET.Element) -> Optional[str]:
    title_element = article.find('.//ArticleTitle')
    if title_element is None:
        return None

    title = "".join(title_element.itertext()).strip()
    if title:
        title = unescape(html.fromstring(title).text_content())

    return title


def extract_pubmedid(article: ET.Element) -> Optional[str]:
    """
    Extract PubMed ID from a PubmedArticle element
    """
    # <ArticleIdList>
    #    <ArticleId IdType="pubmed">41498818</ArticleId>
    pmid_element = article.find(
        './/PubmedData/ArticleIdList/ArticleId[@IdType="pubmed"]')
    return pmid_element.text if pmid_element is not None else None


def extract_doi(article: ET.Element) -> Optional[str]:
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


def extract_abstract_text(article: ET.Element, debug_dir: str = None, pmid: str = None) -> str:
    """Concatenate and clean all `<AbstractText>` parts into a single string.

    If abstract parts have labels, they are prefixed (e.g. 'Background: ...').
    Returns cleaned plain-text or empty string when no abstract is present.
    """

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
    """Command-line entrypoint: fetch PubMed records since last fetch and save CSV."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    date_file = os.path.join(dir_path, "last_data_fetch.txt")

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-file", type=str, default=None)
    args = parser.parse_args()

    if args.log_file:
        log_dir = os.path.dirname(args.log_file)
        if not log_dir:
            log_dir = dir_path
    else:
        log_dir = os.path.join(dir_path, "log")

    os.makedirs(log_dir, exist_ok=True)
    cleanup_old_logs(log_dir, keep_n=50)

    logging.basicConfig(
        filename=args.log_file if args.log_file else None,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True
    )

    with open(date_file, "r", encoding="utf-8") as f:
        last_data_fetch_str = f.readlines()[-1].strip()

    start_date = datetime.strptime(last_data_fetch_str, "%Y/%m/%d").date()
    end_date = datetime.now(zurich).date()

    base_query = SEARCH_STRING_WITHOUT_STUDY_TYPE

    date_chunks = split_into_5y_window(start_date, end_date)

    all_data = []
    seen_pmids = set()
    total_no_abstracts = 0

    # debug_dir = os.path.join(dir_path, "debug_pubmed")
    # os.makedirs(debug_dir, exist_ok=True)

    start_time = datetime.now(zurich)

    for chunk_idx, (chunk_start, chunk_end) in enumerate(date_chunks, start=1):

        logging.info(
            f"Processing chunk {chunk_idx}/{len(date_chunks)}: "
            f"{chunk_start} → {chunk_end}"
        )

        search_string = (
            base_query +
            f' AND (("{fmt(chunk_start)}"[Date - Create] : "{fmt(chunk_end)}"[Date - Create]))'
        )

        start = 0
        retmax = 1000
        bad_response_count = 0
        max_bad_responses = 5

        while True:
            xml_data = get_pubmed_data(
                search_string, retstart=start, retmax=retmax)

            if not xml_data:
                logging.error("No esearch response → retry page")
                bad_response_count += 1
                if bad_response_count > max_bad_responses:
                    break
                time.sleep(5)
                continue

            if "<eSearchResult" not in xml_data:
                logging.error("Invalid esearch response (not XML)")

                # with open(os.path.join(debug_dir, f"bad_esearch_{start}.xml"), "w") as f:
                #     f.write(xml_data)

                bad_response_count += 1
                if bad_response_count > max_bad_responses:
                    break

                time.sleep(5)
                continue

            bad_response_count = 0

            try:
                root = ET.fromstring(xml_data.encode("utf-8"))
            except ET.ParseError:
                logging.error("XML parse error")
                break

            pmids = [x.text for x in root.xpath("//IdList/Id") if x.text]

            count_text = root.findtext("Count")
            if not count_text:
                logging.error("Missing Count → retrying same request")
                time.sleep(5)
                continue

            count = int(count_text)

            safe_start = start + 1
            safe_end = min(start + retmax, count)

            if safe_start <= count:
                logging.info(
                    f"[Chunk {chunk_idx}] PubMed reports {count} results. "
                    f"Fetching records {safe_start}-{safe_end}"
                )
            else:
                logging.info(
                    f"[Chunk {chunk_idx}] PubMed reports {count} results. "
                    f"Pagination complete (start={start}, count={count})"
                )

            if pmids:
                abstract_xml = get_pubmed_abstracts(pmids)

                if not abstract_xml:
                    logging.error("efetch failed")
                    break

                try:
                    articles = extract_pubmed_articles(abstract_xml)
                except Exception as e:
                    logging.error(f"efetch XML parse error: {e}")
                    break

                batch_new = 0
                batch_no_abstracts = 0

                for article in articles:
                    article_info = parse_pubmed_data(article)
                    pmid = article_info["pubmed_id"]

                    if not pmid or pmid in seen_pmids:
                        continue

                    seen_pmids.add(pmid)

                    if not article_info["abstract"]:
                        batch_no_abstracts += 1

                        # debug_file = os.path.join(
                        #     debug_dir,
                        #     f"missing_abstract_{pmid}.xml"
                        # )
                        # with open(debug_file, "wb") as f:
                        #     f.write(ET.tostring(article, pretty_print=True))

                    all_data.append(article_info)
                    batch_new += 1

                total_no_abstracts += batch_no_abstracts

                logging.info(
                    f"[Chunk {chunk_idx}] Batch fetched: pmids={len(pmids)}, "
                    f"added={batch_new}, "
                    f"no_abstracts_in_batch={batch_no_abstracts}, "
                    f"total_records={len(all_data)}"
                )

                if len(pmids) == 0 or start >= count:
                    break

                start += retmax
                time.sleep(1)

            else:
                break

    end_time = datetime.now(zurich)
    duration = format_timedelta_hms(end_time - start_time)

    df = pd.DataFrame(all_data)
    if not df.empty:
        df["text"] = df["title"].fillna("") + "^\n" + df["abstract"].fillna("")

    today = datetime.now(zurich).strftime("%Y/%m/%d")

    from_date = last_data_fetch_str.replace("/", "")
    to_date = today.replace("/", "")

    outfile = os.path.join(
        dir_path,
        "pubmed_fetch_results",
        f"pubmed_results_{from_date}_{to_date}_{duration}.csv"
    )

    logging.info(
        f"Finished PubMed fetch: total_records={len(df)}, "
        f"total_no_abstracts={total_no_abstracts}, duration={duration}"
    )

    df.to_csv(outfile, index=False, encoding="utf-8")

    logging.info(f"Wrote {len(df)} records to {outfile}")

    with open(date_file, "a", encoding="utf-8") as f:
        f.write(today + "\n")


if __name__ == "__main__":
    main()
