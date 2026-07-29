import re
from collections import OrderedDict
from typing import Optional

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import dcc, html

from data.queries import (get_all_labels, get_all_tasks, get_ids,
                          get_latest_retrieval_date, get_paper_ner_tags,
                          get_study_count)
from style.colors import get_color_mapping

SECTION_PATTERN = re.compile(
    r"("
    r"BACKGROUND|INTRODUCTION|CONTEXT|RATIONALE|CONDITIONS?|"
    r"OBJECTIVE|OBJECTIVES|AIM|AIMS|PURPOSE|IMPORTANCE|"
    r"DESIGN|STUDY DESIGN|SETTING|SETTINGS|POPULATION|PARTICIPANTS|SUBJECTS|"
    r"ELIGIBILITY|INCLUSION CRITERIA|EXCLUSION CRITERIA|"
    r"METHODS?|PATIENTS AND METHODS|MATERIALS AND METHODS|STATISTICAL ANALYSIS|"
    r"INTERVENTION|INTERVENTIONS|DOSAGE|DOSAGE AND ADMINISTRATION|"
    r"PRIMARY OUTCOME|PRIMARY OUTCOMES|SECONDARY OUTCOME|SECONDARY OUTCOMES|"
    r"MAIN OUTCOME MEASURES|OUTCOMES?|MEASURES|EFFICACY|SAFETY|SAFETY AND EFFICACY|ADVERSE EVENTS|"
    r"RESULTS?|FINDINGS|"
    r"DISCUSSION|INTERPRETATION|LIMITATIONS|TRIAL LIMITATIONS|"
    r"CONCLUSION|CONCLUSIONS|REGISTRATION|TRIAL REGISTRATION|CLINICALTRIAL\.GOV IDENTIFIER|"
    r"FUNDING|FINANCIAL SUPPORT|ACKNOWLEDGMENTS?|REFERENCES?|CONFLICT OF INTEREST"
    r")\s*:",
    flags=re.IGNORECASE,
)

tasks = get_all_tasks()
filter_data = OrderedDict({task: get_all_labels(task) for task in tasks})


def header_layout() -> dbc.Navbar:
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("PsyNamic", href="/"),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem(
                                        "Evidence Strength", href="/insights/evidence-strength"),
                                    dbc.DropdownMenuItem(
                                        "Efficacy & Safety Endpoints", href="/insights/efficacy-safety"),
                                    dbc.DropdownMenuItem(
                                        "Long-term Data", href="/insights/long-term"),
                                    dbc.DropdownMenuItem(
                                        "Sex Bias", href="/insights/sex-bias"),
                                    dbc.DropdownMenuItem(
                                        "Number of Participants", href="/insights/participants"),
                                    dbc.DropdownMenuItem(
                                        "Study Protocol", href="/insights/study-protocol"),
                                    dbc.DropdownMenuItem(
                                        "Dosage", href="/insights/dosage"),

                                ],
                                nav=True,
                                in_navbar=True,
                                label="Insights",
                                id="insightsDropdown"
                            ),

                            dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem(
                                        "Filter all studies", href="/explore/filter"),
                                    dbc.DropdownMenuItem(
                                        "Search", href="/explore/search"),
                                    dbc.DropdownMenuItem(
                                        "Dual Task Analysis", href="/explore/dual-task"),
                                    dbc.DropdownMenuItem(
                                        "Time", href="/explore/time"),
                                ],
                                nav=True,
                                in_navbar=True,
                                label="Explore",
                                id="exploreDropdown"
                            ),

                            dbc.NavItem(dbc.NavLink("About", href="/about")),
                            dbc.NavItem(dbc.NavLink(
                                "Contact", href="/contact")),
                        ],
                        className="mr-auto",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
                html.Img(src="/assets/stride_lab_logo_transparent.png",
                         className="ms-3 me-3", width="10%")
            ],
            className="py-4"
        ),
        color="light",
        light=True,
        expand="lg",
        className="bg-light"
    )


def footer_layout() -> html.Footer:
    return html.Footer(
        dbc.Container(
            html.Div(
                "Copyright © 2026. STRIDE-Lab, Department of Clinical Research, University of Bern.",
                className="text-center"
            ),
            className="py-3"
        ),
        className="footer bg-light",
    )


