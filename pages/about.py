from dash import html
import dash_bootstrap_components as dbc


def reference(number, title, authors, journal, year):
    return html.Div(
        html.Span(
            [
                reference_number(number),
                f" {authors} ({year}). {title}. ",
                html.I(journal),
                "."
            ]
        ),
        style={'fontSize': '0.9em', 'marginBottom': '10px'}
    )


def reference_number(number):
    return html.Sup(html.Span(f"[{number}]", style={'fontSize': '0.8em'}))


def about_layout():

    return dbc.Container(
        children=[

            html.H1("About PsyNamic"),

            html.P(
                "PsyNamic is an automated living systematic review of clinical research "
                "on psychedelic therapies for psychiatric disorders. It continuously "
                "retrieves newly published studies and uses language models to extract "
                "and structure key information such as study design, substances, "
                "dosages, and target conditions. The results are presented in an "
                "interactive online platform that enables rapid exploration of trends "
                "and evidence in this rapidly evolving field.",
                className="mb-4"
            ),

            html.Div(
                html.Img(
                    src="assets/pipeline_psynamic_only_pubmed.png",
                    style={'width': '90%'},
                    className="my-4"
                ),
                style={'textAlign': 'center'}
            ),

            html.H3("Study Retrieval"),

            dbc.Accordion(
                start_collapsed=True,
                flush=True,
                children=[
                    dbc.AccordionItem(
                        title="Where do the studies come from?",
                        children=[

                            "We continously retrieve new studies from PubMed every Friday "
                            "using the official NCBI Entrez API. Only records "
                            "that include an abstract are considered. ",
                            html.A(
                                "(Learn more about the Entrez API)",
                                href="https://www.ncbi.nlm.nih.gov/books/NBK25501/",
                                target="_blank"),

                            "The exact PubMed search query can be seen here: ",
                            html.A(
                                "Download search_string.txt",
                                href="/assets/pubmed_search_string.txt",
                                download="search_string.txt"
                            ),
                            "A language model then further assesses the retrieved studies for relevance (s. Language Models section).",
                            "Whereas all new data is from PubMed, a small subset of studies (n=~960), which was manually annotated, was manually retrieved from multiple databases (Embase, Medline, Cochrane Trials (CENTRAL), PsycInfo, Scopus, and Web of Science)."
                        ]
                    ),

                    dbc.AccordionItem(
                        title="Which studies are included?",
                        children=[
                            html.B("Included studies"),
                            html.P(
                                "Clinical studies in human populations that "
                                "report on the use of classical psychedelic "
                                "substances. This includes studies in healthy "
                                "participants (including recreational users) "
                                "as well as individuals with medical or "
                                "psychiatric conditions. Both interventional "
                                "and observational clinical studies are eligible."
                            ),
                            html.B("Excluded studies"),
                            html.P(
                                "Animal-only studies, non-systematic reviews or "
                                "opinion pieces, corrigenda, studies using "
                                "non-psychedelic substances (such as THC, CBD, "
                                "cocaine, or heroin), and studies focusing "
                                "solely on operative pain or anesthesia without "
                                "relevant psychological or psychiatric outcomes."
                            ),
                        ],
                    ),
                ],
                className="mb-3",
            ),

            html.H3("Language Models"),

            dbc.Accordion(
                start_collapsed=True,
                flush=True,
                children=[
                    dbc.AccordionItem(
                        title="For what purpose are language models used?",
                        children=[
                            html.P(
                                "We use language models to automatically classify a retrieved study as relevant or not relevant and to extract key information such as study characteristics, substance-related information or clinical measures."
                            ),]
                    ),

                    dbc.AccordionItem(
                        title="What models are used?",
                        children=[
                            html.P(
                                children=[
                                    "We use fine-tuned biomedical variants of BERT",
                                    reference_number(1),
                                    " to automatically assess study relevance and extract key information. The biomedical variants (such as SciBERT and BioBERT) are pre-trained on scientific and biomedical literature, making them particularly effective for understanding domain-specific terminology and concepts relevant to clinical research."
                                ]
                            ),
                            html.P(
                                "Like famous language models such as ChatGPT, BERT is based on the transformer architecture and was pre-trained on a large corpus of text. However, unlike GPT-based models, BERT models are designed for understanding text rather than generating it and are much smaller in size (roughly 110M). In PsyNamic, 19 BERT-based models are fine-tuned for specific tasks such as determining the study type or extracting dosage information. In total, PsyNamic uses 19 expert models, each trained for a specific task (for example, identifying study design, participant characteristics, or dosage information)."),
                        ],
                    ),


                    dbc.AccordionItem(
                        title="How were the models trained?",
                        children=[
                            html.P("The models were trained on a manually annotated dataset. In Janaury 2024, a comprehensive literature research was conducted across multiple databases (PubMed, PsycInfo, Web of Science) to identify relevant studies on psychedelic therapies. ~5,600 of which studies were manually screened for relevance and then used to train the model that classifies studies as relevant or not. From the relevant studies, ~960 studies were randomly selected and manually annotated by at least two medical professionals. The data was then split into training, validation, and test set. Per task, a BERT-based model was fine-tuned on the training set and evaluated on the test set. Several biomedical variants of BERT were evaluated per task (such as BioBERT, BioMedBERT or SciBERT) and the best performance per task was selected.")
                        ]
                    ),

                    dbc.AccordionItem(
                        title="How well do the models perform?",
                        children=[
                            html.P("The models show good performance across a range of tasks, with F1-scores typically above 0.80 for key information extraction tasks. The figure below shows the F1-score of the best performing model per task as measured on the test set."),
                            html.Img(
                                src="assets/best_f1_scores_per_task.png",
                                style={'width': '80%'},
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),

            html.H3("Information Extraction"),

            dbc.Accordion(
                start_collapsed=True,
                flush=True,
                children=[
                    dbc.AccordionItem(
                        title="What exactly do we mean by 'information extraction'?",
                        children=[
                            "In the context of PsyNamic, information extraction refers to automatically turning the free text of study titles and abstracts into structured information that can be searched, filtered, and compared across many studies. For information that holds for the entire abstract, the language model perform classification. In classification, the language model assigns one or more labels from a predefined list, such as the study type or the condition being studied. For information that is mentioned with many different phrases/words across abstracts, the language model peform named entity recognitio (NER). In NER, the language model marks specific spans of text that are of a pre-defined type, such as dosage information."
                        ]
                    ),
                    dbc.AccordionItem(
                        title="What information is extracted?",
                        children=[
                            html.P(
                                "PsyNamic extracts structured information from study titles and abstracts "
                                "using classification (study-level labels) and named entity recognition "
                                "(token-level extraction from the text)."
                            ),

                            html.H6("Classification (study-level)"),

                            html.P("Study characteristics:"),
                            html.Ul([
                                html.Li("Study Type"),
                                html.Li("Data Type"),
                                html.Li("Data Collection"),
                                html.Li("Number of Participants"),
                                html.Li("Age of Participants"),
                                html.Li("Sex of Participants"),
                                html.Li("Study Purpose"),
                                html.Li("Study Control"),
                            ]),

                            html.P("Substance-related information:"),
                            html.Ul([
                                html.Li("Substances"),
                                html.Li("Application Form"),
                                html.Li("Regimen"),
                                html.Li("Setting"),
                                html.Li("Substance Naivety"),
                            ]),

                            html.P("Clinical measures:"),
                            html.Ul([
                                html.Li("Condition"),
                                html.Li("Outcomes"),
                                html.Li("Clinical Trial Phase"),
                                html.Li("Study Conclusion"),
                            ]),

                            html.H6("Named Entity Recognition (token-level)"),
                            html.Ul([
                                html.Li("Dosage"),
                                html.Li("Application Area"),
                            ]),
                        ],
                    ),

                    dbc.AccordionItem(
                        title="What are the specific task definitions?",
                        children=[

                            html.P(
                                "Each task is handled by a dedicated model that predicts one specific "
                                "aspect of a study based on its title and abstract."
                            ),

                            html.H6("Relevance"),
                            html.P(
                                "Determines whether a study reports on the use of classical psychedelic substances in humans. "
                                "Possible labels: Relevant | Irrelevant"
                            ),

                            html.H6("Study Type"),
                            html.P(
                                "Classifies the overall study design. Possible labels: "
                                "Randomized-controlled trial (RCT) | Cohort study | Real-world study | Qualitative study | "
                                "Case report | Case series | Systematic review/meta-analysis | Study protocol | Other"
                            ),

                            html.H6("Data Collection"),
                            html.P(
                                "Indicates how data were collected. Possible labels: Prospective | Retrospective | Not applicable | Unknown"
                            ),

                            html.H6("Data Type"),
                            html.P(
                                "Specifies whether outcomes were measured at one time point or over time. Possible labels: "
                                "Cross-sectional | Longitudinal short | Longitudinal long | Not applicable | Unknown"
                            ),

                            html.H6("Number of Participants"),
                            html.P(
                                "Categorizes the total number of participants. Possible labels: "
                                "1–20 | 21–40 | 41–60 | 61–80 | 81–100 | 100–199 | 200–499 | 500–999 | ≥1000 | Not applicable | Unknown"
                            ),

                            html.H6("Age of Participants"),
                            html.P(
                                "Indicates participant age group. Possible labels: Pediatric (<18) | Adult (≥18) | Both | Unknown | Not applicable"
                            ),

                            html.H6("Sex of Participants"),
                            html.P(
                                "Specifies participant sex. Possible labels: Male | Female | Both | Unknown | Not applicable"
                            ),

                            html.H6("Study Purpose"),
                            html.P(
                                "Identifies the main aim of the study. Possible labels: "
                                "Efficacy endpoints | Safety endpoints | Pharmacokinetics | Mechanism of action | "
                                "Disease model study | Demographic study"
                            ),

                            html.H6("Study Control"),
                            html.P(
                                "Describes the control condition. Possible labels: "
                                "Placebo | Active control | Pre-post | Non-controlled | Other | Not applicable"
                            ),

                            html.H6("Substances"),
                            html.P(
                                "Identifies studied psychedelic substances. Possible labels: "
                                "Ketamine | S-Ketamine | R-Ketamine | MDMA | LSD | Psilocybin | Psychedelic mushrooms | "
                                "Ayahuasca | DMT | 5-MeO-DMT | Mescaline | Ibogaine | Salvinorin A | Combination therapy | Analogue | Unknown"
                            ),

                            html.H6("Application Form"),
                            html.P(
                                "Specifies how substances were administered. Possible labels: "
                                "Oral | Nasal | Intravenous | Subcutaneous | Smoking | Other | Unknown | Not applicable"
                            ),

                            html.H6("Regimen"),
                            html.P(
                                "Indicates dosing regimen. Possible labels: Single dose | Multiple applications | Microdosing | Unknown"
                            ),

                            html.H6("Setting"),
                            html.P(
                                "Describes study setting. Possible labels: Clinical | Naturalistic | Party setting | Palliative | Other | Unknown | Not applicable"
                            ),

                            html.H6("Substance Naivety"),
                            html.P(
                                "Indicates prior psychedelic experience. Possible labels: Substance-naïve participants | Substance-non-naïve participants | Unknown | Not applicable"
                            ),

                            html.H6("Condition"),
                            html.P(
                                "Specifies medical or psychological condition studied. Possible labels: "
                                "Psychiatric condition | Depression | Anxiety | PTSD | Alcoholism | Other addictions | Anorexia | Alzheimer’s disease | Non-Alzheimer dementia | Substance abuse | (Chronic) Pain | Palliative setting | Recreational drug use | Healthy participants"
                            ),

                            html.H6("Outcomes"),
                            html.P(
                                "Specifies measured outcomes. Possible labels: "
                                "Mental functions | Physiological functions | Neuroimaging (MRI/fMRI) | PET/SPECT | EEG/MEG | "
                                "Surveys | Interviews | Psychedelic experience | Soluble biomarker | Neurotoxicity | Suicide | Emergency department visits | Driving ability"
                            ),

                            html.H6("Clinical Trial Phase"),
                            html.P(
                                "Classifies trial phase. Possible labels: Phase 1 | Phase 2 | Phase 3 | Phase 4 | Unknown | Not applicable"
                            ),

                            html.H6("Study Conclusion"),
                            html.P(
                                "Indicates overall study conclusion. Possible labels: Positive | Negative | Neutral | Mixed | Unknown | Not applicable"
                            ),

                            html.H6("Named Entity Recognition: Dosage"),
                            html.P(
                                "Extracts numerical dosage information directly from the text (no predefined categories)."
                            ),

                            html.H6(
                                "Named Entity Recognition: Application Area"),
                            html.P(
                                "Extracts the text describing the specific body area or system where the intervention was applied."
                            ),
                        ],
                    )
                ]
            ),

            html.H5("References", className="mt-5"),
            html.Div(
                children=[
                    reference(
                        1,
                        "BERT: Pre-training of Deep Bidirectional Transformers "
                        "for Language Understanding",
                        "Devlin et al.",
                        "North American Association for Computational Linguistics",
                        2019
                    )
                ]
            )
        ]
    )
