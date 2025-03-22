from dash import html, dcc
from components.layout import filter_selection, study_grid
from data.queries import get_studies_details, nr_studies


def filter_layout():
    total_nr = nr_studies()

    grid = study_grid(
        nr_total_studies=total_nr,
        nr_filtered_studies=total_nr,
        last_update='January 2024',
        tags=True,
        id={"type": "studies-grid", "index": 5}
    )

    return html.Div([
        html.H1("Explore and filter all studies", className="my-4"),
        html.P("Explore all studies by applying filters to the data."),
        dcc.Store(id='filtered-study-ids', data=[]),
        dcc.Store(id='filter-tags', data=[]),
        filter_selection(),
        grid,
    ], className="container", id="filter-layout")