def content_layout(list_of_children: list, id: str = "content") -> dbc.Container:
    stores = [
        dcc.Store(
            id="selected-ids",
            data=[],
            storage_type="memory"
        ),
    ]

    return dbc.Container(
        stores + list_of_children,
        class_name="py-4 content-container",
        id=id,
    )


def filter_component(filter_buttons: list[dbc.Button] = [], info_buttons: list[dbc.Button] = []) -> html.Div:
    """Builds the sections that display the active filters and info buttons in the studies display page."""
    children = [
        dbc.Row(
            className="mt-2 mb-2",
            children=[
                dbc.Col(
                    html.Span("Active Filters"),
                    width=2,
                    className="text-start text-secondary",
                ),
                dbc.Col(
                    id="active-filter-buttons",
                    children=filter_buttons,
                    width=10,
                ),
            ],
        ),
    ]

    if info_buttons:
        children.append(
            dbc.Row(
                className="mt-2 mb-2",
                children=[
                    dbc.Col(
                        html.Span("Info"),
                        width=2,
                        className="text-start text-secondary",
                    ),
                    dbc.Col(
                        id="active-infos-buttons",
                        children=info_buttons,
                        width=10,
                    ),
                ],
            )
        )

    return html.Div(
        children=children,
    )


def tag_component(tags: list[dict]) -> html.Div:
    """Builds the sections that display the active tags in the paper modal."""
    rows = [dbc.Row(
            className="d-flex align-items-center mt-2 mb-2",
            children=[
                dbc.Col(
                    html.Span([tag['task'], ':']),
                    width="auto",
                ),
                dbc.Col(
                    children=tag['buttons'],
                    width="auto",
                ),
                # dbc.Col(
                #     # make it secondary color
                #     html.Span(['Predicted by ', tag['model']],
                #               className="text-secondary"),
                #     width="auto",
                # ),
            ],
            )
            for tag in tags]
    return html.Div(
        children=rows,
    )


def study_grid(
    page_key: str,
    nr_filtered_studies: int,
    grid_id: str = "studies-grid",
    is_dosage: bool = False,
    tags: bool = True,
    default_sort_column: str = None,
    default_sort_order: str = "desc",
) -> html.Div:
    """
    A unified, shared data grid component for displaying research studies.
    Can be configured as a generic study grid or a specialized dosage grid.
    """

    if is_dosage:
        columns = [
            {"field": "title", "headerName": "Title", "sortable": True, "flex": 1},
            {
                "field": "abstract",
                "headerName": "Abstract",
                "filter": True,
                "cellStyle": {"whiteSpace": "pre-line"},
                "sortable": True,
                "flex": 2,
            },
            {"field": "year", "headerName": "Year",
                "sortable": True, "width": 100},
            {"field": "dosage", "headerName": "Dosage", "sortable": True, "flex": 2},
        ]

        if default_sort_column is None:
            default_sort_column = "dosage"

    else:
        columns = [
            {"field": "title", "headerName": "Title", "sortable": True, "flex": 1},
            {
                "field": "abstract",
                "headerName": "Abstract",
                "filter": True,
                "cellStyle": {"whiteSpace": "pre-line"},
                "sortable": True,
                "flex": 2,
            },
            {"field": "year", "headerName": "Year",
                "sortable": True, "width": 100},
            {
                "field": "url",
                "headerName": "URL",
                "sortable": False,
                "filter": False,
                "width": 150,
            },
        ]

        if default_sort_column is None:
            default_sort_column = "year"

    if tags:
        columns.append(
            {
                "headerName": "Tags",
                "field": "tags",
                "filter": False,
                "sortable": False,
                "width": 200,
                "cellRenderer": "Tag",
            }
        )

    ag_grid_options = {
        "rowModelType": "infinite",
        "pagination": True,
        "paginationPageSize": 20,
        "rowSelection": "single",
        "cacheBlockSize": 20,
        "defaultColDef": {
            "sortable": True,
            "resizable": True,
        },
        "sortModel": [
            {
                "colId": default_sort_column,
                "sort": default_sort_order,
            }
        ],
    }

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "Found Studies:",
                        className="d-inline me-1",
                        id={
                            "type": "study-grid-debug-field",
                            "index": grid_id,
                        },
                    ),

                    html.Span(
                        f"{nr_filtered_studies}",
                        className="d-inline",
                        id={
                            "type": "study-grid-count-filtered",
                            "index": grid_id,
                        },
                    ),

                    html.Span(
                        "(of total",
                        className="d-inline mx-1",
                    ),

                    html.Span(
                        f"{get_study_count()}",
                        className="d-inline",
                        id={
                            "type": "study-grid-count-total",
                            "index": grid_id,
                        },
                    ),

                    html.Span(
                        ")",
                        className="d-inline",
                    ),
                ],
                className="d-flex",
            ),

            dag.AgGrid(
                id={
                    "type": "study-grid",
                    "index": grid_id,
                },
                columnDefs=columns,
                rowModelType="infinite",
                dashGridOptions=ag_grid_options,
                style={
                    "height": "500px",
                    "width": "100%",
                },
            ),

            dbc.Button(
                "Download CSV",
                id={"type": "download-btn", "index": grid_id},
                color="primary",
                className="mt-3",
            ),
            dcc.Download(id={"type": "download-csv", "index": grid_id}),

            dbc.Row(
                [
                    html.Span(
                        f"Last data update: {get_latest_retrieval_date()}",
                        className="d-flex justify-content-center",
                    )
                ]
            ),

            paper_details_modal(
                id_prefix=grid_id,
            ),
        ],
        id=f"{grid_id}-display",
        key=page_key,
    )


