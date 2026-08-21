
from dash import ctx, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from data.queries import get_filtered_study_ids, get_ids


def register(app):
    @app.callback(
        Output("filtered-study-ids", "data"),
        Input("active-filters", "data"),
        Input("selected-ids", "data"),
        State("url", "pathname"),
        State("filtered-study-ids", "data"),
    )
    @log_time
    def update_filtered_ids(
        active_filters: dict,
        selected_ids: list,
        pathname: str,
        filtered_study_ids: list,
    ):
        """Callback to update the filtered study IDs based on active filters or selected IDs (in graphs)."""
        trigger = ctx.triggered_id
        if trigger is None and not active_filters:
            return no_update
        elif trigger == "active-filters":
            if not active_filters:
                new_ids = get_ids()
            else:
                new_ids = get_filtered_study_ids(active_filters)
            return new_ids

        elif trigger == "selected-ids":
            new_ids = selected_ids if selected_ids else None
            return new_ids
        
        if "insights" in pathname:
            return filtered_study_ids

        return filtered_study_ids
