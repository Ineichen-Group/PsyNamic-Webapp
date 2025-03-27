import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import html, dcc
from collections import OrderedDict
from data.queries import nr_studies, get_all_tasks, get_all_labels
from style.colors import get_color_mapping

tasks = get_all_tasks()
filter_data = OrderedDict({task: get_all_labels(task) for task in tasks})


def header_layout():
    return dbc.Navbar(
        dbc.Container(
            [
                # link to home
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


def footer_layout():
    return html.Footer(
        dbc.Container(
            html.Div(
                "Copyright © 2025. STRIDE-Lab, Center for Reproducible Science, University of Zurich",
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


def content_layout(list_of_children: list, id: str = "content"):
    return dbc.Container(
        list_of_children,
        class_name="py-4",
        id=id,
        style={"minHeight": "82vh"},

    )


def filter_component(filter_buttons: list[dbc.Button] = [], info_buttons: list[dbc.Button] = None, id: 'str' = 'active-filters'):
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
                    id=id,
                    children=filter_buttons,
                    width=10,
                ),
            ],
        )
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
                        id="info-buttons",
                        children=info_buttons,
                        width=10,
                    ),
                ],
            )
        )

    return html.Div(
        children=children,
    )


def tag_component(tags: list[dict]):
    rows = [dbc.Row(
            className="d-flex align-items-center mt-2 mb-2",
            children=[
                dbc.Col(
                    html.Span([tag['task'], ':']),
                    width="auto",
                ),
                dbc.Col(
                    id="active-filters",
                    children=tag['buttons'],
                    width="auto",
                ),
                dbc.Col(
                    # make it secondary color
                    html.Span(['Predicted by ', tag['model']],
                              className="text-secondary"),
                    width="auto",
                ),
            ],
            )
            for tag in tags]
    return html.Div(
        children=rows,
    )


def studies_display(study_tags: dict[int, list[html.Div]] = None, last_update: str = 'January 2024'):
    """
    Main display function with AG Grid for studies, expandable text, pagination, filtering, and CSV download.
    """
    # studies, nr = get_studies_details(study_tags)
    total_studies = nr_studies()

    return study_grid(total_studies, last_update, study_tags)


def study_grid(
        nr_total_studies: int,
        nr_filtered_studies: int,
        last_update: str,
        tags: bool = True,
        id: str = "studies-grid",
        default_sort_column: str = "year",
        default_sort_order: str = "desc"):

    columns = [
        {"field": "title", "headerName": "Title", "sortable": True, "flex": 1},
        {"field": "year", "headerName": "Year","sortable": True, "width": 100},
        {"field": "abstract", "headerName": "Abstract", "filter": True,
         "cellStyle": {"whiteSpace": "pre-line"}, "sortable": True, "flex": 2}
    ]

    if tags:
        columns.append({
            "headerName": "Tags",
            "field": "tags",
            "filter": False,
            "sortable": False,
            "width": 200,
            "cellRenderer": "Tag",
        })

    ag_grid_options = {
        "pagination": True,
        "paginationPageSize": 20,
        "rowSelection": "single",
        "cacheBlockSize": 20,
        "defaultColDef": {
            "sortable": True,
            "resizable": True,
        },
        "sortModel": [{"colId": default_sort_column, "sort": default_sort_order}],
    }

    return html.Div(
        [
            html.Div(
                children=[
                    html.Span(
                        "Found Studies: ",
                        className="d-inline",
                        style={"marginRight": "0.2rem"}
                    ),
                    html.Span(
                        f"{nr_filtered_studies}",
                        className="d-inline",
                        id="count-filtered",
                    ),
                    html.Span(
                        " (out of ",
                        className="d-inline"
                    ),
                    html.Span(
                        f"{nr_total_studies}",
                        id="count-total",
                        className="d-inline"
                    ),
                    html.Span(
                        " )",
                        className="d-inline"
                    ),
                ],
                className="d-flex"
            ),

            dag.AgGrid(
                id=id,
                columnDefs=columns,
                rowModelType="infinite",
                dashGridOptions=ag_grid_options,
                style={"height": "500px", "width": "100%"},
            ),

            dbc.Button("Download CSV", id="download-csv-button",
                       color="primary", className="mt-3"),
            dcc.Download(id="download-csv"),

            dbc.Row(
                children=[html.Span(
                    f'Last data update: {last_update}', className="d-flex justify-content-center")]
            ),
            paper_details_modal(),
        ], id="studies-display"
    )


