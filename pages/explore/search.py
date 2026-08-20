from dash import html, dcc
import dash_bootstrap_components as dbc


def search_layout():
    return html.Div(
        [
            html.H1("Search Papers", className="my-4"),
            html.P(
                "Enter a PubMed ID, internal study ID, DOI, or part of a title to find matching papers."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="pubmed id, id, doi or title",
                            className="form-control",
                            n_submit=0,  # Allows pressing 'Enter' to submit
                        ),
                        width=9,
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Search",
                            id="search-button",
                            color="primary",
                            n_clicks=0,
                        ),
                        width=3,
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                id="search-results", className="search-results-container hidden"
            ),
            html.Div(id="search-paper-details"),
            dcc.Store(
                id="last-search-store", data=None, storage_type="memory"
            ),
        ],
        className="container",
        id="search-layout",
    )