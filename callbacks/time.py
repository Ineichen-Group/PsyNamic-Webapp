from dash.dependencies import Input, Output

from callbacks.utils import log_time
from components.graphs import bar_chart
from data.queries import get_time_data


def register(app):

    @app.callback(
        Output("selected-ids", "data", allow_duplicate=True),
        Output("time-graph", "figure"),
        Input("start-year", "value"),
        Input("end-year", "value"),
        Input({"type": "include-study-protocol-toggle", "index": "time"}, "value"),
        prevent_initial_call=True
    )
    @log_time
    def update_time_view(start_year: int, end_year: int, include_study_protocol_toggle: list):
        """Updates the studies grid and time graph based on the selected start and end years."""
        include_study_protocols = "include" in (include_study_protocol_toggle or [])
        df, ids = get_time_data(
            start_year=start_year,
            end_year=end_year,
            include_study_protocols=include_study_protocols,
        )

        fig = bar_chart(
            data=df,
            x="Year",
            y="Frequency",
            title="Frequency of Publications per Year",
            x_label="Year",
            y_label="Frequency",
        ).figure

        return ids, fig