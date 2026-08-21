
from dash import ctx, no_update
from dash.dependencies import ALL, Input, Output, State

from callbacks.utils import log_time
from data.queries import get_filtered_study_ids, get_ids


def register(app):
    @app.callback(
        Output("filtered-study-ids", "data"),
        Input("active-filters", "data"),
        Input("selected-ids", "data"),
        Input({"type": "include-study-protocol-toggle", "index": ALL}, "value"),
        State("url", "pathname"),
        State("filtered-study-ids", "data"),
    )
    @log_time
    def update_filtered_ids(
        active_filters: dict,
        selected_ids: list,
        include_study_protocol_toggle_values: list,
        pathname: str,
        filtered_study_ids: list,
    ):
        """Callback to update the filtered study IDs based on active filters or selected IDs (in graphs)."""
        include_study_protocols = True
        if include_study_protocol_toggle_values:
            include_study_protocols = any(
                "include" in (value or [])
                for value in include_study_protocol_toggle_values
            )
        trigger = ctx.triggered_id
        is_toggle_trigger = isinstance(trigger, dict) and trigger.get("type") == "include-study-protocol-toggle"
        if trigger is None and not active_filters:
            return no_update
        elif trigger == "active-filters":
            if not active_filters:
                new_ids = get_ids(include_study_protocols=include_study_protocols)
            else:
                new_ids = get_filtered_study_ids(
                    active_filters,
                    include_study_protocols=include_study_protocols,
                )
            return new_ids

        elif trigger == "selected-ids":
            new_ids = selected_ids if selected_ids else get_ids(
                include_study_protocols=include_study_protocols
            )
            if not include_study_protocols and new_ids:
                protocol_ids = set(get_ids("Study Type", "Study protocol"))
                new_ids = [paper_id for paper_id in new_ids if paper_id not in protocol_ids]
            return new_ids

        elif is_toggle_trigger:
            if selected_ids:
                new_ids = selected_ids
            elif active_filters:
                new_ids = get_filtered_study_ids(
                    active_filters,
                    include_study_protocols=include_study_protocols,
                )
            else:
                new_ids = get_ids(include_study_protocols=include_study_protocols)

            if not include_study_protocols and new_ids:
                protocol_ids = set(get_ids("Study Type", "Study protocol"))
                new_ids = [paper_id for paper_id in new_ids if paper_id not in protocol_ids]

            return new_ids
        
        if "insights" in pathname:
            return filtered_study_ids

        return filtered_study_ids