def studies_display(
    page_key: str,
    ids: list[int] = None,
    filters: Optional[OrderedDict] = None,
    infos: Optional[OrderedDict] = None,
    tags: bool = True,
    grid_id: str = "studies-grid",
    is_dosage: bool = False,
) -> html.Div:
    """Builds the studies display page with a filter component and a study grid."""

    if ids is None:
        ids = get_ids()

    filter_buttons = build_filter_info_buttons(
        filters, map_all_labels=False) if filters else []
    info_buttons = build_filter_info_buttons(
        infos, map_all_labels=False) if infos else []

    return html.Div([
        html.H3("Filtered Studies"),

        filter_component(filter_buttons, info_buttons),

        dcc.Store(
            id="active-filters",
            data=filters or {},
            storage_type="memory",
        ),

        dcc.Store(
            id="active-infos",
            data=infos or {},
            storage_type="memory",
        ),

        dcc.Store(
            id="filtered-study-ids",
            data=ids,
            storage_type="memory",
        ),
        dcc.Store(
            id="grid-refresh",
            data=0,
        ),
        dcc.Loading(
            id=f"{grid_id}-loading",
            type="circle",
            children=study_grid(
                page_key=page_key,
                nr_filtered_studies=len(ids),
                grid_id=grid_id,
                is_dosage=is_dosage,
                tags=tags,
            ),
        ),
    ])


def checkbox_filter_selection() -> html.Div:
    """
    Builds the checkbox menu in the filter page, allowing users to select tasks and labels for filtering studies.
    """
    tasks = get_all_tasks() or []
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id="task-dropdown",
                    options=[{"label": task, "value": task} for task in tasks],
                    placeholder="Select a task",
                    clearable=False,
                ),
            ], width=9),

            dbc.Col([
                dbc.Button("Add Filter", id="add-filter-btn",
                           n_clicks=0,),
            ], width=3),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.Div(id="checkbox-container"),
            ], width=12),
        ], className="mb-4"),


    ], className="m-0 p-0")


def _get_tags(active_tags: OrderedDict[str, list[str]], map_all_labels: bool = True) -> OrderedDict[str, list[str]]:
    """Get consistent tag information for each task and label, including color mapping.

    OrderedDict({'Study Type': ['Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']})
    ->
    OrderedDict({'Study Type': [{'task': 'Study Type', 'label': 'Randomized-controlled trial (RCT)', 'color': 'rgb(85, 131, 102)'}, {'task': 'Study Type', 'label': 'Systematic review/meta-analysis', 'color': 'rgb(119, 157, 132)'}, {'task': 'Study Type', 'label': 'Other', 'color': 'rgb(199, 199, 199)'}]})
    """
    ordered_tags = OrderedDict()
    for task, labels in active_tags.items():
        if map_all_labels:
            all_labels_task = get_all_labels(task)
        else:
            all_labels_task = labels
        task_color_mapping = get_color_mapping(task, all_labels_task)
        for label in labels:
            tag_info = {
                'task': task,
                'label': label,
                'color': task_color_mapping[label]
            }
            if task not in ordered_tags:
                ordered_tags[task] = []
            ordered_tags[task].append(tag_info)
    return ordered_tags


