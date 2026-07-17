from dash.dependencies import Input, Output, State
from dash import no_update, ALL
from data.queries import get_studies_details, nr_studies, get_ids
from callbacks.utils import log_time


def register(app):
    @app.callback(
        Output('count-filtered', 'children', allow_duplicate=True),
        Output("studies-grid", "getRowsResponse"),
        Input("filtered-study-ids", "data"),
        Input("studies-grid", "getRowsRequest"),
        State("active-filters", "data"),
        prevent_initial_call=True
    )
    @log_time
    def update_grid(filtered_ids, study_grid_request, active_filters):
        if filtered_ids is None:
            # get all ids if no filtered ids are provided
            filtered_ids = get_ids()
        studies = get_studies_details(
            ids=filtered_ids if filtered_ids else [],
            start_row=study_grid_request["startRow"],
            end_row=study_grid_request["endRow"],
            sort_model=study_grid_request.get(
                "sortModel", [{"colId": "year", "sort": "desc"}]),
            filter_model=study_grid_request.get("filterModel", {}),
            tags=active_filters
        )
        responses = {"rowData": studies, "rowCount": len(filtered_ids) if filtered_ids else nr_studies()}
        return len(filtered_ids), responses
