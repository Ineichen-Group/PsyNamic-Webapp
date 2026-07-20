from dash.dependencies import Input, Output, State
from dash import no_update, ALL
from dash.exceptions import PreventUpdate
from data.queries import get_studies_details, nr_studies, get_ids
from callbacks.utils import log_time


def register(app):
    @app.callback(
    Output("count-filtered", "children", allow_duplicate=True),
    Output("studies-grid", "getRowsResponse"),
    Input("studies-grid", "getRowsRequest"),
    Input("grid-refresh", "data"),
    State("filtered-study-ids", "data"),
    State("active-filters", "data"),
    State("active-infos", "data"),
    prevent_initial_call='initial_duplicate'
)
    @log_time
    def update_grid(study_grid_request: dict, refresh: int, filtered_ids: list, active_filters: dict, active_infos: dict):
        # 2. If the grid request isn't ready yet during layout swap, clear out the grid row data completely
        if study_grid_request is None:
            return no_update, {"rowData": [], "rowCount": 0}

        if filtered_ids is None:
            filtered_ids = get_ids()

        tags = {**active_filters, **active_infos}
        
        studies = get_studies_details(
            ids=filtered_ids if filtered_ids else [],
            start_row=study_grid_request["startRow"],
            end_row=study_grid_request["endRow"],
            sort_model=study_grid_request.get("sortModel", [{"colId": "year", "sort": "desc"}]),
            filter_model=study_grid_request.get("filterModel", {}),
            tags=tags
        )
        
        responses = {
            "rowData": studies, 
            "rowCount": len(filtered_ids) if filtered_ids else nr_studies()
        }
        
        return len(filtered_ids), responses