from dash import html
from components.layout import checkbox_filter_selection, studies_display


def filter_layout():
    return [
        html.H1(
            "Explore and filter all studies",
            className="my-4",
        ),

        html.P(
            "Explore all studies by applying filters to the data."
        ),

        html.Div(
            id="filter-selection-container",
            children=checkbox_filter_selection(),
        ),

        studies_display("filter-page"),
    ]
