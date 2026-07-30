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

        return ids, fig