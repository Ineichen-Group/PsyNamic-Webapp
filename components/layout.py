import dash_bootstrap_components as dbc
from dash import html, Input, Output, ctx
from data.queries import get_studies
import math
import re
import numpy as np
from plotly.express.colors import sequential


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
                                        "Good Research Practices", href="/insights/good-research"),
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
        className="footer bg-light"
    )


def content_layout(list_of_children: list):
    return dbc.Container(
        list_of_children,
        class_name="py-4"
    )


def search_filter_component(filter_buttons: list[dbc.Button] = []):
    return html.Div(
        className="m-4",
        children=[
            dbc.Form(
                className="d-flex",
                children=[
                    dbc.Row(
                        className="flex-grow-1",
                        children=[
                            dbc.Col(
                                dbc.Input(
                                    type="search",
                                    placeholder="Search",
                                    className="me-2",
                                    id="search-input",
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Search",
                                    color="outline-success",
                                    className="me-2",
                                    id="search-button",
                                    n_clicks=0,
                                ),
                                width="auto",
                            ),
                        ],
                    ),
                ],
            ),
            dbc.Row(
                className="mt-3 d-flex align-items-center",
                children=[
                    dbc.Col(
                        html.Span("Active Filters:", className="me-2"),
                        width="auto",
                    ),
                    dbc.Col(
                        id="active-filters",
                        children=filter_buttons,
                        width="auto",
                    ),
                ],
            ),
        ],
    )


def studies_display():
    """
    Main display function to handle paginated study cards.
    """
    # Fetch studies dynamically
    studies = get_studies()

    # Initial setup
    page_size = 20  # Number of studies per page
    total_pages = math.ceil(len(studies) / page_size)  # Total number of pages

    return html.Div(
        [
            html.Div(
                id="study-cards-container",
                children=[
                    study_view(study, idx)
                    for idx, study in enumerate(paginate_studies(studies, 1, page_size))
                ],
            ),
            html.Div(
                className="d-flex justify-content-between align-items-center mt-3",
                children=[
                    dbc.Button("Previous", id="prev-page-btn",
                               n_clicks=0, color="primary", disabled=True),
                    html.Div(id="page-info",
                             children=f"Page 1 of {total_pages}"),
                    dbc.Button("Next", id="next-page-btn",
                               n_clicks=0, color="primary"),
                ],
            ),
        ],
        id="studies-display-container",
    )


def study_view(s: dict[str, str], idx: int):
    """
    Creates an individual card for each study with an expandable abstract.
    """
    return dbc.Card(
        children=[
            dbc.CardHeader(
                children=[
                    html.H5(
                        f'{s["title"]}, ({s["year"]})', className="mb-0"
                    ),
                    dbc.Button(
                        html.I(className="fa-solid fa-caret-down"),
                        color="link",
                        id={'type': 'collapse-button', 'index': idx},
                        n_clicks=0,
                    ),
                ],
                className="d-flex justify-content-between align-items-center",
                id=f"heading{idx+1}",
            ),
            dbc.Collapse(
                dbc.CardBody(s['abstract']),
                id={'type': 'collapse', 'index': idx},
                is_open=False,
            ),
        ],
    )


def paginate_studies(studies, page, page_size):
    """
    Helper function to paginate studies.
    """
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return studies[start_idx:end_idx]


def filter_button(color: str, filter: str, cat: str, editable: bool = False):
    children = [html.Span(f"{filter} ", style={"marginRight": "0.5rem"})]
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
        id=f'{cat}-{filter}',
        n_clicks=0,
        value={"category": cat, "value": filter},
        title=f'{cat}: {filter}',
    )
