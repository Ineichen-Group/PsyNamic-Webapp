from dash import dcc, html

from components.graphs import bar_chart
from components.layout import studies_display
from data.queries import get_time_data


def time_layout():
    df, ids = get_time_data()

    min_year = df["Year"].min()
    max_year = df["Year"].max()

    df, ids = get_time_data(start_year=min_year, end_year=max_year)
    graph = bar_chart(
        data=df,
        x="Year",
        y="Frequency",
        title="Frequency of Publications per Year",
        x_label="Year",
        y_label="Frequency",
    )
    graph.id = "time-graph"

    return html.Div([
        html.H1("Number of publications over time", className="my-4"),
        html.Div([
            html.Div([
                html.Label("Start Year:", className="form-label pe-4"),
                dcc.Input(id='start-year', type='number', value=min_year,
                          min=min_year, max=max_year, className="form-control", debounce=True),
            ], className="col-md-3"),

            html.Div([
                html.Label("End Year:", className="form-label pe-4"),
                dcc.Input(id='end-year', type='number', value=max_year,
                          min=min_year, max=max_year, className="form-control", debounce=True),
            ], className="col-md-3"),
        ], className="row g-3 mb-3"),
        graph,
        studies_display(page_key='time', ids=ids,
                        filters={}, infos={}, tags=False),
    ], className="container", id="time-layout")
