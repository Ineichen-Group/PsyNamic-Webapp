
from dash import ctx
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from data.queries import get_filtered_study_ids


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
    @log_time
    def update_filtered_ids(
        active_filters: dict,
        selected_ids: list,
        pathname: str,
        filtered_study_ids: list,
        grid_refresh: int,
    ):
        """Callback to update the filtered study IDs based on active filters or selected IDs (in graphs)."""
        trigger = ctx.triggered_id
        # layout initialization
        if trigger is None:
            return filtered_study_ids, grid_refresh

        elif trigger == "active-filters":
            new_ids = get_filtered_study_ids(active_filters)
            return new_ids, (grid_refresh or 0) + 1

        elif trigger == "selected-ids":
            new_ids = selected_ids if selected_ids else None
            return new_ids, (grid_refresh or 0) + 1
        
        if "insights" in pathname:
            return filtered_study_ids, grid_refresh

        return filtered_study_ids, grid_refresh
