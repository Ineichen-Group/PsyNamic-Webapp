from dash import ctx, no_update
from dash.dependencies import Input, Output

from callbacks.utils import log_time
from components.graphs import bar_chart, get_ids_from_selected_data
from data.queries import get_time_data


def register(app):

    @app.callback(
        Output("selected-ids", "data", allow_duplicate=True),
        Output("time-graph", "figure"),
        Input("start-year", "value"),
        Input("end-year", "value"),
        Input({"type": "include-study-protocol-toggle", "index": "time"}, "value"),
        Input("time-graph", "selectedData"),
        prevent_initial_call=True
    )
    @log_time
    def update_time_view(start_year: int, end_year: int, include_study_protocol_toggle: list, selected_data: dict):
        """Updates the studies grid and time graph based on the selected start/end years or a bar selection."""
        if ctx.triggered_id == "time-graph":
            if not selected_data or not selected_data.get("points"):
                return no_update, no_update
            return get_ids_from_selected_data([selected_data]), no_update

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
