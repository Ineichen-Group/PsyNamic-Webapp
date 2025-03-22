import plotly.express as px
import logging
import time

from dash import callback_context, html, no_update, dcc
from dash.dependencies import Input, Output, State, ALL

from pages.explore.dual_task import get_dual_task_data, create_pie_chart, create_bar_chart, dual_task_layout
from components.layout import filter_button, tag_component
from style.colors import rgb_to_hex, get_color_mapping, SECONDARY_COLOR
from data.queries import get_studies_details, get_time_data, get_studies_details
import pandas as pd


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
    reset_click_data(app)
    # register_dual_task_view_callbacks(app)
    # register_filter(app)
    register_pagination_callbacks(app)
    register_modal_callbacks(app)
    register_download_csv_callback(app)


def register_time_view_callbacks(app):
    @app.callback(
        Output("studies-display", "getRowsResponse", allow_duplicate=True),
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
            Output('dual-task-layout', 'children'),
            Output('validation-message', 'children'),
            Output('task1-pie-graph', 'figure'),
            Output('task2-bar-graph', 'figure'),
            Output('active-filters', 'children'),
            Output('studies-display', 'rowData'),
            Output('studies-count', 'children'),
        ],
        [
            Input('jux_dropdown1', 'value'),
            Input('jux_dropdown2', 'value'),
            Input('task1-pie-graph', 'clickData'),
        ],
    )
    @log_time
    def update_dual_task_view(dropdown1_value, dropdown2_value, click_data):
        if dropdown1_value == dropdown2_value:
            return dual_task_layout(task1=None, task2=None), "Choose two different tasks.", no_update, no_update, no_update, no_update

        # Default values
        task1_value = dropdown1_value or 'Substances'
        task2_value = dropdown2_value or 'Condition'

        # Default empty values
        pie_chart, bar_chart, filter_div, study_data = no_update, no_update, no_update, no_update
        nr_studies = 0

        # If click event exists, update the charts & filters
        if click_data:
            label = click_data['points'][0]['label']
            color = click_data['points'][0]['color']

            # Fetch updated data based on clicked label
            task1_data, task2_data, study_tags = get_dual_task_data(
                task1_value, task2_value, label)

            # Get color mappings
            task1_all_labels = task1_data[task1_value].unique()
            col_map = get_color_mapping(task1_value, task1_all_labels)

            if rgb_to_hex(color) == SECONDARY_COLOR:
                color = col_map.get(label, '#000000')

            # Update charts
            pie_chart = create_pie_chart(
                task1_data, task1_value, col_map, highlight=label, highlight_color=color)
            bar_chart = create_bar_chart(task2_data, task2_value, color)

            # Update filters
            filters = [{'category': task1_value,
                        'value': label, 'color': color}]
            filter_div = html.Div(className="d-flex flex-wrap",
                                  children=[filter_button(f['color'], f['value'], f['category']) for f in filters])

            # Update study display
            study_data = get_studies_details(study_tags)
            nr_studies = len(study_data) if study_data else 0

        return dual_task_layout(dropdown1_value, dropdown2_value), "", pie_chart, bar_chart, filter_div, study_data, nr_studies


def reset_click_data(app):
    @app.callback(
        Output('task1-pie-graph', 'clickData'),
        Input('jux_dropdown1', 'value'),
        Input('jux_dropdown2', 'value'),
    )
    # TODO: Not sure which order the callbacks are called --> this might not be consistent
    def reset_click_data(dropdown1_value, dropdown2_value):
        """When the dropdown values change, reset the click data"""
        return None


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
        Output("studies-display", "getRowsResponse", allow_duplicate=True),
        Input("studies-display", "getRowsRequest"),
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
        [Input("studies-display", "selectedRows")],
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
        State("studies-display", "rowData"),
        prevent_initial_call=True,
    )
    @log_time
    def download_csv(n_clicks, row_data):
        current_data_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        if not row_data:
            return no_update
        refactored_data = []
        tasks = set(t['task'] for t in row_data[0]['tags'])
        for row in row_data:
            tags = row['tags']
            for task in tasks:
                row[task] = []
            for tag in tags:
                row[tag['task']].append(tag['label'])
            row.pop('tags')
            refactored_data.append(row)

        df = pd.DataFrame(refactored_data)

        return dcc.send_data_frame(df.to_csv, f"psynamic_data_{current_data_time}.csv", index=False)