def dosage_study_grid(
        nr_total_studies: int,
        nr_filtered_studies: int,
        last_update: str,
        tags: bool = True,
        default_sort_column: str = "Dosage",
        default_sort_order: str = "desc"):

    columns = [
        {"field": "title", "headerName": "Title", "sortable": True, "flex": 1},
        {"field": "year", "headerName": "Year","sortable": True, "width": 100},
        {"field": "abstract", "headerName": "Abstract", "filter": True,
         "cellStyle": {"whiteSpace": "pre-line"}, "sortable": True, "flex": 2},
        {"field": "dosage", "headerName": "Dosage", "sortable": True, "flex": 2},
    ]

    if tags:
        columns.append({
            "headerName": "Tags",
            "field": "tags",
            "filter": False,
            "sortable": False,
            "width": 200,
            "cellRenderer": "Tag",
        })

    ag_grid_options = {
        "pagination": True,
        "paginationPageSize": 20,
        "rowSelection": "single",
        "cacheBlockSize": 20,
        "defaultColDef": {
            "sortable": True,
            "resizable": True,
        },
        "sortModel": [{"colId": default_sort_column, "sort": default_sort_order}],
    }

    return html.Div(
        [
            html.Div(
                children=[
                    html.Span(
                        "Found Studies: ",
                        className="d-inline",
                        style={"marginRight": "0.2rem"}
                    ),
                    html.Span(
                        f"{nr_filtered_studies}",
                        className="d-inline",
                        id="count-filtered",
                    ),
                    html.Span(
                        " (out of ",
                        className="d-inline"
                    ),
                    html.Span(
                        f"{nr_total_studies}",
                        id="count-total",
                        className="d-inline"
                    ),
                    html.Span(
                        " )",
                        className="d-inline"
                    ),
                ],
                className="d-flex"
            ),

            dag.AgGrid(
                id='dosage-study-grid',
                columnDefs=columns,
                rowModelType="infinite",
                dashGridOptions=ag_grid_options,
                style={"height": "500px", "width": "100%"},
            ),

            dbc.Button("Download CSV", id="download-csv-button",
                       color="primary", className="mt-3"),
            dcc.Download(id="download-csv"),

            dbc.Row(
                children=[html.Span(
                    f'Last data update: {last_update}', className="d-flex justify-content-center")]
            ),
            paper_details_modal(id="dosage-modal"),
        ], id="studies-display"
    )


def filter_selection():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id="task-dropdown",
                    options=[{"label": task, "value": task}
                             for task in filter_data.keys()],
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

        html.H3("Filtered Studies"),
        filter_component(id='selected-filters'),

        dcc.Store(id="filter-store", data={}),
    ], className="m-0 p-0")


def get_tags(tags: OrderedDict[str, list[str]]) -> OrderedDict[str, list[str]]:
    ordered_tags = OrderedDict()
    for task, labels in tags.items():
        all_labels_task = get_all_labels(task)
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


def filter_button(color: str, label: str, task: str, editable: bool = False):
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
            html.I(className="fa-solid fa-xmark", style={"marginLeft": "0.5rem"})
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


def paper_details_modal(id="paper-modal"):
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="paper-title")),
            dbc.ModalBody(
                [
                    html.Span("Link to PubMed: "),
                    html.A(
                        id="paper-link",
                        target="_blank",
                        href="",                    ),
                    html.P(id="paper-abstract", className="abstract-text"),
                    html.Div(id='modal-tags'),
                ]
            ),
        ],
        id=id,
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