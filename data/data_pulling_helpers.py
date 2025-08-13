import requests
import csv
import time
from typing import Optional
import requests


# Extracted from pubmed search string
substance_terms = [
    "Lysergic Acid Diethylamide",
    "Psilocybin",
    "psilocin",
    "Mescaline",
    "N,N-Dimethyltryptamine",
    "Banisteriopsis",
    "N-Methyl-3,4-methylenedioxyamphetamine",
    "3,4-Methylenedioxyamphetamine",
    "Ketamine",
    "Ibogaine",
    "salvinorin a",
    "LSD",
    "LSD-25",
    "lysergic acid diethylamide",
    "delysid",
    "lysergide",
    "lysergamide",
    "Psilocybin",
    "Psilocibin",
    "comp360",
    "Psilocin",
    "4-HO-DMT",
    "psilocyn",
    "mescalin",
    "3,4,5-trimethoxyphenethylamine",
    "TMPEA",
    "Peyot",
    "DMT",
    "dimethyltryptamine",
    "dimethyl tryptamine",
    "N,N-DMT",
    "ayahuasca",
    "banisteriopsis",
    "5-methoxy-N,N-dimethyltryptamine",
    "methylbufotenin",
    "5-MeO-DMT",
    "5 methoxy dmt",
    "5 methoxy n, n dimethyl tryptamine",
    "5 methoxydimethyltryptamine",
    "n, n dimethyl 5 methoxytryptamine",
    "Methylenedioxymethamphetamine",
    "3,4-Methylenedioxy methamphetamine",
    "n methyl 3, 4 methylenedioxyamphetamine",
    "midomafetamine",
    "MDMA",
    "ecstasy",
    "Esketamine",
    "iboga",
    "salvinorin",
    "salvia divinorum"
]
""
OPEN_ALEX_API = "https://api.openalex.org/"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/"


# Semantic Scholar API
# --------------------------------------------------------------------------------
def get_semantic_scholar_abstract(doi_or_url: str) -> Optional[str]:
    """
    Fetch the abstract of a paper from Semantic Scholar given a DOI or DOI URL.
    """
    # Extract DOI from URL if necessary
    if doi_or_url.startswith("https://doi.org/"):
        doi = doi_or_url.split("https://doi.org/")[1]
    else:
        doi = doi_or_url

    base_url = "https://api.semanticscholar.org/graph/v1/paper/"
    paper_id = f"DOI:{doi}"
    params = {"fields": "abstract"}

    try:
        response = requests.get(f"{base_url}{paper_id}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("abstract")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    


# OpenAlex API
# --------------------------------------------------------------------------------

def build_openalex_search_query(substance_terms: list[str]) -> str:
    """ Just to try out, not peer reviewed yet"""
    query = ' OR '.join([f'"{word.replace(",", "")}"' for word in substance_terms if word.strip()])
    query = f'({query}) AND ("study" OR "trial" OR "psych")'
    print(f"Search query: {query}")
    return query


def search_openalex_works(query: str, output_file: str):
    """
    Search OpenAlex works using cursor paging, writing results continuously to file.
    Avoids duplicates and respects OpenAlex rate limits.
    """

    base_url = f"{OPEN_ALEX_API}works"
    per_page = 200  # max allowed
    seen_ids = set()

    cursor = "*"  # start
    requests_this_second = 0
    start_second = time.time()

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = None
        while True:
            # Rate limiting (10 req/sec)
            current_time = time.time()
            if current_time - start_second < 1:
                if requests_this_second >= 10:
                    time.sleep(1 - (current_time - start_second))
                    start_second = time.time()
                    requests_this_second = 0
            else:
                start_second = time.time()
                requests_this_second = 0

            params = {
                "filter": f"title_and_abstract.search:{query}",
                "per-page": per_page,
                "cursor": cursor
            }

            try:
                response = requests.get(base_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                requests_this_second += 1

                page_results = data.get("results", [])
                if not page_results:
                    break

                # Initialize CSV writer on first batch
                if writer is None and page_results:
                    keys = [
                        "id", "doi", "title", "publication_year", "type",
                        "pmid", "pmcid", "mag", "abstract"
                    ]
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()

                # Process and write each work
                for item in page_results:
                    if item["id"] not in seen_ids:
                        seen_ids.add(item["id"])
                        work_info = {
                            "id": item.get("id"),
                            "doi": item.get("doi"),
                            "title": item.get("title"),
                            "publication_year": item.get("publication_year"),
                            "type": item.get("type"),
                            "pmid": item.get("ids", {}).get("pmid"),
                            "pmcid": item.get("ids", {}).get("pmcid"),
                            "mag": item.get("ids", {}).get("mag"),
                        }
                        writer.writerow(work_info)

                # Move to next page
                cursor = data.get("meta", {}).get("next_cursor")
                if not cursor:
                    break

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                time.sleep(5)
                continue

    print(f"Finished. Saved results to {output_file}")


def get_openalex_topic(topic_id: int):
    """
    Check if an OpenAlex topic ID is valid and retrieve its details.
    """
    try:
        response = requests.get(topic_id, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        topic_details = {
            "id": data.get("id"),
            "display_name": data.get("display_name"),
            "description": data.get("description"),
            "keywords": data.get("keywords", []),
            "domain": {
                "id": data.get("domain", {}).get("id"),
                "display_name": data.get("domain", {}).get("display_name")
            },
            "field": {
                "id": data.get("field", {}).get("id"),
                "display_name": data.get("field", {}).get("display_name")
            },
            "subfield": {
                "id": data.get("subfield", {}).get("id"),
                "display_name": data.get("subfield", {}).get("display_name")
            },
            "wikidata": data.get("ids", {}).get("wikipedia")
        }
        
        return topic_details
    
    except requests.exceptions.HTTPError:
        print(f"Error: Topic ID '{topic_id}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def find_openalex_topics(term, per_page=10):
    """
    Search OpenAlex for topics matching a term.

    :param term: str, the search term
    :param per_page: int, number of results to return
    :return: list of topic objects
    """
    response = requests.get(
        f"{OPEN_ALEX_API}topics",
        params={
            "search": term,
            "per_page": per_page
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        return []


if __name__ == "__main__":
    example_doi = "https://doi.org/10.1056/nejmoa2032994"
    print(get_semantic_scholar_abstract(example_doi))
    topics = find_openalex_topics("animal", per_page=10)
    for topic in topics:
        print(topic['display_name'], topic['id'])
    simple_query = 'psilocybin'
    search_openalex_works(simple_query, "openalex_results_psilocybin.csv")
    query = build_openalex_search_query(substance_terms)
    search_openalex_works(query, "openalex_results.csv")