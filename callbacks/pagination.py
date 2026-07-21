from dash.dependencies import MATCH, Input, Output, State

from callbacks.utils import log_time
from data.queries import (get_ids, get_studies_details,
                          get_studies_details_ner, nr_studies)


def register(app):

    @app.callback(
        Output({"type": "study-grid-count-filtered", "index": MATCH}, "children"),
        Output({"type": "study-grid", "index": MATCH}, "getRowsResponse"),
        Input({"type": "study-grid", "index": MATCH}, "getRowsRequest"),
        Input("grid-refresh", "data"),
        State({"type": "study-grid", "index": MATCH}, "id"),
        State("filtered-study-ids", "data"),
        State("active-filters", "data"),
        State("active-infos", "data"),
        prevent_initial_call="initial_duplicate",
    )
    @log_time
    def update_grid(
        study_grid_request: dict, 
        _,
        grid_id: dict[str, str],
        filtered_ids: list[int],
        active_filters: dict,
        active_infos: dict,
    ):
        """Callback to update the study grid with filtered and sorted data based on user interactions."""
        if study_grid_request is None:
            return 0, {
                "rowData": [],
                "rowCount": 0,
            }

        if filtered_ids is None:
            filtered_ids = get_ids()

        tags = {**active_filters, **active_infos}

        is_dosage = grid_id["index"] == "dosage-study-grid"

        if is_dosage:
            studies = get_studies_details_ner(
                ids=filtered_ids if filtered_ids else [],
                start_row=study_grid_request["startRow"],
                end_row=study_grid_request["endRow"],
                sort_model=study_grid_request.get(
                    "sortModel",
                    [{"colId": "year", "sort": "desc"}],
                ),
                filter_model=study_grid_request.get(
                    "filterModel",
                    {},
                ),
                tags=tags,
            )
        else:
            # check if grid came from dual task view, if so, map all colors for the active infos
            map_all_labels = grid_id["index"] == "dual-task-study-grid"
            studies = get_studies_details(
                ids=filtered_ids if filtered_ids else [],
                start_row=study_grid_request["startRow"],
                end_row=study_grid_request["endRow"],
                sort_model=study_grid_request.get(
                    "sortModel",
                    [{"colId": "year", "sort": "desc"}],
                ),
                filter_model=study_grid_request.get(
                    "filterModel",
                    {},
                ),
                tags=tags,
                map_all_labels=map_all_labels,
            )

        response = {
            "rowData": studies,
            "rowCount": (
                len(filtered_ids)
                if filtered_ids
                else nr_studies()
            ),
        }

        return response["rowCount"], response
