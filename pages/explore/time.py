import time
from dash import dcc, html
import pandas as pd
import dash_ag_grid as dag
from data.queries import get_time_data


def time_layout():
    df, ids = get_time_data()  # Initial dataset

    return html.Div([
        html.H1("Number of publications over time", className="my-4"),

        # Input fields for start and end year
        html.Div([
            html.Div([
                html.Label("Start Year:", className="form-label pe-4"),
                dcc.Input(id='start-year', type='number', value=df["Year"].min(),
                          min=1955, max=time.localtime().tm_year, className="form-control"),
            ], className="col-md-3"),

            html.Div([
                html.Label("End Year:", className="form-label pe-4"),
                dcc.Input(id='end-year', type='number', value=df["Year"].max(),
                          min=1955, max=time.localtime().tm_year, className="form-control"),
            ], className="col-md-3"),
        ], className="row g-3 mb-3"),

        # Graph placeholder
        dcc.Graph(id="time-graph"),

        # Table placeholder
        dag.AgGrid(
            id="time-studies-display",
            columnDefs=[
                {"field": "title", "headerName": "Title", "filter": True, "flex": 1},
                {"field": "abstract", "headerName": "Abstract", "filter": True, "flex": 2},
                {"field": "year", "headerName": "Year", "filter": True, "width": 100},
            ],
            rowData=[],
            dashGridOptions={"pagination": True, "paginationPageSize": 20},
            defaultColDef={"sortable": True, "resizable": True},
            style={"height": "500px", "width": "100%"},
        ),
    ], className="container")
