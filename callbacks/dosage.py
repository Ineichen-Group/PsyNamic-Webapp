
from dash import ALL, ctx, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.graphs import (get_ids_from_click_data,
                               get_ids_from_selected_data)
from pages.insights.views import build_dosage_graph


def register(app):
    @app.callback(
        Output("selected-ids", "data", allow_duplicate=True),
        Input({"type": "dosage-box-plot", "index": ALL}, "selectedData"),
        Input({"type": "dosage-box-plot", "index": ALL}, "clickData"),
        Input("dosage-reset-btn", "n_clicks"),
        prevent_initial_call=True
    )
    @log_time
    def update_selected_ids(select_data: list, click_data: list, _: list):
        if ctx.triggered_id == 'dosage-reset-btn':
            return []
        # if any of selected_data is not None,
        elif any(sd is not None for sd in select_data):
            return get_ids_from_selected_data(select_data)

        elif any(cd is not None for cd in click_data):
            return get_ids_from_click_data(click_data)

        else:
            return no_update

    @app.callback(
        Output("dosage-graph-container", "children"),
        Output("selected-ids", "data", allow_duplicate=True),
        Input({"type": "include-study-protocol-toggle", "index": "dosage-normalization-page"}, "value"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    @log_time
    def update_dosage_graph(include_study_protocol_toggle: list, pathname: str):
        if pathname != "/insights/dosage":
            return no_update, no_update

        include_study_protocols = "include" in (include_study_protocol_toggle or [])
        graph, ids = build_dosage_graph(include_study_protocols=include_study_protocols)
        return graph, ids
