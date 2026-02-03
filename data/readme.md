# Name Formats
- pubmed_fetch_results/pubmed_results_{from_date}_{fetch_date}_{fetch_time}.csv
    example: pubmed_results_20231216_20260112_00-00-10.csv
    - includes all data published between 16.12.2023 and 12.01.2026 (including both dates)
    - fetched on the 12.01.2026
    - to fetch the data, it took 10 seconds

- relevant_studies/studies_{fetch_date}.csv
    - can be mapped to pubmed fetch results by fetch_date
    
- predictions/{class|ner}_predictions_{fetch_date}_{prediction_time}.csv
    - can be mapped to pubmed fetch results by fetch_date


  