def build_filter_info_buttons(tags: OrderedDict[str, list[dict]], editable: bool = False, map_all_labels: bool = True) -> list[dbc.Button]:
    """
    Extracted shared tag-building logic used in both modals.
    input = {
        "Condition": ['Depression', 'Anxiety'],
    output = [dbc.Button(...), dbc.Button(...)]

    """
    consistent_tags = _get_tags(tags, map_all_labels=map_all_labels)
    return [
        filter_info_button(
            tag["color"],
            tag["label"],
            tag["task"],
            editable=editable
        )
        for task in tags if tags[task]
        for tag in consistent_tags[task]
    ]


def filter_info_button(color: str, label: str, task: str, editable: bool = False):
    """ Create info/filter button """
    children = [html.Span(f"{label}", style={"font-size": "16px"})]
    custom_style = {
        "borderRadius": "1rem",
        "backgroundColor": f'{color}',
        "color": "white",
        "padding": "0.2rem 0.8rem",
        "margin": "0.1rem",
    }

    if editable:
        children.append(
            html.I(className="fa-solid fa-xmark",
                   style={"marginLeft": "0.5rem"})
        )
    else:
        custom_style["backgroundColor"] = color
        custom_style["border"] = "none"
        custom_style["boxShadow"] = "none"
        custom_style["cursor"] = "default"

    id = {'type': 'filter-button', 'task': task,
          'label': label} if editable else 'tag-button'
    return dbc.Button(
        children=children,
        style=custom_style,
        color="light",
        id=id,
        n_clicks=0,
        value={"category": task, "value": label},
        title=f'{task}: {label}',
    )


