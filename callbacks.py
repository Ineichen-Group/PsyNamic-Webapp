import logging
import time

import pandas as pd
import plotly.express as px

from dash import callback_context, no_update, dcc
from dash.dependencies import Input, Output, State, ALL

from pages.explore.dual_task import (
    get_dual_task_data,
    create_pie_chart,
    create_bar_chart,
    dual_study_grid,
    get_dual_filters,
    dual_task_graphs,
)
from components.layout import filter_button, tag_component
from style.colors import rgb_to_hex, get_color_mapping, SECONDARY_COLOR
from data.queries import get_studies_details, get_time_data


STYLE_NORMAL = {'border': '1px solid #ccc'}
STYLE_ERROR = {'border': '2px solid red'}


def log_time(func):
    """Decorator to log execution time of functions."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logging.info(
            f"{func.__name__} callback executed in {duration:.4f} seconds")
        return result
    return wrapper


def register_callbacks(app):
    register_time_view_callbacks(app)
    register_studyview_callbacks(app)
    register_dual_task_view_callbacks(app)
    # register_filter(app)
    register_pagination_callbacks(app)
    register_modal_callbacks(app)
    register_download_csv_callback(app)


def register_time_view_callbacks(app):
    @app.callback(
        Output("studies-grid", "getRowsResponse", allow_duplicate=True),
        Output("time-graph", "figure"),
        Output("count-filtered", "children"),
        Input("start-year", "value"),
        Input("end-year", "value"),
        prevent_initial_call=True
    )
    def update_time_view(start_year, end_year):
        df, ids = get_time_data(start_year=start_year, end_year=end_year)
        fig = px.bar(df, x="Year", y="Frequency", title="Frequency of Publications per Year", labels={
            "Frequency": "Frequency"
        })
        studies = get_studies_details(
            ids=ids,
        )
        return {
            "rowData": studies,
            "rowCount": len(ids)
        }, fig, len(ids)


def register_dual_task_view_callbacks(app):
    @app.callback(
        [
            Output('validation-message', 'children'),
            Output('dual-task-graph', 'children'),
            Output('task1-pie-graph', 'figure'),
            Output('task2-bar-graph', 'figure'),
            Output('active-filters', 'children'),
            Output('dual-study-grid', 'children'),
        ],
        [
            Input('jux_dropdown1', 'value'),
            Input('jux_dropdown2', 'value'),
            Input('task1-pie-graph', 'clickData'),
        ],
        prevent_initial_call=True
    )
    @log_time
    def update_dual_task_view(dropdown1_value, dropdown2_value, click_data):
        ctx = callback_context
        # Reset click data if dropdown value changes
        if 'dropdown' in ctx.triggered_id:
            click_data = None
        if dropdown1_value == dropdown2_value:
            return "Choose two different tasks.", no_update, no_update, no_update, no_update, no_update

        if click_data:
            label = click_data['points'][0]['label']
            color = click_data['points'][0]['color']

            task1_data, task2_data, ids, tags = get_dual_task_data(
                dropdown1_value, dropdown2_value, label)
            task1_all_labels = task1_data[dropdown1_value].unique()
            col_map = get_color_mapping(dropdown1_value, task1_all_labels)

            if rgb_to_hex(color) == SECONDARY_COLOR:
                color = col_map.get(label, '#000000')

            # Update charts
            pie_chart = create_pie_chart(
                task1_data, dropdown1_value, col_map, highlight=label, highlight_color=color)
            bar_chart = create_bar_chart(task2_data, dropdown2_value, color)

            filters = get_dual_filters(dropdown1_value, label)

            return "", no_update, pie_chart, bar_chart, filters, dual_study_grid(ids, tags)

        df_task1, df_task2, ids, tags = get_dual_task_data(
            dropdown1_value, dropdown2_value)
        graph = dual_task_graphs(
            df_task1, df_task2, dropdown1_value, dropdown2_value)
        return "", graph, no_update, no_update, get_dual_filters(), dual_study_grid(ids, tags)


def register_studyview_callbacks(app):
    @app.callback(
        Output({'type': 'collapse', 'index': ALL}, 'is_open'),
        Input({'type': 'collapse-button',
              'index': ALL}, 'n_clicks'),
        State({'type': 'collapse', 'index': ALL}, 'is_open'),
    )
    @log_time
    def toggle_collapse(n_clicks_list: list, is_open_list):
        ctx = callback_context
        if not ctx.triggered:
            return is_open_list
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        index = int(button_id.split('{"index":')[1].split(',')[0])

        new_is_open_list = [False] * len(is_open_list)
        new_is_open_list[index] = not is_open_list[index]

        return new_is_open_list


def register_pagination_callbacks(app):
    @app.callback(
        Output("studies-grid", "getRowsResponse", allow_duplicate=True),
        Input("studies-grid", "getRowsRequest"),
        State("filtered-study-ids", "data"),
        State("filter-tags", "data"),
        prevent_initial_call=True
    )
    def fetch_studies_infinite(request, filtered_ids, tags):
        start_row = request["startRow"]
        end_row = request["endRow"]

        sort_model = request.get(
            "sortModel", [{"colId": "year", "sort": "desc"}])
        filter_model = request.get("filterModel", {})
        studies = get_studies_details(
            ids=filtered_ids if filtered_ids else [],
            start_row=start_row,
            end_row=end_row,
            sort_model=sort_model,
            filter_model=filter_model,
            tags=tags
        )

        return {
            "rowData": studies,
            "rowCount": len(filtered_ids) if filtered_ids else len(studies)
        }


def register_modal_callbacks(app):
    @app.callback(
        [Output("paper-modal", "is_open", allow_duplicate=True),
         Output("paper-title", "children", allow_duplicate=True),
         Output("paper-link", "children", allow_duplicate=True),
         Output("paper-abstract", "children", allow_duplicate=True),
         Output("modal-tags", "children", allow_duplicate=True)
         ],
        [Input("studies-grid", "selectedRows")],
        prevent_initial_call=True
    )
    @log_time
    def show_study_paper_details(selected_row_data):
        if not selected_row_data:
            return False, no_update, no_update, no_update, no_update

        if len(selected_row_data) == 1:
            paper = selected_row_data[0]
            title = paper["title"] + " (" + str(paper["year"]) + ")"
            abstract = paper["abstract"]
            link_to_pubmed = paper["link_to_pubmed"]

            tags = []
            prev_task = None
            task_dict = {
                'task': '',
                'buttons': [],
                'model': '',
            }

            for tag in paper['tags']:
                if tag['task'] != prev_task:
                    if task_dict['task']:
                        tags.append(task_dict)

                    prev_task = tag['task']
                    task_dict = {
                        'task': tag['task'],
                        'buttons': [filter_button(tag['color'], tag['label'], tag['task'])],
                        'model': 'BERT',  # Replace with actual model if necessary
                    }
                else:
                    task_dict['buttons'].append(filter_button(
                        tag['color'], tag['label'], tag['task']))

            if task_dict['task']:
                tags.append(task_dict)

            buttons = tag_component(tags)

            return True, title, link_to_pubmed, abstract, buttons

        return no_update


def register_download_csv_callback(app):
    @app.callback(
        Output("download-csv", "data"),
        Input("download-csv-button", "n_clicks"),
        State("filtered-study-ids", "data"),
        State("filter-tags", "data"),
        prevent_initial_call=True,
    )
    @log_time
    def download_csv(n_clicks, filtered_ids, tags):
        current_data_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        studies = get_studies_details(
            ids=filtered_ids if filtered_ids else [],
            start_row=0,
            end_row=len(filtered_ids) if filtered_ids else None,
            tags=tags
        )

        if not studies:
            return no_update

        refactored_data = []
        tasks = set(t['task'] for study in studies for t in study['tags'])
        for study in studies:
            study_data = study.copy()
            tags = study_data.pop('tags', [])

            for task in tasks:
                study_data[task] = []

            for tag in tags:
                study_data[tag['task']].append(tag['label'])

            for task in tasks:
                study_data[task] = ", ".join(study_data[task])

            refactored_data.append(study_data)

        df = pd.DataFrame(refactored_data)

        return dcc.send_data_frame(df.to_csv, f"psynamic_data_{current_data_time}.csv", index=False)
