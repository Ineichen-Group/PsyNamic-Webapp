import time
from dash import dcc, html
import pandas as pd
import dash_ag_grid as dag
from data.queries import get_time_data, get_studies_details
from components.layout import study_grid


def time_layout():
    df, ids = get_time_data()  # Initial dataset
    total_studies = len(ids)
    studies = get_studies_details(ids=ids)
    grid = study_grid(studies, total_studies=total_studies,
                      last_update='January 2021', tags=False, id="time-studies-display")

    return html.Div([
        html.H1("Number of publications over time", className="my-4"),

        # Input fields for start and end year
        html.Div([
            html.Div([
                html.Label("Start Year:", className="form-label pe-4"),
                dcc.Input(id='start-year', type='number', value=df["Year"].min(),
                          min=1955, max=time.localtime().tm_year, className="form-control", debounce=True),
            ], className="col-md-3"),

            html.Div([
                html.Label("End Year:", className="form-label pe-4"),
                dcc.Input(id='end-year', type='number', value=df["Year"].max(),
                          min=1955, max=time.localtime().tm_year, className="form-control", debounce=True),
            ], className="col-md-3"),
        ], className="row g-3 mb-3"),

        # Graph placeholder
        dcc.Graph(id="time-graph"),

        grid,
    ], className="container")
