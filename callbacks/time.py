from dash.dependencies import Input, Output

from callbacks.utils import log_time
from data.queries import get_studies_details, get_time_data
from components.graphs import bar_chart

def register(app):

    @app.callback(
        Output("studies-grid", "getRowsResponse", allow_duplicate=True),
        Output("time-graph", "figure"),
        Output("count-filtered", "children", allow_duplicate=True),
        Input("start-year", "value"),
        Input("end-year", "value"),
        prevent_initial_call=True
    )
    @log_time
    def update_time_view(start_year: int, end_year: int):
        """Updates the studies grid and time graph based on the selected start and end years."""
        df, ids = get_time_data(start_year=start_year, end_year=end_year)

        fig = bar_chart(
            data=df,
            x="Year",
            y="Frequency",
            title="Frequency of Publications per Year",
            x_label="Year",
            y_label="Frequency",
        ).figure


        studies = get_studies_details(ids=ids)

        return (
            {"rowData": studies, "rowCount": len(ids)},
            fig,
            len(ids),
        )