from collections import OrderedDict

from dash import ALL, callback_context, ctx
from dash.dependencies import Input, Output, State
from data.queries import get_filtered_study_ids, log_time, get_ids


def register(app):
    @app.callback(
        Output("filtered-study-ids", "data"),
        Output("grid-refresh", "data"),
        Input("active-filters", "data"),
        Input("selected-ids", "data"),
        State("url", "pathname"),
        State("filtered-study-ids", "data"),
        State("grid-refresh", "data"),
    )
    def update_filtered_ids(
        active_filters: dict,
        selected_ids: list,
        pathname: str,
        filtered_study_ids: list,
        grid_refresh: int,
    ):
        trigger = ctx.triggered_id
        # layout initialization
        if trigger is None:
            return filtered_study_ids, grid_refresh

        if "insights" in pathname:
            return filtered_study_ids, grid_refresh

        if trigger == "active-filters":
            new_ids = get_filtered_study_ids(active_filters)
            return new_ids, (grid_refresh or 0) + 1

        if trigger == "selected-ids":
            new_ids = selected_ids
            return new_ids, (grid_refresh or 0) + 1

        return filtered_study_ids, grid_refresh
    

    @app.callback(
        Output({'type': 'collapse', 'index': ALL}, 'is_open'),
        Input({'type': 'collapse-button', 'index': ALL}, 'n_clicks'),
        State({'type': 'collapse', 'index': ALL}, 'is_open'),
    )
    def toggle_collapse(n_clicks_list, is_open_list):
        ctx = callback_context

        if not ctx.triggered:
            return is_open_list

        button_id = ctx.triggered_id
        index = int(button_id.split('{"index":')[1].split(',')[0])

        new_is_open_list = [False] * len(is_open_list)
        new_is_open_list[index] = not is_open_list[index]

        return new_is_open_list

