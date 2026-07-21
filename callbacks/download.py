import pandas as pd
from dash import dcc, no_update, ctx
from dash.dependencies import Input, Output, State, ALL

from callbacks.utils import log_time
from data.queries import get_studies_details, get_studies_details_ner


def register(app):

    @app.callback(
        Output({"type": "download-csv", "index": ALL}, "data"),
        Input({"type": "download-btn", "index": ALL}, "n_clicks"),
        State("filtered-study-ids", "data"),
        State("active-filters", "data"),
        State("active-infos", "data"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    @log_time
    def download_csv(n_clicks_list: list[int], filtered_ids: list[int], active_filters: dict, active_infos: dict, pathname: str):
        # Ignore triggers when no button has actually been clicked
        if not ctx.triggered_id or not any(clicks for clicks in n_clicks_list if clicks):
            return [no_update] * len(n_clicks_list)

        current_data_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        tags = {**(active_filters or {}), **(active_infos or {})}
        is_dosage_view = bool(pathname and "dosage" in pathname.lower())

        # Fetch appropriate studies data
        if is_dosage_view:
            if not filtered_ids:
                all_dosage_studies = get_studies_details_ner(start_row=0, end_row=None)
                filtered_ids = [s['id'] for s in all_dosage_studies] if all_dosage_studies else []

            studies = get_studies_details_ner(
                ids=filtered_ids if filtered_ids else None,  # Fixed parameter name
                start_row=0,
                end_row=len(filtered_ids) if filtered_ids else None,
            )
        else:
            ids_to_fetch = filtered_ids if filtered_ids else None
            studies = get_studies_details(
                ids=ids_to_fetch,
                start_row=0,
                end_row=len(ids_to_fetch) if ids_to_fetch else None,
                tags=tags,
            )

        if not studies:
            return [no_update] * len(n_clicks_list)

        # Process and build DataFrame
        refactored_data = []
        tasks = set(
            t['task']
            for study in studies
            for t in study.get('tags', [])
            if isinstance(t, dict) and 'task' in t
        )

        for study in studies:
            study_data = study.copy()
            tag_list = study_data.pop('tags', [])

            for task in tasks:
                study_data[task] = []

            for tag in tag_list:
                if isinstance(tag, dict) and 'task' in tag and 'label' in tag:
                    study_data[tag['task']].append(str(tag['label']))

            for task in tasks:
                study_data[task] = ", ".join(study_data[task])

            refactored_data.append(study_data)

        df = pd.DataFrame(refactored_data)

        if 'abstract' in df.columns:
            df.drop(columns=['abstract'], inplace=True)

        prefix = "psynamic_dosage_data" if is_dosage_view else "psynamic_data"
        download_payload = dcc.send_data_frame(
            df.to_csv,
            f"{prefix}_{current_data_time}.csv",
            index=False,
        )

        triggered_index = ctx.triggered_id["index"]
        outputs = []
        for target in ctx.outputs_list:
            target_id = target.get("id", target)
            target_index = target_id.get("index") if isinstance(target_id, dict) else None
            
            if target_index == triggered_index:
                outputs.append(download_payload)
            else:
                outputs.append(no_update)

        # Return payload to the specific matched output target
        return outputs