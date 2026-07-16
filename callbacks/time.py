import plotly.express as px
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from data.queries import get_studies_details, get_time_data


def register(app):

    @app.callback(
        Output({"type": "studies-grid", "index": 6},
               "getRowsResponse", allow_duplicate=True),
        Output("time-graph", "figure"),
        Output("count-filtered", "children"),
        Input("start-year", "value"),
        Input("end-year", "value"),
        prevent_initial_call=True
    )
    @log_time
    def update_time_view(start_year, end_year):
        df, ids = get_time_data(start_year=start_year, end_year=end_year)

        fig = px.bar(
            df,
            x="Year",
            y="Frequency",
            title="Frequency of Publications per Year",
            labels={"Frequency": "Frequency"},
        )

        studies = get_studies_details(ids=ids)

        return (
            {"rowData": studies, "rowCount": len(ids)},
            fig,
            len(ids),
        )