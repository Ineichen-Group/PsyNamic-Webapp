
from dash import ctx, no_update
from dash.dependencies import ALL, Input, Output, State

from callbacks.utils import log_time
from data.queries import get_filtered_study_ids, get_ids

# Pages with their own dedicated callback that recomputes "selected-ids" in response to the
# include-study-protocols toggle (e.g. re-running a chart query). On these pages the toggle must
# NOT also be handled directly below: both callbacks fire off the same toggle click, so acting on
# it here too causes a double grid refresh (once from a stale recompute here, once from the
# dedicated callback's own recompute). Skip to no_update and let the "selected-ids" update that
# callback writes drive this one instead.
_SELF_MANAGED_TOGGLE_PATHNAMES = {
    "/insights/dosage",
    "/insights/evidence-strength",
    "/insights/efficacy-safety",
    "/insights/long-term",
    "/insights/sex-bias",
    "/insights/participants",
}


def register(app):
    @app.callback(
        Output("filtered-study-ids", "data"),
        Input("active-filters", "data"),
        Input("selected-ids", "data"),
        Input({"type": "include-study-protocol-toggle", "index": ALL}, "value"),
        State("url", "pathname"),
        State("filtered-study-ids", "data"),
        State("advanced-mode", "data"),
    )
    @log_time
    def update_filtered_ids(
        active_filters: dict,
        selected_ids: list,
        include_study_protocol_toggle_values: list,
        pathname: str,
        filtered_study_ids: list,
        advanced_mode: bool,
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
            # On the advanced filter page, apply_advanced_filter (filters.py) owns re-applying the
            # boolean expression on this same toggle; skip here to avoid racing it with a stale recompute.
            if pathname == "/explore/filter" and advanced_mode:
                return no_update

            if pathname in _SELF_MANAGED_TOGGLE_PATHNAMES:
                return no_update

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
