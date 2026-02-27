from dash import html
import dash_bootstrap_components as dbc


study_information = {
    "Study characteristics": [
        {
            "task_name": "Study Type",
            "task_description": "Overall study design.",
            "labels": {
                "Randomized-controlled trial (RCT)": "Participants are randomly assigned to groups, including at least one control group.",
                "Cohort study": "A group of people is followed over time to study outcomes related to psychedelic exposure.",
                "Real-world study": "Examines variables in a real-world population and setting at a single point in time.",
                "Study protocol": "Outlines the methodology of a study still to be conducted.",
                "Systematic review/meta-analysis": "Summarizes all available research on a specific psychedelic-related question.",
                "Qualitative Study": "Explores subjective experiences and perceptions via interviews, focus groups, or content analysis.",
                "Case report": "Detailed report of one individual’s treatment and follow-up.",
                "Case series": "Collection of case reports involving similar interventions.",
                "Other": "Studies not belonging to the above categories or not classifiable."
            }
        },
        {
            "task_name": "Data Collection",
            "task_description": "Whether data was collected prospectively or retrospectively.",
            "labels": {
                "Prospective": "Data has been gathered prospectively.",
                "Retrospective": "Data has been collected retrospectively, e.g. as in case series and reports.",
                "Not applicable": "Not applicable to this study type, e.g. for systematic reviews.",
                "Unknown": "Data collection is unknown."
            }
        },
        {
            "task_name": "Data Type",
            "task_description": "Whether outcomes were measured at one time point or over time.",
            "labels": {
                "Cross-sectional": "Outcomes are measured during one single time point (or more than one time point within ≤ 24 hours).",
                "Longitudinal long": "Outcomes are measures during at least two different time points > 24 hours apart and the total follow-up time is ≥ 3 months.",
                "Longitudinal short": "Outcomes are measures during at least two different time points > 24 hours apart but the total follow-up time is < 3 months.",
                "Not applicable": "e.g., for systematic reviews or for studies pooling a variety of other studies together without providing information about data type.",
                "Unknown": "Data type is unknown."
            }
        },
        {
            "task_name": "Number of Participants",
            "task_description": "Total number of participants.",
            "labels": {
                "1-20": "",
                "21-40": "",
                "41-60": "",
                "61-80": "",
                "81-100": "",
                "100-199": "",
                "200-499": "",
                "500-999": "",
                "≥1000": "",
                "Not applicable": "E.g., for most systematic reviews.",
                "Unknown": ""
            }
        },
        {
            "task_name": "Age of Participants",
            "task_description": "Age group of participants.",
            "labels": {
                "Pediatric (< 18 years old)": "",
                "Adult (≥18 years)": "",
                "Unknown": "",
                "Not applicable": ""
            }
        },
        {
            "task_name": "Sex of Participants",
            "task_description": "",
            "labels": {
                "Both sexes": "We assume both sexes if nothing reported and ≥ 5 included subjects.",
                "Female": "",
                "Male": "",
                "Not applicable": "e.g., for most systematic reviews",
                "Unknown": "Neither the number of participants nor their sex is reported."
            }
        },
        {
            "task_name": "Study Purpose",
            "task_description": "Overall purpose of the study",
            "labels": {
                "Efficacy endpoints": "Measures whether a psychedelic improves disease or mental health.",
                "Safety endpoints": "Discusses potential adverse events or side effects of a psychedelic substance.",
                "Pharmacokinetics": "How the body absorbs, distributes, metabolizes, and excretes the substance.",
                "Mechanism of action": "Assesses potential molecular or mechanistic actions of the psychedelic substance.",
                "Disease model study": "Uses the psychedelic substance to induce a model psychosis.",
                "Demographic study": "Epidemiological study assessing psychedelic use or related outcomes in a population."
            }
        },
        {
            "task_name": "Study Control",
            "task_description": "Describes the control condition.",
            "labels": {
                "Placebo": "",
                "Active control": "E.g., midazolam as a control for ketamine.",
                "Pre-post": "Measurements before (pre) and after (post) psychedelic intervention.",
                "Other control": "E.g., non-users, cross-over.",
                "Non-controlled": "",
                "Not applicable": "E.g., for systematic reviews."
            }
        }
    ],
    "Substance-related information": [
        {
            "task_name": "Substances",
            "task_description": "Psychedelic substance(s) studied",
            "labels": {
                "Ketamine": "Racemic ketamine (not including S- or R-ketamine)",
                "S-Ketamine": "",
                "R-Ketamine": "",
                "MDMA": "Also referred to as Ecstasy.",
                "LSD": "",
                "Psilocybin": "Or psilocin.",
                "Psychedelic mushrooms": "Includes psychedelic truffles.",
                "Ayahuasca": "DMT plus MAO-inhibitor, also 5-MeO-DMT plus MAO-inhibitor.",
                "DMT": "DMT / N,N-DMT, sometimes referred to as tryptamines.",
                "5-MeO-DMT": "Sometimes referred to as tryptamines.",
                "Mescaline": "",
                "Ibogaine": "Ibogaine / iboga, includes noribogaine.",
                "Salvinorin A": "Also referred to as Salvia or Salvia Divinorum.",
                "Combination Therapy": "Combination with other substances or therapies.",
                "Analogue": "A substance closely related to the psychedelic listed.",
                "Unknown": "Psychedelic mentioned without specification."
            }
        },
        {
            "task_name": "Application Form",
            "task_description": "How substances were administered",
            "labels": {
                "Oral": "",
                "Nasal": "",
                "Intravenous": "",
                "Smoking": "Including inhalation.",
                "Subcutaneous": "",
                "Other": "Including sublingual.",
                "Unknown": "",
                "Not applicable": "E.g., for systematic reviews."
            }
        },
        {
            "task_name": "Regimen",
            "task_description": "Dosing regimen of psychedelic substance(s)",
            "labels": {
                "Microdosing": "As defined by the study authors.",
                "Multiple Applications": "Substance applied at multiple time points.",
                "Single Dose": "Substance applied only once.",
                "Unknown": "Dosing information unclear."
            }
        },
        {
            "task_name": "Setting",
            "task_description": "Study setting",
            "labels": {
                "Clinical": "Substance applied in a clinical setting.",
                "Naturalistic": "Substance applied in a naturalistic setting.",
                "Party setting": "",
                "Other setting": "",
                "Unknown": "Setting is unclear from the title/abstract.",
                "Not applicable": "Not applicable to this study type, e.g. for systematic reviews.",
                "Palliative Setting": "Applied in end-of-life care."
            }
        },
        {
            "task_name": "Substance Naivety",
            "task_description": "Whether participants are naive or experienced with psychedelic substances",
            "labels": {
                "Substance-Naïve Participants": "Study participants have not used psychedelic substances in the past.",
                "Substance-non-naïve participants": "Study participants did use psychedelic substances in the past.",
                "Unknown": "It is not clear whether the study participants have consumed such substances.",
                "Not applicable": "E.g., for systematic reviews."
            }
        }

    ],
    "Clinical measures": [
        {
            "task_name": "Condition",
            "task_description": "Medical or psychological condition studied",
            "labels": {
                "Psychiatric condition": "E.g., PTSD, depression, anxiety, addiction.",
                "Depression": "",
                "Anxiety": "",
                "Post-traumatic stress disorder (PTSD)": "",
                "Alcoholism": "",
                "Other addictions": "Includes addictions like smoking and others.",
                "Anorexia": "",
                "Alzheimer’s disease": "",
                "Non-Alzheimer dementia": "",
                "Substance abuse": "Polydrug users or abusers studied for effects of psychedelics.",
                "(Chronic) Pain": "Includes conditions like cluster headache.",
                "Palliative Setting": "End-of-life context.",
                "Recreational Drug Use": "",
                "Healthy Participants": "Participants without major medical conditions, e.g., in population studies."
            }
        },
        {
            "task_name": "Outcomes",
            "task_description": "Measured outcomes",
            "labels": {
                "The ability to drive a car": "",
                "Suicide": "including suicidal ideation or related questionnaires.",
                "Functional MRI": "Also called fMRI.",
                "MRI": "E.g., arterial spin labelling. If fMRI is used, classify it under both MRI and fMRI.",
                "PET, SPECT": "Or similar imaging approaches.",
                "Physiological Functions": "E.g., heart rate, blood pressure, body temperature, pupillary diameter, BMI.",
                "Electroencephalography (EEG)": "Includes MEG.",
                "Mental Functions": "E.g., ability to recognize faces, form language, mindfulness, memory, measures of mood or depression, impulsivity.",
                "Psychedelic experience": "E.g., mystical experience questionnaire or visual scale for psychedelic experience.",
                "Soluble biomarker": "E.g., proteins in blood/CSF, substances in body compartments like hair, pharmacokinetic measures, or genotyping.",
                "Surveys": "E.g., questionnaires on recreational psychedelic use.",
                "Interviews": "E.g., person-to-person interviews.",
                "Neurotoxicity": "E.g., direct measures like MR-spectroscopy or patient cell assays; excludes indirect measures.",
                "Emergency department visits": "E.g., studies assessing reasons for emergency department visits of users of psychedelic substances."

            }
        },
        {
            "task_name": "Clinical Trial Phase",
            "task_description": "",
            "labels": {
                "Phase 1": "Tests safety, dosage range, and pharmacokinetics in 20–100 people (usually healthy).",
                "Phase 2": "Tests effectiveness and optimal dosing; 100–300 patients; often randomized and single- or double-blind.",
                "Phase 3": "Large-scale testing (hundreds–thousands) to confirm safety and effectiveness before approval, randomized and double-blind.",
                "Phase 4": "Post-marketing surveillance; monitors long-term safety, rare side effects, and real-world effectiveness.",
                "Unknown": "Fulfilling above definition but phase not explicitly (or implicitly) mentioned.",
                "Not Applicable": "Not fulfilling the above definition."
            }
        },
        {
            "task_name": "Study Conclusion",
            "task_description": "Overarching finding of the study",
            "labels": {
                "Positive": "Having a beneficial therapeutic impact (e.g., 'lsd might decrease suicidal ideation in depression').",
                "Negative": "E.g., ketamine worsened neuropathic pain in patients.",
                "Neutral": "E.g., 'we did not observe an effect of MDMA on avoidance behaviour'.",
                "Mixed": "Both negative and positive conclusion.",
                "Unknown": "No conclusion.",
                "Not Applicable": "E.g., for fMRI studies or study protocols."
            }
        }

    ]

}


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