def paper_details_modal(id_prefix: str):
    """Render a modal container for paper/study details."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    id={"type": "paper-modal-title", "index": id_prefix})
            ),
            dbc.ModalBody(
                html.Div(
                    id={"type": "paper-modal-content", "index": id_prefix})
            ),
        ],
        id={"type": "study-grid-modal", "index": id_prefix},
        size="xl",
        is_open=False,
    )


def ner_tag(text: str, category: str = None):
    hilight_colors = {
        "Dosage": "#CCFF00",
    }
    default_highlight = "#FFFF00"

    color = hilight_colors[category] if category in hilight_colors else default_highlight

    return html.Span(
        [
            html.Span(text, className="ner-text"),
            html.Span(category, className="ner-category") if category else None,
        ],
        className="ner-tag",
        style={
            "backgroundColor": color,
        },
    )


def highlighted_text(text: str, cutpoints: list) -> html.Span:
    """Renders text with inline NER highlights given character cutpoints."""
    if not cutpoints:
        return html.Span(text)

    elements = []
    last_index = 0

    sorted_cutpoints = sorted(cutpoints, key=lambda cp: cp["start"])

    for cp in sorted_cutpoints:
        start, end, tag = cp["start"], cp["end"], cp.get("tag", "")

        if last_index < start:
            elements.append(html.Span(text[last_index:start]))

        elements.append(ner_tag(text[start:end], category=tag))
        last_index = end

    if last_index < len(text):
        elements.append(html.Span(text[last_index:]))

    return html.Span(elements)


def build_tag_buttons(paper):
    """Extracted shared tag-building logic used in both modals."""
    tags = []
    prev_task = None
    task_dict = {"task": "", "buttons": [], "model": ""}
    for tag in paper.get("tags", []):
        if tag["task"] != prev_task:
            if task_dict["task"]:
                tags.append(task_dict)

            prev_task = tag["task"]
            task_dict = {
                "task": tag["task"],
                "buttons": [filter_info_button(tag["color"], tag["label"], tag["task"])],
                "model": "BERT",  # TODO: Replace with actual model name if available in the tag data
            }
        else:
            task_dict["buttons"].append(
                filter_info_button(tag["color"], tag["label"], tag["task"])
            )

    if task_dict["task"]:
        tags.append(task_dict)

    return tag_component(tags)


def id_bar(internal_id: str, pubmed_id: str, doi: str) -> html.Div:
    return html.Div(
        f"Internal ID: {internal_id} | PubMed ID: {pubmed_id}"
        + (f" | DOI: {doi}" if doi else ""),
        className="text-muted",
    )


def build_paper_details(paper: dict, tags_component=None) -> html.Div:
    """Build detailed paper view for search/explore page using unified abstract styling."""
    if not paper:
        return html.Div()

    title = paper.get("title", "")
    year_str = f" ({paper.get('year', '')})" if paper.get("year") else ""
    full_title = f"{title}{year_str}"

    paper_url = paper.get("url", "")
    internal_id = paper.get("id", "")
    pubmed_id = paper.get("pubmed_id", "")
    doi = paper.get("doi", "")

    raw_abstract = paper.get("prediction_input")
    cutpoints = get_paper_ner_tags(internal_id)

    abstract_content = build_structured_abstract(
        raw_abstract, cutpoints=cutpoints)

    return html.Div(
        [
            html.Div(
                [
                    id_bar(internal_id, pubmed_id, doi),
                    build_share_button(internal_id),
                ],
                className="d-flex justify-content-between align-items-center mb-2",
            ),
            html.H3(full_title, className="mb-2"),
            (
                html.Div(
                    [
                        html.Strong("URL: "),
                        html.A(
                            paper_url,
                            href=paper_url,
                            target="_blank",
                            rel="noopener noreferrer",
                        ),
                    ],
                    className="modal-paper-link mb-2",
                )
                if paper_url
                else None
            ),

            html.Div(
                [
                    html.H4("Abstract", className="fw-bold mb-2"),
                    abstract_content,
                ],
                className="modal-paper-abstract mb-3",
            ),
            (
                html.Div(
                    [
                        html.H4("Tags", className="fw-bold mb-2"),
                        tags_component,
                    ],
                    className="modal-tags",
                )
                if tags_component
                else None
            ),
        ], style={"border": "1px solid #ccc", "padding": "1rem", "borderRadius": "0.5rem"}
    )


def build_share_button(paper_id: int) -> html.Div:
    """Build a borderless share icon button neatly aligned in flex containers."""
    return html.Div(
        [
            html.Button(
                [
                    html.I(className="fas fa-share-nodes fa-lg"),
                ],
                className="btn btn-link text-secondary p-0 border-0 text-decoration-none share-paper-btn d-flex align-items-center",
                type="button",
                title="Share this paper",
                **{"data-paper-id": str(paper_id)},
            ),
        ],
        className="d-inline-flex align-items-center p-2 m-2",
    )


def structured_highlighted_text(text, cutpoints):
    """Render structured abstracts while preserving NER highlighting."""
    matches = list(SECTION_PATTERN.finditer(text))

    if not matches:
        return highlighted_text(text, cutpoints)

    children = []

    for i, match in enumerate(matches):
        heading = match.group(1).upper()

        raw_start = match.end()
        raw_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        raw_section = text[raw_start:raw_end]

        leading_spaces = len(raw_section) - len(raw_section.lstrip())
        trailing_spaces = len(raw_section) - len(raw_section.rstrip())

        sec_start = raw_start + leading_spaces
        sec_end = raw_end - trailing_spaces

        section_text = text[sec_start:sec_end]

        section_cutpoints = []
        for cp in cutpoints:
            if cp["end"] <= sec_start or cp["start"] >= sec_end:
                continue

            c_start = max(sec_start, cp["start"]) - sec_start
            c_end = min(sec_end, cp["end"]) - sec_start

            if c_end > c_start:
                section_cutpoints.append({
                    **cp,
                    "start": c_start,
                    "end": c_end,
                })

        children.append(
            html.Div(
                [
                    html.Strong(f"{heading}: "),
                    highlighted_text(section_text, section_cutpoints)
                    if section_cutpoints
                    else section_text,
                ],
                style={"marginBottom": "0.35rem"},
            )
        )

    return children


def _split_prediction_input(paper):
    """Split prediction_input into title and body when the source text includes both."""
    prediction_input = (
        paper.get('prediction_input')
        or paper.get('abstract')
        or ''
    )
    title = paper.get('title', '') or ''

    for separator in ('.^\n', '.^.'):
        if separator in prediction_input:
            split_title, body = prediction_input.split(separator, 1)
            return (split_title or title), body, len(split_title) + len(separator)

    return title, prediction_input, 0


def _split_highlight_cutpoints(cutpoints, title_length, body_offset):
    """Split raw cutpoints into title-relative and body-relative spans."""
    title_cutpoints = []
    body_cutpoints = []

    if not cutpoints:
        return title_cutpoints, body_cutpoints

    for cp in cutpoints:
        start = cp.get('start', 0)
        end = cp.get('end', 0)

        if end <= title_length:
            title_cutpoints.append(cp.copy())
            continue

        if start >= body_offset:
            body_cp = cp.copy()
            body_cp['start'] = max(0, start - body_offset)
            body_cp['end'] = max(0, end - body_offset)
            body_cutpoints.append(body_cp)
            continue

        if start < title_length:
            title_cp = cp.copy()
            title_cp['start'] = start
            title_cp['end'] = min(end, title_length)
            if title_cp['end'] > title_cp['start']:
                title_cutpoints.append(title_cp)

        if end > body_offset:
            body_cp = cp.copy()
            body_cp['start'] = max(0, start - body_offset)
            body_cp['end'] = max(0, end - body_offset)
            if body_cp['end'] > body_cp['start']:
                body_cutpoints.append(body_cp)

    return title_cutpoints, body_cutpoints


def build_structured_abstract(text: str, cutpoints: list | None = None) -> html.Div:
    """
    Renders structured abstracts into formatted paragraphs with preserved NER highlights.
    """
    if not text:
        return html.Div("No abstract available.", className="text-muted")

    cutpoints = cutpoints or []
    matches = list(SECTION_PATTERN.finditer(text))

    # Fallback for plain/unstructured abstracts
    if not matches:
        return html.Div(
            highlighted_text(text, cutpoints),
            className="abstract-container"
        )

    children = []

    def get_section_cutpoints(sec_start: int, sec_end: int) -> list:
        sec_cps = []
        for cp in cutpoints:
            cp_start, cp_end = cp.get("start", 0), cp.get("end", 0)
            if cp_end <= sec_start or cp_start >= sec_end:
                continue

            c_start = max(sec_start, cp_start) - sec_start
            c_end = min(sec_end, cp_end) - sec_start

            if c_end > c_start:
                sec_cps.append({
                    **cp,
                    "start": c_start,
                    "end": c_end,
                })
        return sec_cps

    first_match_start = matches[0].start()
    if first_match_start > 0:
        raw_prefix = text[:first_match_start]
        trailing_spaces = len(raw_prefix) - len(raw_prefix.rstrip())
        sec_end = first_match_start - trailing_spaces
        sec_start = 0

        prefix_text = text[sec_start:sec_end].strip()
        if prefix_text:
            prefix_cutpoints = get_section_cutpoints(sec_start, sec_end)
            children.append(
                html.Div(
                    highlighted_text(prefix_text, prefix_cutpoints)
                    if prefix_cutpoints
                    else prefix_text,
                    style={"marginBottom": "0.35rem"},
                    className="abstract-section abstract-prefix",
                )
            )

    for i, match in enumerate(matches):
        heading = match.group(1).upper()

        raw_start = match.end()
        raw_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        raw_section = text[raw_start:raw_end]

        leading_spaces = len(raw_section) - len(raw_section.lstrip())
        trailing_spaces = len(raw_section) - len(raw_section.rstrip())

        sec_start = raw_start + leading_spaces
        sec_end = raw_end - trailing_spaces

        section_text = text[sec_start:sec_end]
        section_cutpoints = get_section_cutpoints(sec_start, sec_end)

        children.append(
            html.Div(
                [
                    html.Strong(f"{heading}: ", className="abstract-heading"),
                    highlighted_text(section_text, section_cutpoints)
                    if section_cutpoints
                    else section_text,
                ],
                style={"marginBottom": "0.35rem"},
                className="abstract-section",
            )
        )

    return html.Div(children, className="abstract-container")
