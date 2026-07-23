from dash import ctx, no_update
from dash.dependencies import MATCH, Input, Output, State

from callbacks.utils import log_time
from data.queries import get_ids, get_studies_details, get_studies_details_ner


def register(app):
    @app.callback(
        Output({"type": "study-grid-count-filtered", "index": MATCH}, "children"),
        Output({"type": "study-grid", "index": MATCH}, "getRowsResponse"),
        Input({"type": "study-grid", "index": MATCH}, "getRowsRequest"),
        Input("filtered-study-ids", "data"),
        State("active-filters", "data"),
        State("active-infos", "data"),
        State({"type": "study-grid", "index": MATCH}, "id"),
        prevent_initial_call="initial_duplicate",
    )
    @log_time
    def update_grid(
        study_grid_request: dict,
        filtered_ids: list[int],
        active_filters: dict,
        active_infos: dict,
        grid_id: dict[str, str],
    ):
        """Callback to update grid when either pagination moves or filtered-study-ids changes."""        
        # Guard against uninitialized request
        if study_grid_request is None and ctx.triggered_id != "filtered-study-ids":
            return no_update, no_update

        if study_grid_request is None:
            study_grid_request = {
                "startRow": 0,
                "endRow": 20,
                "sortModel": [{"colId": "year", "sort": "desc"}],
                "filterModel": {},
            }

        if filtered_ids is None:
            filtered_ids = get_ids()

        tags = {**(active_filters or {}), **(active_infos or {})}
        is_dosage = grid_id["index"] == "dosage-study-grid"

        if is_dosage:
            studies = get_studies_details_ner(
                ids=filtered_ids,
                start_row=study_grid_request.get("startRow", 0),
                end_row=study_grid_request.get("endRow", 20),
                sort_model=study_grid_request.get(
                    "sortModel", [{"colId": "year", "sort": "desc"}]
                ),
                filter_model=study_grid_request.get("filterModel", {}),
                tags=tags,
            )
        else:
            map_all_labels = grid_id["index"] == "dual-task-study-grid"
            studies = get_studies_details(
                ids=filtered_ids if filtered_ids else [],
                start_row=study_grid_request.get("startRow", 0),
                end_row=study_grid_request.get("endRow", 20),
                sort_model=study_grid_request.get(
                    "sortModel", [{"colId": "year", "sort": "desc"}]
                ),
                filter_model=study_grid_request.get("filterModel", {}),
                tags=tags,
                map_all_labels=map_all_labels,
            )

        if not studies or len(filtered_ids) == 0:
            return 0, {
                "rowData": [],
                "rowCount": 1,
            }

        total_count = len(filtered_ids)
        response = {
            "rowData": studies,
            "rowCount": total_count,
        }

        return total_count, response