from dash import Input, Output, State, ctx, no_update

from components.graphs import get_ids_from_selected_data


def register(app):

    @app.callback(
        Output("selected-ids", "data", allow_duplicate=True),
        Output("view-bar-chart", "figure"),
        Input("reset-btn", "n_clicks"),
        Input("view-bar-chart", "selectedData"),
        State("default-view-ids", "data"),
        State("default-view-figure", "data"),
        prevent_initial_call=True,
    )
    def update_selected_ids(
        _,
        selected_data,
        default_view_ids,
        default_view_figure,
    ):
        if ctx.triggered_id == "reset-btn":
            # Replace the whole figure
            return (
                default_view_ids,
                default_view_figure,
            )

        if not selected_data or not selected_data.get("points"):
            return no_update, no_update

        selected_ids = get_ids_from_selected_data([selected_data])

        return (
            selected_ids if selected_ids else no_update,
            no_update,
        )
