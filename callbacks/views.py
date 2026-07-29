from dash import ALL, Input, Output, ctx, State, no_update
from components.graphs import get_ids_from_selected_data
from copy import deepcopy
import plotly.graph_objects as go

def register(app):
    @app.callback(
        Output("selected-ids", "data", allow_duplicate=True),
        Output({"type": "view-graph", "index": ALL}, "figure"),
        Input("reset-btn", "n_clicks"),
        Input({"type": "view-graph", "index": ALL}, "selectedData"),
        State("default-view-ids", "data"),
        State({"type": "view-graph", "index": ALL}, "figure"),
        prevent_initial_call=True,
    )
    def update_selected_ids(
        n_clicks,
        all_selected_data,
        default_view_ids,
        figures,
    ):
        trigger = ctx.triggered_id

        # Reset button
        if trigger == "reset-btn":
            cleared_figures = []

            for fig_dict in figures:
                fig = go.Figure(fig_dict)
                fig.update_traces(selectedpoints=[])

                cleared_figures.append(fig)

            return default_view_ids, cleared_figures

        # Normal selection
        valid_selections = [
            s for s in all_selected_data
            if s and s.get("points")
        ]

        if not valid_selections:
            return no_update, [no_update] * len(all_selected_data)

        selected_ids = get_ids_from_selected_data(valid_selections)

        return (
            selected_ids if selected_ids else no_update,
            [no_update] * len(all_selected_data),
        )