def generate_classification_ul(tasks_data, start_collapsed=True):
    """
    Generates an html.Ul with multiple classification tasks.

    Parameters:
    - tasks_data (list of dicts): Each dict should contain:
        {
            "task_name": str,
            "task_description": str,
            "labels": dict of {label_name: label_description}
        }
    - start_collapsed (bool): Whether the nested accordion starts collapsed (default True)

    Returns:
    - html.Ul: List of tasks, each with expandable labels
    """

    task_items = []

    for task in tasks_data:
        task_name = task["task_name"]
        task_description = task["task_description"]
        labels_dict = task["labels"]

        # Make a comma-separated string of labels for the accordion title
        label_list_str = ", ".join(labels_dict.keys())

        task_items.append(
            html.Li([
                # Nested accordion for labels
                dbc.Accordion([
                    dbc.AccordionItem(
                        title=html.Div(
                            children=[
                                html.B(f"{task_name}: "),
                                html.I(task_description),
                                html.Br(),
                                html.Span(
                                    html.Small(
                                        f"Labels: {label_list_str}")),
                            ],
                        ),
                        children=[
                            html.Ul([
                                html.Li([
                                    html.Span(f"{label}: "),
                                    html.I(description)
                                ]) for label, description in labels_dict.items()
                            ], className="label-description")
                        ],
                        className='label-text',
                    )
                ], start_collapsed=start_collapsed)
            ])
        )

    return html.Ul(task_items)


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

                            html.P([
                                "We continuously retrieve newly published studies from PubMed on a weekly basis "
                                "using the official NCBI Entrez API ",
                                html.A(
                                    "(Learn more about the Entrez API)",
                                    href="https://www.ncbi.nlm.nih.gov/books/NBK25501/",
                                    target="_blank"
                                ),
                                ".",
                                "Only records that include an abstract are considered. The exact PubMed search query can be seen here: ",
                                html.A(
                                    "Download search_string.txt",
                                    href="/assets/pubmed_search_string.txt",
                                    download="search_string.txt"
                                ),
                                "."
                            ]),

                            html.P(
                                ""
                            ),

                            html.P([
                                "A language model then further assesses the retrieved studies for relevance "
                                "(s. ",
                                html.I("Language Models "),
                                "section)."
                            ]),

                            html.P(
                                "While all newly added studies come from PubMed, a smaller subset of "
                                "approximately 960 studies was manually collected and annotated during "
                                "model development. These studies were retrieved from multiple databases, "
                                "including Embase, Medline, Cochrane Trials (CENTRAL), PsycInfo, Scopus, "
                                "and Web of Science."
                            ),
                        ]
                    ),

                    dbc.AccordionItem(
                        title="Which studies are included?",
                        children=[
                            html.P(
                                "Included studies: Clinical studies in human populations that "
                                "report on the use of classical psychedelic "
                                "substances. This includes studies in healthy "
                                "participants (including recreational users) "
                                "as well as individuals with medical or "
                                "psychiatric conditions. Both interventional "
                                "and observational clinical studies are eligible."
                            ),
                            html.P(
                                "Excluded studies: Animal-only studies, non-systematic reviews or "
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
                            html.Span(
                                "We use language models to automatically classify a retrieved study as relevant or not relevant and to extract key information such as study characteristics, substance-related information or clinical measures (s. "
                            ),
                            html.I("Information Extraction"),
                            " section)."
                        ]
                    ),

                    dbc.AccordionItem(
                        title="What models are used?",
                        children=[
                            html.P(
                                children=[
                                    "We use fine-tuned biomedical variants of BERT",
                                    reference_number(1),
                                    " to automatically assess study relevance and extract key information. The biomedical variants (such as BiomedBERT",
                                    reference_number(2),
                                    ", SciBERT",
                                    reference_number(3),
                                    ", BioBERT",
                                    reference_number(4),
                                    " and BioLinkBERT",
                                    reference_number(5),
                                    ") are pre-trained on scientific and biomedical literature, making them particularly effective for understanding domain-specific terminology and concepts relevant to clinical research."
                                ]
                            ),
                            html.P(
                                "Like well-known language models such as ChatGPT, BERT is based on the transformer architecture and was pre-trained on vast amounts of text. However, BERT models are optimized for understanding and analyzing text rather than generating it, and they are considerably smaller in size (around 110 million parameters)."),
                            html.P(
                                "In PsyNamic, 19 BERT-based models are fine-tuned for individual tasks. Each model acts as an expert for a specific aspect of information extraction, such as determining the study design, identifying participant characteristics, or extracting dosage information.")
                        ],
                    ),

                    dbc.AccordionItem(
                        title="How were the models trained?",
                        children=[
                            html.P("The models were trained using a manually annotated dataset. In January 2024, a comprehensive literature search was conducted across multiple databases, including Embase, Medline, Cochrane Trials (CENTRAL), PsycInfo, Scopus, to identify studies on psychedelic therapies."),
                            html.P("Approximately 5,600 studies were manually screened for relevance. These studies were used to train a model that classifies publications as relevant or irrelevant. From the relevant studies, around 960 were randomly selected and manually annotated in detail by at least two medical professionals to ensure annotation quality."),
                            html.P("The annotated dataset was then split into training, validation, and test sets. For each information extraction task, a separate BERT-based model was fine-tuned using the training data and evaluated on the test set. Multiple biomedical variants of BERT were compared for each task, and the best-performing model was selected.")
                        ]
                    ),

                    dbc.AccordionItem(
                        title="How well do the models perform?",
                        children=[
                            html.Div(
                                children=[
                                    html.P(
                                        "The models show good performance across a range of tasks, with F1-scores "
                                        "typically above 0.80 for key information extraction tasks. The figure below "
                                        "shows the F1-score of the best performing model per task as measured on the test set."
                                    ),
                                    html.P([
                                        "Some tasks operate at the abstract level, assigning labels to an entire title "
                                        "and abstract (e.g., study type or relevance), while others operate at the token "
                                        "level, identifying specific information directly within the text (e.g., dosage "
                                        "or application area). See the ",
                                        html.I("Information Extraction"),
                                        " section for more details on the specific tasks."
                                    ]),
                                ],),
                            html.Div(
                                html.Img(
                                    src="assets/best_f1_scores_per_task.png",
                                    style={'width': '60%'},
                                    className="my-4"
                                ),
                                style={'textAlign': 'center'}
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
                            "In PsyNamic, information extraction turns study titles and abstracts into structured data. For information that applies to the entire abstract, the model uses text classification. It assigns one or more labels from a predefined list, such as study type or the condition being studied. For details mentioned in many ways across abstracts, the model uses named entity recognition (NER). In NER, it identifies specific spans of text, like dosage."
                        ]
                    ),

                    dbc.AccordionItem(
                        title="What information is extracted?",
                        children=[
                            html.P(
                                "PsyNamic extracts structured information from study titles and abstracts "
                                "using classification (abstract-level) and named entity recognition (token-level)."
                            ),

                            html.H5("Classification (abstract-level)"),
                            html.Div(
                                children=[
                                    html.H6("Study characteristics:"),
                                    generate_classification_ul(
                                        study_information["Study characteristics"], start_collapsed=True),
                                ],
                                # left margin
                                className="ps-4"
                            ),

                            html.Div(
                                children=[
                                    html.H6("Substance-related information:"),
                                    generate_classification_ul(
                                        study_information["Substance-related information"], start_collapsed=True),
                                ],
                                className="ps-4"
                            ),

                            html.Div(
                                children=[
                                    html.H6("Clinical measures:"),
                                    generate_classification_ul(
                                        study_information["Clinical measures"], start_collapsed=True),
                                ],
                                className="ps-4"
                            ),

                            html.H5("Named Entity Recognition (token-level)"),
                            html.Ul([
                                html.Li([
                                    html.B("Dosage: "), html.Span(
                                        "The applied dosage(s) of the psychedelic substance(s).", className="task-description")
                                ]),
                                html.Li([
                                    html.B("Application Area: "), html.Span(
                                        "The condition or disease studied defined as a medically recognized state with identifiable diagnostic features, progression, and treatment response, typically having an ICD-10/11 code.", className="task-description")
                                ])
                            ])
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
                            ),
                            reference(
                                2,
                                "Domain-Specific Language Model Pretraining for Biomedical Natural Language Processing",
                                "Gu et al.",
                                "ACM Transactions on Computing for Healthcare (HEALTH)",
                                2020
                            ),
                            reference(
                                3,
                                "SciBERT: A Pretrained Language Model for Scientific Text",
                                "Beltagy et al.",
                                "Conference on Empirical Methods in Natural Language Processing",
                                2019),
                            reference(
                                4,
                                "BioBERT: a pre-trained biomedical language representation model for biomedical text mining",
                                "Lee et al.",
                                "Bioinformatics",
                                2019
                            ),
                            reference(
                                5,
                                "LinkBERT: Pretraining Language Models with Document Links",
                                "Yasunaga et al.",
                                "Annual Meeting of the Association for Computational Linguistics",
                                2022
                            ),

                        ]
                    )
                ]
            ),
        ]
    )
