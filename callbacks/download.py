from dash.dependencies import Input, Output, State

import pandas as pd
from dash import no_update, dcc
from dash.dependencies import Input, Output, State

from data.queries import get_studies_details
from callbacks.utils import log_time


def register(app):

    @app.callback(
        Output("download-csv", "data"),
        Input("download-csv-button", "n_clicks"),
        State("filtered-study-ids", "data"),
        State("filter-tags", "data"),
        prevent_initial_call=True,
    )
    @log_time
    def download_csv(n_clicks, filtered_ids, tags):
        if not n_clicks:
            return no_update

        current_data_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")

        studies = get_studies_details(
            ids=filtered_ids if filtered_ids else [],
            start_row=0,
            end_row=len(filtered_ids) if filtered_ids else None,
            tags=tags,
        )

        if not studies:
            return no_update

        refactored_data = []
        tasks = set(
            t['task']
            for study in studies
            for t in study.get('tags', [])
        )

        for study in studies:
            study_data = study.copy()
            tag_list = study_data.pop('tags', [])

            # Initialize empty columns per task
            for task in tasks:
                study_data[task] = []

            for tag in tag_list:
                study_data[tag['task']].append(tag['label'])

            # Convert lists to comma-separated strings
            for task in tasks:
                study_data[task] = ", ".join(study_data[task])

            refactored_data.append(study_data)

        df = pd.DataFrame(refactored_data)

        # Remove abstract column due to legal reasons
        if 'abstract' in df.columns:
            df.drop(columns=['abstract'], inplace=True)

        return dcc.send_data_frame(
            df.to_csv,
            f"psynamic_data_{current_data_time}.csv",
            index=False,
        )
