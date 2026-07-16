from dash.dependencies import Input, Output, State
from dash import no_update, ALL
from data.queries import get_studies_details, nr_studies
from callbacks.utils import log_time


def register(app):

    @app.callback(
        Output({"type": "studies-grid", "index": ALL}, "getRowsResponse"),
        Output('count-filtered', 'children', allow_duplicate=True),
        Input({"type": "studies-grid", "index": ALL}, "getRowsRequest"),
        Input("filter-tags", "data"),
        State("filtered-study-ids", "data"),
        prevent_initial_call=True
    )
    @log_time
    def fetch_studies_infinite(requests, tags, filtered_ids):
        if not requests:
            return no_update, no_update

        responses = []
        row_count = len(filtered_ids) if filtered_ids else nr_studies()

        for request in requests:
            if request is None:
                responses.append({"rowData": [], "rowCount": row_count})
                continue

            studies = get_studies_details(
                ids=filtered_ids if filtered_ids else [],
                start_row=request["startRow"],
                end_row=request["endRow"],
                sort_model=request.get(
                    "sortModel", [{"colId": "year", "sort": "desc"}]),
                filter_model=request.get("filterModel", {}),
                tags=tags
            )

            if not studies:
                row_count = 0

            responses.append({
                "rowData": studies,
                "rowCount": row_count
            })

        return responses, row_count

