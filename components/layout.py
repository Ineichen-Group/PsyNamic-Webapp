import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import html, dcc
from data.queries import get_studies_details


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
                                        "Dual Task Analysis", href="/explore/dual-task"),
                                    dbc.DropdownMenuItem(
                                        "Time", href="/explore/time"),],
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
                "Copyright © 2024. STRIDE-Lab, Center for Reproducible Science, University of Zurich",
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
        id=id
    )


def filter_component(filter_buttons: list[dbc.Button] = [], comp_id: str = "active-filters", label="Active Filters:"):
    return html.Div(
        children=[
            dbc.Row(
                className="mt-3 d-flex align-items-center p-3",
                children=[
                    dbc.Col(
                        html.Span(label),
                        width="auto",
                    ),
                    dbc.Col(
                        id=comp_id,
                        children=filter_buttons,
                        width="auto",
                    ),
                ],
            ),
        ],
    )


def studies_display(study_tags: dict[str: list[html.Div]] = None):
    """
    Main display function with AG Grid for studies, expandable text, pagination, filtering, and CSV download.
    """
    return html.Div(
        [
            dag.AgGrid(
                id="studies-display",
                columnDefs=[
                    {"field": "title", "headerName": "Title",
                        "filter": True, "flex": 1},
                    {"field": "year", "headerName": "Year",
                        "filter": True, "width": 100},
                    {
                        "field": "abstract",
                        "headerName": "Abstract",
                        "filter": True,
                        "cellStyle": {"whiteSpace": "pre-line"},
                        "flex": 2,
                    },
                    {
                        "headerName": "Tags",
                        "field": "tags",
                        "filter": False,
                        "sortable": False,
                        "width": 200,
                        "cellRenderer": "Tag",
                    },
                ],
                rowData=get_studies_details(study_tags),
                dashGridOptions={
                    "pagination": True,
                    "paginationPageSize": 20,
                    "rowSelection": "single",
                },
                defaultColDef={
                    "sortable": True,
                    "resizable": True,
                },
                style={"height": "500px", "width": "100%"},
            ),

            dbc.Button("Download CSV", id="download-csv-button",
                       color="primary", className="mt-3"),
            dcc.Download(id="download-csv"),

            paper_details_modal(),
        ],
        id="studies-display-container",
    )


def filter_button(color: str, label: str, task: str, editable: bool = False):
    children = [html.Span(f"{label} ", style={"marginRight": "0.5rem"})]
    custom_style = {
        "borderRadius": "1rem",
        "backgroundColor": f'{color}',
        "color": "white",
        "marginRight": "0.5rem",
    }

    if editable:
        children.append(html.I(className="fa-solid fa-xmark"))
    else:
        custom_style["backgroundColor"] = color
        custom_style["border"] = "none"
        custom_style["boxShadow"] = "none"
        custom_style["cursor"] = "default"

    return dbc.Button(
        children=children,
        style=custom_style,
        color="light",
        id=f'{task}-{label}',
        n_clicks=0,
        value={"category": task, "value": label},
        title=f'{task}: {label}',
    )


def paper_details_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="paper-title")),
            dbc.ModalBody(
                [
                    html.P(id="paper-abstract", className="abstract-text"),
                    filter_component(
                        comp_id='active-filters-modal', label="Tags:"),
                ]
            ),
        ],
        id="paper-modal",
        size="xl",
        is_open=False,
    )


def ner_tag(text: str, category: str):
    hilight_colors = {
        "Dosage": "#bbf484",
    }

    color = hilight_colors[category]

    return html.Span(
        [
            html.Span(text, className="ner-text"),
            html.Span(category, className="ner-category"),
        ],
        className="ner-tag",
        style={
            "backgroundColor": color,
        },
    )
