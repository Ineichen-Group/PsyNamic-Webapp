from collections import OrderedDict
from typing import Optional

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import dcc, html

from data.queries import (get_all_labels, get_all_tasks, get_ids,
                          latest_update, ner_tags_type, nr_studies)
from style.colors import get_color_mapping

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
        style={
            "marginTop": "auto",
            "width": "100%",
            "position": "relative",
            "bottom": "0",
        }
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
        class_name="py-4",
        id=id,
        style={"minHeight": "82vh"},
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
                    id="active-filters-bli-blub",
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
                        className="d-inline",
                        id={
                            "type": "study-grid-debug-field",
                            "index": grid_id,
                        },
                        style={"marginRight": "0.2rem"},
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
                        className="d-inline",
                        style={
                            "marginLeft": "0.25rem",
                            "marginRight": "0.25rem",
                        },
                    ),

                    html.Span(
                        f"{nr_studies()}",
                        className="d-inline",
                        id={
                            "type": "study-grid-count-total",
                            "index": grid_id,
                        },
                        style={"marginRight": "0.25rem"},
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
                        f"Last data update: {latest_update()}",
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

    filter_buttons = build_filter_info_buttons(filters, map_all_labels=False) if filters else []
    info_buttons = build_filter_info_buttons(infos, map_all_labels=False) if infos else []

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
        study_grid(
            page_key=page_key,
            nr_filtered_studies=len(ids),
            grid_id=grid_id,
            is_dosage=is_dosage,
            tags=tags,
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
        for task in tags
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

    return dbc.Modal(
        [
            dbc.ModalHeader(id={"type": "paper-title", "index": id_prefix}),
            dbc.ModalBody(
                [
                    html.A(id={"type": "paper-link", "index": id_prefix}),
                    html.Div(
                        id={"type": "paper-abstract", "index": id_prefix}),
                    html.Div(
                        id={"type": "paper-dosage-normalization", "index": id_prefix}),
                    html.Div(id={"type": "modal-tags", "index": id_prefix}),
                ]
            ),
        ],
        id={"type": "study-grid-modal", "index": id_prefix}, size="xl",
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
    elements = []
    last_index = 0

    for cp in cutpoints:
        start, end, tag = cp['start'], cp['end'], cp['tag']

        if last_index < start:
            elements.append(html.Span(text[last_index:start]))

        elements.append(ner_tag(text[start:end], category=tag))
        last_index = end

    if last_index < len(text):
        elements.append(html.Span(text[last_index:]))

    return html.Span(elements)


def get_filter_buttons(task, labels):
    """
    Creates filter buttons based on task and labels.
    """
    labels = sorted(labels)
    color_mapping = get_color_mapping(task, labels)
    buttons = []
    for label in labels:
        buttons.append(filter_info_button(
            color_mapping[label], label, task))
    return buttons


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


def build_paper_details(paper, ner_category=None, body_label="Abstract", tags_component=None):
    """Build a detail card with consistent title/body highlighting."""
    paper_id = paper.get('id')
    ner_tags = ner_tags_type(
        paper_id, ner_category) if ner_category else ner_tags_type(paper_id)
    paper_title, body_text, body_offset = _split_prediction_input(paper)
    title_tags, body_tags = _split_highlight_cutpoints(
        ner_tags,
        len(paper_title),
        body_offset,
    )

    highlighted_title = highlighted_text(
        paper_title, title_tags) if title_tags else paper_title
    highlighted_body = highlighted_text(
        body_text, body_tags) if body_tags else body_text

    children = [
        *_build_paper_header(paper, highlighted_title),
        html.H5(body_label),
        html.Div(highlighted_body, className='mb-3'),
    ]

    if tags_component:
        children.extend([
            html.H5("Tags"),
            tags_component,
        ])

    return html.Div(children, className='p-3 border rounded')


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


def _build_paper_header(paper, highlighted_title):
    """Build the shared paper header with URL, ids, and title."""
    paper_url = paper.get('url') or ''
    internal_id = paper.get('id') or ''
    pubmed_id = paper.get('pubmed_id') or ''

    return [
        html.Div([
            html.Span("URL: "),
            html.A(paper_url, href=paper_url, target='_blank'),
        ]),
        html.Div(
            f"Internal ID: {internal_id} | PubMed ID: {pubmed_id}",
            className='text-muted small',
        ),
        html.H3(highlighted_title),
    ]
