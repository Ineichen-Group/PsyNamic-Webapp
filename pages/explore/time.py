import time
from dash import dcc, html
import pandas as pd
import dash_ag_grid as dag
from data.queries import get_time_data, get_studies_details
from components.layout import study_grid
import plotly.express as px


def time_layout():
    df, ids = get_time_data()  # Initial dataset (can be adjusted as needed)
    total_studies = len(ids)
    
    # Passing total studies and filtered studies for the grid display
    grid = study_grid(
        nr_total_studies=total_studies,
        nr_filtered_studies=total_studies, 
        last_update='January 2024',  # Update this as needed
        tags=False,
        id={"type": "studies-grid", "index": 6}
    )
    min_year = 1955
    max_year = time.localtime().tm_year

    df, ids = get_time_data(start_year=min_year, end_year=max_year)
    fig = px.bar(df, x="Year", y="Frequency", title="Frequency of Publications per Year", labels={
            "Frequency": "Frequency"
        })

    return html.Div([
        html.H1("Number of publications over time", className="my-4"),
        dcc.Store(id='filtered-study-ids', data=ids),
        dcc.Store(id='filter-tags', data=[]),
        # Input fields for start and end year
        html.Div([
            html.Div([
                html.Label("Start Year:", className="form-label pe-4"),
                dcc.Input(id='start-year', type='number', value=df["Year"].min(),
                          min=min_year, max=max_year, className="form-control", debounce=True),
            ], className="col-md-3"),

            html.Div([
                html.Label("End Year:", className="form-label pe-4"),
                dcc.Input(id='end-year', type='number', value=df["Year"].max(),
                          min=min_year, max=max_year, className="form-control", debounce=True),
            ], className="col-md-3"),
        ], className="row g-3 mb-3"),

        # Graph placeholder
        dcc.Graph(id="time-graph", figure=fig),
        grid,
    ], className="container", id="time-layout")
