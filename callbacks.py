import plotly.express as px
import pandas as pd

from dash.dependencies import Input, Output, State, ALL
from dash import callback_context, html
from pages.explore.dual_task import get_dual_task_data, create_pie_chart, create_bar_chart
from components.layout import filter_button
from style.colors import rgb_to_hex, get_color_mapping, SECONDARY_COLOR

STYLE_NORMAL = {'border': '1px solid #ccc'}
STYLE_ERROR = {'border': '2px solid red'}


def register_callbacks(app, data_paths: dict):
    register_time_view_callbacks(app, data_paths['frequency_df'])
    register_studyview_callbacks(app)
    reset_click_data(app)
    register_dual_task_view_callbacks(app)
    # register_filter(app)
    register_pagination_callbacks(app)


def register_time_view_callbacks(app, frequency_df: pd.DataFrame):
    @app.callback(
        Output('time-plot', 'figure'),
        Input('start-year', 'value'),
        Input('end-year', 'value')
    )
    def update_time_graph(start_year, end_year):
        # Filter data based on input years
        filtered_df = frequency_df[(frequency_df['Year'] >= start_year) & (
            frequency_df['Year'] <= end_year)]

        # Create the bar plot
        fig = px.bar(filtered_df, x='Year', y='Frequency',
                     title='Frequency of IDs per Year', labels={'Frequency': 'Frequency'})

        return fig


def register_dual_task_view_callbacks(app):
    @app.callback(
        [Output('task2-bar-graph', 'figure'),
         Output('task1-pie-graph', 'figure'),
         Output('jux_dropdown1', 'style'),
         Output('jux_dropdown2', 'style'),
         Output('validation-message', 'children'),
         Output('active-filters', 'children')],
        [Input('task1-pie-graph', 'clickData'),
         Input('jux_dropdown1', 'value'),
         Input('jux_dropdown2', 'value')],
    )
    def update_graph(click_data, dropdown1_value, dropdown2_value):
        task1_value = dropdown1_value or 'Substances'
        task2_value = dropdown2_value or 'Condition'

        # If the same task is selected, show an error message
        if dropdown1_value == dropdown2_value:
            return {}, {}, STYLE_ERROR, STYLE_ERROR, "Choose two different values", None

        style1, style2 = STYLE_NORMAL, STYLE_NORMAL
        task1_data, task2_data, study_tags = get_dual_task_data(
            task1_value, task2_value)

        task1_all_labels = task1_data[task1_value].unique()
        col_map = get_color_mapping(task1_value, task1_all_labels)

        pie_chart = create_pie_chart(task1_data, task1_value, col_map)
        bar_chart = create_bar_chart(task2_data, task2_value, None)

        if not click_data:
            return bar_chart, pie_chart, style1, style2, "", None

        label = click_data['points'][0]['label']
        color = click_data['points'][0]['color']

        # If the segment is gray, restore its original color from col_map
        if rgb_to_hex(color) == SECONDARY_COLOR:
            color = col_map.get(label, '#000000')  # Default black if not found

        task1_data, task2_data, study_tags = get_dual_task_data(
            task1_value, task2_value, label)
        pie_chart = create_pie_chart(
            task1_data, task1_value, col_map, highlight=label, highlight_color=color)
        bar_chart = create_bar_chart(task2_data, task2_value, color)

        filters = [{'category': task1_value, 'value': label, 'color': color}]
        filter_div = html.Div(className="d-flex flex-wrap",
                              children=[filter_button(f['color'], f['value'], f['category']) for f in filters])

        return bar_chart, pie_chart, style1, style2, "", filter_div


# def register_filter(app):
#     @app.callback(
#         Output('accordion', 'children'),
#         Input('active-filters', 'children'),
#     )
#     def update_study_view(filters):
#         if not filters:
#             return no_update
#         studies = get_studies(filters)
#         return [study_view(s, idx) for idx, s in enumerate(studies)]


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
        Output("studies-ag-grid", "dashGridOptions"),
        Input("page-size-dropdown", "value"),)
    def update_page_size(selected_page_size):
        """
        Updates the AG Grid pagination page size dynamically.
        """
        return {
            "pagination": True,
            "paginationPageSize": selected_page_size,
            "groupDefaultExpanded": 0,
            "autoGroupColumnDef": {
                "headerName": "Abstract",
                "field": "abstract",
                "cellRenderer": "agGroupCellRenderer",
            },
        }
